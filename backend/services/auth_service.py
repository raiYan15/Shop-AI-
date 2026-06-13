"""
ShopMind AI — Authentication Service
Handles user management, password hashing, JWT access tokens,
and refresh-token session lifecycle persisted in MongoDB.
"""

import os
import logging
import secrets
import hashlib
from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext
from dotenv import load_dotenv
from pathlib import Path
from bson import ObjectId

load_dotenv(Path(__file__).parent.parent / ".env")

logger = logging.getLogger(__name__)

# ── JWT Config ────────────────────────────────────────────────────────────────
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "").strip()
if not SECRET_KEY:
    # Fallback for local/dev only. Do NOT rely on this in production.
    SECRET_KEY = secrets.token_urlsafe(48)
    logger.warning("JWT_SECRET_KEY is not set. Using ephemeral in-memory secret for this process.")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_DAYS = 30
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "30"))

# ── Password Hashing ─────────────────────────────────────────────────────────
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain_password: str) -> str:
    """Hash a plain-text password."""
    return pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain-text password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


# ── JWT Token ─────────────────────────────────────────────────────────────────
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a signed JWT access token."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta if expires_delta else timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> Optional[dict]:
    """Decode and validate a JWT token. Returns payload or None if invalid."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError as e:
        logger.warning(f"JWT decode failed: {e}")
        return None


# ── User DB Helpers ───────────────────────────────────────────────────────────
async def get_user_by_email(email: str) -> Optional[dict]:
    """Fetch a user document from MongoDB by email."""
    from services.db import get_collection
    users = get_collection("users")
    user = await users.find_one({"email": email.lower().strip()})
    return user


async def get_user_by_id(user_id: str) -> Optional[dict]:
    """Fetch a user document from MongoDB by _id string."""
    from services.db import get_collection
    try:
        users = get_collection("users")
        user = await users.find_one({"_id": ObjectId(user_id)})
        return user
    except Exception:
        return None


async def create_user(
    email: str,
    password: str,
    first_name: str,
    last_name: str,
    phone: str = "",
) -> dict:
    """
    Create a new user in MongoDB.
    Returns the created user document (without password_hash).
    Raises ValueError if email already exists.
    """
    from services.db import get_collection
    from pymongo.errors import DuplicateKeyError

    users = get_collection("users")

    # Check for duplicate email
    existing = await users.find_one({"email": email.lower().strip()})
    if existing:
        raise ValueError("An account with this email already exists.")

    now = datetime.now(timezone.utc)
    user_doc = {
        "email": email.lower().strip(),
        "password_hash": hash_password(password),
        "first_name": first_name.strip(),
        "last_name": last_name.strip(),
        "phone": phone.strip(),
        "profile_image": "",
        "role": "user",
        "membership_type": "standard",
        "last_login": now,
        "theme_preference": "dark",
        "notification_settings": {
            "price_drop_alerts": True,
            "ai_recommendations": True,
            "email_newsletters": False,
        },
        "shopping_preferences": {
            "preferred_categories": [],
            "budget_range": "",
            "brands": [],
        },
        "created_at": now,
        "updated_at": now,
        "is_active": True,
    }

    try:
        result = await users.insert_one(user_doc)
        user_doc["_id"] = result.inserted_id
        return _sanitize_user(user_doc)
    except DuplicateKeyError:
        raise ValueError("An account with this email already exists.")


async def authenticate_user(email: str, password: str) -> Optional[dict]:
    """
    Validate email + password.
    Returns sanitized user dict on success, None on failure.
    """
    user = await get_user_by_email(email)
    if not user:
        return None
    if not verify_password(password, user.get("password_hash", "")):
        return None
    try:
        users = get_collection("users")
        await users.update_one(
            {"_id": user["_id"]},
            {
                "$set": {
                    "last_login": datetime.now(timezone.utc),
                    "updated_at": datetime.now(timezone.utc),
                }
            },
        )
        user["last_login"] = datetime.now(timezone.utc)
    except Exception as exc:
        logger.warning(f"Failed to update last_login: {exc}")
    return _sanitize_user(user)


def _sanitize_user(user: dict) -> dict:
    """Remove sensitive fields and convert ObjectId to string."""
    return {
        "id": str(user["_id"]),
        "email": user["email"],
        "first_name": user.get("first_name", ""),
        "last_name": user.get("last_name", ""),
        "phone": user.get("phone", ""),
        "profile_image": user.get("profile_image", ""),
        "role": user.get("role", "user"),
        "membership_type": user.get("membership_type", "standard"),
        "created_at": user.get("created_at", datetime.now(timezone.utc)).isoformat(),
        "last_login": user.get("last_login", datetime.now(timezone.utc)).isoformat(),
        "theme_preference": user.get("theme_preference", "dark"),
        "notification_settings": user.get("notification_settings", {}),
        "shopping_preferences": user.get("shopping_preferences", {}),
        "is_active": user.get("is_active", True),
    }


def _hash_refresh_token(refresh_token: str) -> str:
    return hashlib.sha256(refresh_token.encode("utf-8")).hexdigest()


def _new_refresh_token() -> str:
    return secrets.token_urlsafe(48)


async def create_session(user_id: str, user_agent: str = "", ip_address: str = "") -> str:
    """Create a refresh-token backed session in MongoDB and return raw token."""
    from services.db import get_collection

    sessions = get_collection("sessions")
    now = datetime.now(timezone.utc)
    refresh_token = _new_refresh_token()
    token_hash = _hash_refresh_token(refresh_token)
    expires_at = now + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

    await sessions.insert_one(
        {
            "session_id": secrets.token_hex(16),
            "user_id": user_id,
            "refresh_token_hash": token_hash,
            "created_at": now,
            "updated_at": now,
            "last_used_at": now,
            "expires_at": expires_at,
            "is_revoked": False,
            "user_agent": user_agent[:512],
            "ip_address": ip_address[:128],
        }
    )
    return refresh_token


async def revoke_session(refresh_token: str) -> None:
    """Revoke session identified by a refresh token."""
    from services.db import get_collection

    sessions = get_collection("sessions")
    token_hash = _hash_refresh_token(refresh_token)
    await sessions.update_one(
        {"refresh_token_hash": token_hash, "is_revoked": False},
        {"$set": {"is_revoked": True, "updated_at": datetime.now(timezone.utc)}},
    )


async def refresh_session(refresh_token: str, user_agent: str = "", ip_address: str = "") -> Optional[dict]:
    """
    Validate refresh token, rotate it, and return {user, refresh_token}.
    Returns None if token/session invalid.
    """
    from services.db import get_collection

    sessions = get_collection("sessions")
    users = get_collection("users")
    token_hash = _hash_refresh_token(refresh_token)
    now = datetime.now(timezone.utc)

    session = await sessions.find_one(
        {
            "refresh_token_hash": token_hash,
            "is_revoked": False,
            "expires_at": {"$gt": now},
        }
    )
    if not session:
        return None

    user_id = session.get("user_id")
    try:
        user = await users.find_one({"_id": ObjectId(user_id)})
    except Exception:
        user = None
    if not user:
        await sessions.update_one({"_id": session["_id"]}, {"$set": {"is_revoked": True, "updated_at": now}})
        return None

    new_refresh_token = _new_refresh_token()
    new_hash = _hash_refresh_token(new_refresh_token)
    await sessions.update_one(
        {"_id": session["_id"]},
        {
            "$set": {
                "refresh_token_hash": new_hash,
                "last_used_at": now,
                "updated_at": now,
                "user_agent": user_agent[:512] or session.get("user_agent", ""),
                "ip_address": ip_address[:128] or session.get("ip_address", ""),
            }
        },
    )

    return {
        "user": _sanitize_user(user),
        "refresh_token": new_refresh_token,
    }


async def update_user_profile(user_id: str, payload: dict) -> Optional[dict]:
    """Update editable user profile and settings fields."""
    from services.db import get_collection

    users = get_collection("users")
    now = datetime.now(timezone.utc)

    allowed_top_level = {
        "first_name",
        "last_name",
        "email",
        "profile_image",
        "theme_preference",
        "notification_settings",
        "shopping_preferences",
        "membership_type",
    }

    updates = {k: v for k, v in payload.items() if k in allowed_top_level}
    if "email" in updates and isinstance(updates["email"], str):
        updates["email"] = updates["email"].lower().strip()
    if not updates:
        user = await get_user_by_id(user_id)
        return _sanitize_user(user) if user else None

    updates["updated_at"] = now
    await users.update_one({"_id": ObjectId(user_id)}, {"$set": updates})
    user = await users.find_one({"_id": ObjectId(user_id)})
    return _sanitize_user(user) if user else None


async def change_user_password(user_id: str, current_password: str, new_password: str) -> bool:
    """Change password after validating current password hash."""
    from services.db import get_collection

    users = get_collection("users")
    user = await users.find_one({"_id": ObjectId(user_id)})
    if not user:
        return False
    if not verify_password(current_password, user.get("password_hash", "")):
        return False

    await users.update_one(
        {"_id": user["_id"]},
        {
            "$set": {
                "password_hash": hash_password(new_password),
                "updated_at": datetime.now(timezone.utc),
            }
        },
    )
    return True


async def ensure_user_indexes():
    """Create unique index on email field."""
    from services.db import get_collection
    from pymongo import ASCENDING
    users = get_collection("users")
    await users.create_index([("email", ASCENDING)], unique=True)
    sessions = get_collection("sessions")
    await sessions.create_index([("refresh_token_hash", ASCENDING)], unique=True)
    await sessions.create_index([("user_id", ASCENDING), ("updated_at", -1)])
    await sessions.create_index([("expires_at", ASCENDING)])
    logger.info("✓ Users collection indexes ensured")
