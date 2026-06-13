"""
ShopMind AI — MongoDB Connection Singleton
Async driver (motor) for FastAPI endpoints.
"""

import os
import logging
from functools import lru_cache
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
import motor.motor_asyncio
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

try:
    import certifi
except Exception:  # pragma: no cover
    certifi = None

# Load .env from backend directory
_env_path = Path(__file__).parent.parent / ".env"
load_dotenv(_env_path)

logger = logging.getLogger(__name__)

MONGODB_URI     = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
MONGODB_DB_NAME = os.getenv("MONGODB_DB_NAME", "shopmind_ai")

# ── Async client (motor) ──────────────────────────────────────────────────────
_async_client: Optional[motor.motor_asyncio.AsyncIOMotorClient] = None


def _atlas_client_kwargs(uri: str) -> dict:
    """Return safe client kwargs for Atlas + local Mongo usage."""
    kwargs = {
        "serverSelectionTimeoutMS": 10000,
        "connectTimeoutMS": 10000,
        "socketTimeoutMS": 10000,
    }

    if "mongodb+srv" in uri:
        kwargs.update(
            {
                "retryWrites": True,
                "w": "majority",
                "tls": True,
                "appname": "shopmind-ai-backend",
            }
        )
        if certifi is not None:
            kwargs["tlsCAFile"] = certifi.where()

    return kwargs

def get_async_client() -> motor.motor_asyncio.AsyncIOMotorClient:
    global _async_client
    if _async_client is None:
        uri = MONGODB_URI
        
        try:
            logger.info(f"Connecting to MongoDB async...")
            _async_client = motor.motor_asyncio.AsyncIOMotorClient(
                uri,
                **_atlas_client_kwargs(uri),
            )
            logger.info("✅ Async MongoDB client initialized")
        except Exception as e:
            logger.warning(f"MongoDB async connection error: {str(e)[:150]}")
            _async_client = motor.motor_asyncio.AsyncIOMotorClient(uri)
    
    return _async_client

def get_db():
    """Return async motor database handle."""
    return get_async_client()[MONGODB_DB_NAME]

def get_collection(name: str):
    """Return a named async collection."""
    return get_db()[name]

# ── Sync client (pymongo — used for index creation at startup) ────────────────
_sync_client: Optional[MongoClient] = None

def get_sync_db():
    global _sync_client
    if _sync_client is None:
        uri = MONGODB_URI
        
        try:
            logger.info("Connecting to MongoDB sync...")
            _sync_client = MongoClient(
                uri,
                **_atlas_client_kwargs(uri),
            )
            logger.info("✅ Sync MongoDB client initialized")
        except Exception as e:
            logger.warning(f"MongoDB sync connection error: {str(e)[:150]}")
            _sync_client = MongoClient(uri, serverSelectionTimeoutMS=3000)
    
    return _sync_client[MONGODB_DB_NAME]

# ── Health check ──────────────────────────────────────────────────────────────
async def ping_mongodb() -> bool:
    """Return True if MongoDB Atlas is reachable."""
    try:
        client = get_async_client()
        await client.admin.command("ping")
        return True
    except Exception as exc:
        logger.warning(f"MongoDB ping failed: {exc}")
        return False

# ── Schema / Index bootstrap ──────────────────────────────────────────────────
def ensure_indexes():
    """Create all required indexes on first boot (idempotent)."""
    try:
        db = get_sync_db()

        required_collections = [
            "users",
            "products",
            "products_dataset",
            "products_live",
            "recommendations",
            "product_embeddings",
            "wishlist",
            "cart",
            "orders",
            "search_history",
            "ai_chats",
            "chat_context",
            "user_preferences",
            "sessions",
            "analytics",
            "external_api_cache",
            "market_trends",
        ]
        existing = set(db.list_collection_names())
        for name in required_collections:
            if name not in existing:
                db.create_collection(name)

        # products
        db.products.create_index("product_id", unique=True)
        db.products.create_index("category")
        db.products.create_index("source")
        db.products.create_index("updated_at")
        db.products.create_index([("title", "text"), ("description", "text")])

        # product_embeddings
        db.product_embeddings.create_index("product_id", unique=True)
        db.product_embeddings.create_index("updated_at")

        # recommendations
        db.recommendations.create_index("product_id")
        db.recommendations.create_index([("user_id", 1), ("updated_at", -1)])

        # search_history
        db.search_history.create_index("query")
        db.search_history.create_index("timestamp")
        db.search_history.create_index([("user_id", 1), ("timestamp", -1)])

        # market_trends
        db.market_trends.create_index("category")
        db.market_trends.create_index("recorded_at")

        # products_live
        db.products_live.create_index("product_id", unique=True)
        db.products_live.create_index([("country", 1), ("updated_at", -1)])
        db.products_live.create_index([("source", 1), ("updated_at", -1)])

        # users + user activity collections
        db.users.create_index("id", unique=True, sparse=True)
        db.users.create_index("email", unique=True)
        db.wishlist.create_index([("user_id", 1), ("product_id", 1)])
        db.cart.create_index([("user_id", 1), ("product_id", 1)])

        # orders
        db.orders.create_index([("user_id", 1), ("created_at", -1)])
        db.orders.create_index("order_id", unique=True, sparse=True)

        # ai copilot traces
        db.ai_chats.create_index([("user_id", 1), ("created_at", -1)])
        db.ai_chats.create_index("type")

        # preference/context memory
        db.user_preferences.create_index("user_id", unique=True, sparse=True)
        db.chat_context.create_index([("user_id", 1), ("updated_at", -1)])

        # analytics snapshots/events
        db.analytics.create_index([("event", 1), ("created_at", -1)])
        db.analytics.create_index([("user_id", 1), ("created_at", -1)])

        # auth sessions
        db.sessions.create_index("refresh_token_hash", unique=True, sparse=True)
        db.sessions.create_index([("user_id", 1), ("updated_at", -1)])
        db.sessions.create_index([("expires_at", 1)])

        # optional dataset mirror collection used by hybrid engine
        db.products_dataset.create_index("product_id", unique=True, sparse=True)
        db.products_dataset.create_index("category")

        logger.info("✓ MongoDB indexes ensured")
    except Exception as exc:
        logger.warning(f"Index creation warning: {exc}")
