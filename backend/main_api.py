"""
ShopMind AI — Live Commerce Platform API
DummyJSON → MongoDB → FAISS → ML Services → React Frontend
"""

import logging
import os
import asyncio
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx
from bson import ObjectId
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query, Depends, Request
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field, EmailStr

load_dotenv(Path(__file__).parent / ".env")

from services.db import ensure_indexes, get_collection, ping_mongodb
from services.embedding_service import get_faiss_index, load_faiss_index, get_embedding_model
from services.search_service import semantic_search, format_product
from services.recommendation_service import (
    get_recommendations_for_product,
    get_recommendations_for_user,
    get_hybrid_recommendation_bundle,
)
from services.market_intelligence import get_trending, get_new_arrivals
from services.rag_service import chat, compare_products, get_knowledge_stats, refresh_knowledge_base, analyze_product_url
from services.pipeline import run_full_pipeline, get_pipeline_status
from services.catalog_fallback import (
    ensure_fallback_catalog_loaded,
    fallback_catalog_stats,
    get_fallback_product,
    list_fallback_products,
    get_fallback_recommendations_for_product,
    get_fallback_recommendations_for_user,
    get_fallback_trending,
    get_fallback_new_arrivals,
)

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger(__name__)

ALLOWED_ORIGINS = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:3000,http://localhost:5173",
).split(",")

RAPIDAPI_HOST = os.getenv("RAPIDAPI_HOST", "real-time-amazon-data.p.rapidapi.com")
RAPIDAPI_BASE_URL = f"https://{RAPIDAPI_HOST}"
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY", "")
RAPIDAPI_CATEGORY_CACHE_TTL_SECONDS = int(os.getenv("RAPIDAPI_CATEGORY_CACHE_TTL_SECONDS", "1800"))
RAPIDAPI_CATEGORY_CACHE_STALE_SECONDS = int(os.getenv("RAPIDAPI_CATEGORY_CACHE_STALE_SECONDS", "21600"))

# country -> cache record
_rapidapi_category_cache: Dict[str, Dict[str, Any]] = {}
_rapidapi_category_cache_lock = asyncio.Lock()

app = FastAPI(
    title="ShopMind AI — Live Commerce Platform",
    description="Auto-updating product catalog with semantic search, recommendations, and RAG",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Pydantic Models ───────────────────────────────────────────────────────────

class SignUpRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    first_name: str = Field(..., min_length=1, max_length=50)
    last_name: str = Field(..., min_length=1, max_length=50)
    phone: str = Field("", max_length=20)


class SignInRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=1)


class RefreshRequest(BaseModel):
    refresh_token: str = Field(..., min_length=20, max_length=512)


class SignOutRequest(BaseModel):
    refresh_token: str = Field(..., min_length=20, max_length=512)


class ProfileUpdateRequest(BaseModel):
    first_name: Optional[str] = Field(None, min_length=1, max_length=80)
    last_name: Optional[str] = Field(None, min_length=1, max_length=80)
    email: Optional[EmailStr] = None
    profile_image: Optional[str] = Field(None, max_length=2000)
    membership_type: Optional[str] = Field(None, min_length=3, max_length=40)
    theme_preference: Optional[str] = Field(None, min_length=3, max_length=20)
    notification_settings: Optional[Dict[str, Any]] = None
    shopping_preferences: Optional[Dict[str, Any]] = None


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(..., min_length=1, max_length=256)
    new_password: str = Field(..., min_length=8, max_length=256)


class CompareRequest(BaseModel):
    product_a: str
    product_b: str


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=1000)
    top_k: int = Field(5, ge=1, le=20)


class ProductUrlAnalysisRequest(BaseModel):
    url: str = Field(..., min_length=8, max_length=2000)


class PaginatedProducts(BaseModel):
    products: List[Dict[str, Any]]
    page: int
    limit: int
    total: int
    pages: int


class ReviewAnalysisRequest(BaseModel):
    product_id: str
    reviews: List[str]


async def _get_products_snapshot(
    page: int,
    limit: int,
    category: Optional[str],
    sort: str,
) -> Dict[str, Any]:
    """Shared products snapshot helper used by paginated and realtime endpoints."""
    try:
        products_col = get_collection("products")
        query: Dict[str, Any] = {}
        if category:
            query["category"] = category.lower()

        total = await products_col.count_documents(query)
        sort_dir = -1 if sort in ("updated_at", "rating", "price") else 1

        cursor = (
            products_col.find(query)
            .sort(sort, sort_dir)
            .skip((page - 1) * limit)
            .limit(limit)
        )

        products: List[Dict[str, Any]] = []
        async for doc in cursor:
            ai_match = round(float(doc.get("rating", 0)) / 5 * 100, 1)
            products.append(format_product(doc, ai_match=ai_match))

        return {
            "products": products,
            "page": page,
            "limit": limit,
            "total": total,
            "pages": max(1, (total + limit - 1) // limit),
            "data_source": "mongodb",
        }
    except Exception as exc:
        logger.warning(f"Products fallback to in-memory catalog: {str(exc)[:120]}")
        await ensure_fallback_catalog_loaded()
        docs, total = list_fallback_products(page=page, limit=limit, category=category, sort=sort)
        products = [format_product(d, ai_match=round(float(d.get("rating", 0)) / 5 * 100, 1)) for d in docs]
        return {
            "products": products,
            "page": page,
            "limit": limit,
            "total": total,
            "pages": max(1, (total + limit - 1) // limit),
            "data_source": "fallback",
        }


# ── Startup ───────────────────────────────────────────────────────────────────

# ── Auth Bearer ──────────────────────────────────────────────────────────────
_bearer = HTTPBearer(auto_error=False)


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(_bearer)):
    """Dependency: validates JWT and returns sanitized user dict."""
    from services.auth_service import decode_access_token, get_user_by_id, _sanitize_user
    if credentials is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    payload = decode_access_token(credentials.credentials)
    if not payload or "sub" not in payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    user = await get_user_by_id(payload["sub"])
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return _sanitize_user(user)


def _client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for", "")
    if forwarded:
        return forwarded.split(",")[0].strip()[:128]
    if request.client and request.client.host:
        return request.client.host[:128]
    return ""


# ── Startup ───────────────────────────────────────────────────────────────────

@app.on_event("startup")
async def startup_event():
    import asyncio

    # Run sync DB index creation in a background thread so it doesn't block startup
    loop = asyncio.get_event_loop()
    loop.run_in_executor(None, _ensure_indexes_safe)

    load_faiss_index()
    get_embedding_model()
    asyncio.create_task(_ensure_user_indexes_bg())
    asyncio.create_task(_warm_fallback_catalog_bg())
    try:
        from scheduler import start_scheduler
        start_scheduler(run_on_startup=False)
        asyncio.create_task(_run_startup_pipeline())
    except Exception as exc:
        logger.warning(f"Scheduler not started: {exc}")
    logger.info("✓ ShopMind AI live platform initialized")


def _ensure_indexes_safe():
    """Run sync index creation in a background thread — never blocks startup."""
    try:
        ensure_indexes()
    except Exception as exc:
        logger.warning(f"DB index creation skipped: {str(exc)[:100]}")


async def _run_startup_pipeline():
    from services.pipeline import run_full_pipeline
    logger.info("Running startup pipeline …")
    await run_full_pipeline()


async def _ensure_user_indexes_bg():
    """Run user index creation as a background task — never blocks startup."""
    from services.auth_service import ensure_user_indexes
    try:
        await ensure_user_indexes()
    except Exception as exc:
        logger.warning(f"User index creation skipped: {str(exc)[:100]}")


async def _warm_fallback_catalog_bg():
    """Warm fallback catalog for degraded mode operations."""
    try:
        result = await ensure_fallback_catalog_loaded()
        if result.get("loaded"):
            logger.info(f"✓ Fallback catalog ready: {result.get('count', 0)} products")
        else:
            logger.warning(f"Fallback catalog unavailable: {result.get('error')}")
    except Exception as exc:
        logger.warning(f"Fallback catalog warmup skipped: {str(exc)[:120]}")


@app.on_event("shutdown")
async def shutdown_event():
    try:
        from scheduler import stop_scheduler
        stop_scheduler()
    except Exception:
        pass


# ── Auth Endpoints ────────────────────────────────────────────────────────────

@app.post("/auth/signup", tags=["Auth"])
async def signup(body: SignUpRequest, request: Request):
    """Register a new user. Returns user info + JWT token."""
    from services.auth_service import create_user, create_access_token, create_session
    try:
        user = await create_user(
            email=body.email,
            password=body.password,
            first_name=body.first_name,
            last_name=body.last_name,
            phone=body.phone,
        )
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        logger.error(f"Signup DB error: {e}")
        raise HTTPException(status_code=503, detail="Database unavailable. Please try again later.")
    token = create_access_token({"sub": user["id"]})
    refresh_token = await create_session(
        user_id=user["id"],
        user_agent=request.headers.get("user-agent", ""),
        ip_address=_client_ip(request),
    )
    return {
        "user": user,
        "access_token": token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@app.post("/auth/signin", tags=["Auth"])
async def signin(body: SignInRequest, request: Request):
    """Authenticate with email + password. Returns user info + JWT token."""
    from services.auth_service import authenticate_user, create_access_token, create_session
    try:
        user = await authenticate_user(body.email, body.password)
    except Exception as e:
        logger.error(f"Signin DB error: {e}")
        raise HTTPException(status_code=503, detail="Database unavailable. Please try again later.")
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    token = create_access_token({"sub": user["id"]})
    refresh_token = await create_session(
        user_id=user["id"],
        user_agent=request.headers.get("user-agent", ""),
        ip_address=_client_ip(request),
    )
    return {
        "user": user,
        "access_token": token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@app.post("/auth/refresh", tags=["Auth"])
async def refresh_token(body: RefreshRequest, request: Request):
    from services.auth_service import refresh_session, create_access_token

    result = await refresh_session(
        refresh_token=body.refresh_token,
        user_agent=request.headers.get("user-agent", ""),
        ip_address=_client_ip(request),
    )
    if not result:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")

    user = result["user"]
    token = create_access_token({"sub": user["id"]})
    return {
        "user": user,
        "access_token": token,
        "refresh_token": result["refresh_token"],
        "token_type": "bearer",
    }


@app.post("/auth/signout", tags=["Auth"])
async def signout(body: SignOutRequest, current_user: dict = Depends(get_current_user)):
    from services.auth_service import revoke_session

    await revoke_session(body.refresh_token)
    return {"ok": True, "user_id": current_user.get("id")}


@app.get("/auth/me", tags=["Auth"])
async def get_me(current_user: dict = Depends(get_current_user)):
    """Return the currently authenticated user."""
    return current_user


@app.put("/auth/profile", tags=["Auth"])
async def update_profile(body: ProfileUpdateRequest, current_user: dict = Depends(get_current_user)):
    from services.auth_service import update_user_profile

    payload = body.model_dump(exclude_none=True)
    updated = await update_user_profile(current_user["id"], payload)
    if not updated:
        raise HTTPException(status_code=404, detail="User not found")
    return {"user": updated}


@app.post("/auth/change-password", tags=["Auth"])
async def change_password(body: ChangePasswordRequest, current_user: dict = Depends(get_current_user)):
    from services.auth_service import change_user_password

    if body.current_password == body.new_password:
        raise HTTPException(status_code=400, detail="New password must be different")

    ok = await change_user_password(current_user["id"], body.current_password, body.new_password)
    if not ok:
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    return {"ok": True}


@app.get("/dashboard/me", tags=["Dashboard"])
async def dashboard_me(current_user: dict = Depends(get_current_user)):
    """Authenticated, user-scoped dashboard payload with dynamic metrics and panels."""
    user_id = current_user["id"]

    users_col = get_collection("users")
    orders_col = get_collection("orders")
    wishlist_col = get_collection("wishlist")
    cart_col = get_collection("cart")
    search_col = get_collection("search_history")
    ai_chats_col = get_collection("ai_chats")
    recs_col = get_collection("recommendations")
    prefs_col = get_collection("user_preferences")

    user_doc = await users_col.find_one({"_id": ObjectId(user_id)})
    if not user_doc:
        raise HTTPException(status_code=404, detail="User not found")

    now = datetime.now(timezone.utc)
    last_30_days = now.timestamp() - (30 * 24 * 3600)

    wishlist_count = await wishlist_col.count_documents({"user_id": user_id})
    cart_count = await cart_col.count_documents({"user_id": user_id})
    order_count = await orders_col.count_documents({"user_id": user_id})
    ai_chat_count = await ai_chats_col.count_documents({"user_id": user_id})

    total_saved = 0.0
    async for order in orders_col.find({"user_id": user_id}).limit(300):
        total_saved += float(order.get("savings", 0) or 0)
        total_saved += float(order.get("discount_value", 0) or 0)
        for item in order.get("items", []) or []:
            list_price = float(item.get("list_price", 0) or 0)
            paid_price = float(item.get("price", 0) or 0)
            qty = int(item.get("quantity", 1) or 1)
            if list_price > paid_price:
                total_saved += (list_price - paid_price) * max(1, qty)

    async for wl in wishlist_col.find({"user_id": user_id}).limit(300):
        total_saved += float(wl.get("deal_savings", 0) or 0)

    category_weights: Dict[str, float] = {}

    def _bump_category(raw: Any, weight: float):
        if not isinstance(raw, str):
            return
        key = raw.strip().lower()
        if not key:
            return
        category_weights[key] = category_weights.get(key, 0) + weight

    async for s in search_col.find({"user_id": user_id}).sort("timestamp", -1).limit(200):
        _bump_category(s.get("category"), 1.4)
        _bump_category(s.get("predicted_category"), 1.2)
    async for w in wishlist_col.find({"user_id": user_id}).limit(200):
        _bump_category(w.get("category"), 2.0)
    async for o in orders_col.find({"user_id": user_id}).limit(200):
        _bump_category(o.get("category"), 2.2)
        for item in o.get("items", []) or []:
            _bump_category(item.get("category"), 2.2)
    async for r in recs_col.find({"user_id": user_id}).limit(120):
        _bump_category(r.get("category"), 1.0)

    favorite_categories = [
        {"name": name.title(), "score": round(score, 2)}
        for name, score in sorted(category_weights.items(), key=lambda kv: kv[1], reverse=True)[:5]
    ]

    recent_searches = []
    async for s in search_col.find({"user_id": user_id}).sort("timestamp", -1).limit(10):
        q = str(s.get("query", "")).strip()
        if q:
            recent_searches.append(q)

    cart_items: List[Dict[str, Any]] = []
    async for c in cart_col.find({"user_id": user_id}).sort("updated_at", -1).limit(20):
        cart_items.append(
            {
                "product_id": c.get("product_id") or c.get("id") or "",
                "name": c.get("product_name") or c.get("title") or c.get("name") or "Unnamed Product",
                "price": float(c.get("price_value", c.get("price", 0)) or 0),
                "quantity": int(c.get("quantity", 1) or 1),
                "thumbnail": c.get("thumbnail") or c.get("image") or "",
            }
        )

    wishlist_items: List[Dict[str, Any]] = []
    async for w in wishlist_col.find({"user_id": user_id}).sort("updated_at", -1).limit(24):
        wishlist_items.append(
            {
                "product_id": w.get("product_id") or w.get("id") or "",
                "name": w.get("product_name") or w.get("title") or w.get("name") or "Wishlist Product",
                "price": float(w.get("price_value", w.get("price", 0)) or 0),
                "category": w.get("category", ""),
                "thumbnail": w.get("thumbnail") or w.get("image") or "",
                "deal_savings": float(w.get("deal_savings", 0) or 0),
            }
        )

    history_items: List[Dict[str, Any]] = []
    async for o in orders_col.find({"user_id": user_id}).sort("created_at", -1).limit(20):
        history_items.append(
            {
                "order_id": o.get("order_id") or str(o.get("_id", "")),
                "created_at": (o.get("created_at") or now).isoformat(),
                "total": float(o.get("total", o.get("amount", 0)) or 0),
                "items_count": len(o.get("items", []) or []),
                "status": o.get("status", "placed"),
            }
        )

    activity_points = {
        "searches": await search_col.count_documents({"user_id": user_id}),
        "orders": order_count,
        "ai_chats": ai_chat_count,
        "wishlist": wishlist_count,
    }

    search_trends = []
    for day_idx in range(7):
        day_ts_from = now.timestamp() - (day_idx + 1) * 24 * 3600
        day_ts_to = now.timestamp() - day_idx * 24 * 3600
        count = await search_col.count_documents(
            {
                "user_id": user_id,
                "timestamp": {
                    "$gte": datetime.fromtimestamp(day_ts_from, timezone.utc),
                    "$lt": datetime.fromtimestamp(day_ts_to, timezone.utc),
                },
            }
        )
        search_trends.append({"day": day_idx + 1, "count": count})
    search_trends.reverse()

    ai_usage_last_30d = await ai_chats_col.count_documents(
        {
            "user_id": user_id,
            "created_at": {"$gte": datetime.fromtimestamp(last_30_days, timezone.utc)},
        }
    )

    user_prefs = await prefs_col.find_one({"user_id": user_id}) or {}

    return {
        "profile": {
            "name": f"{user_doc.get('first_name', '').strip()} {user_doc.get('last_name', '').strip()}".strip() or "User",
            "first_name": user_doc.get("first_name", ""),
            "last_name": user_doc.get("last_name", ""),
            "email": user_doc.get("email", ""),
            "profile_image": user_doc.get("profile_image", ""),
            "role": user_doc.get("role", "user"),
            "membership_type": user_doc.get("membership_type", "standard"),
            "registered_at": (user_doc.get("created_at") or now).isoformat(),
            "last_login": (user_doc.get("last_login") or now).isoformat(),
        },
        "metrics": {
            "total_saved": round(total_saved, 2),
            "orders_count": order_count,
            "ai_chats_count": ai_chat_count,
            "wishlist_count": wishlist_count,
            "cart_count": cart_count,
        },
        "favorite_categories": favorite_categories,
        "recent_searches": recent_searches,
        "cart": {
            "count": cart_count,
            "items": cart_items,
        },
        "wishlist": {
            "count": wishlist_count,
            "items": wishlist_items,
        },
        "history": {
            "orders": history_items,
        },
        "analytics": {
            "shopping_activity": activity_points,
            "search_trends": search_trends,
            "ai_usage_last_30d": ai_usage_last_30d,
            "recommendation_accuracy": round(float(user_prefs.get("recommendation_accuracy", 0.0) or 0.0), 2),
            "most_viewed_categories": favorite_categories[:5],
            "most_purchased_categories": favorite_categories[:5],
        },
        "settings": {
            "theme_preference": user_doc.get("theme_preference", "dark"),
            "notification_settings": user_doc.get("notification_settings", {}),
            "shopping_preferences": user_doc.get("shopping_preferences", {}),
        },
    }


# ── Health & Stats ──────────────────────────────────────────────────────────────

@app.get("/health", tags=["Health"])
async def health_check():
    import asyncio
    try:
        mongo_ok = await asyncio.wait_for(ping_mongodb(), timeout=3.0)
    except asyncio.TimeoutError:
        mongo_ok = False
    index, _ = get_faiss_index()
    return {
        "status": "healthy" if mongo_ok else "degraded",
        "mongodb": "connected" if mongo_ok else "disconnected",
        "faiss_vectors": index.ntotal,
        "models_loaded": True,
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.get("/stats", tags=["Stats"])
async def get_stats():
    index, _ = get_faiss_index()
    try:
        products_col = get_collection("products")
        total = await products_col.count_documents({})
        categories = await products_col.distinct("category")

        pipeline = [
            {"$group": {"_id": None, "avg_rating": {"$avg": "$rating"}}},
        ]
        agg = await products_col.aggregate(pipeline).to_list(length=1)
        avg_rating = round(agg[0]["avg_rating"], 2) if agg else 0.0

        return {
            "total_products": total,
            "index_vectors": index.ntotal,
            "embedding_dimension": index.d if index.ntotal > 0 else 384,
            "categories": len(categories),
            "avg_rating": avg_rating,
            "knowledge_base_entries": get_knowledge_stats()["entries"],
            "data_source": "mongodb",
        }
    except Exception as exc:
        logger.warning(f"Stats fallback to in-memory catalog: {str(exc)[:120]}")
        await ensure_fallback_catalog_loaded()
        fb = fallback_catalog_stats()
        return {
            "total_products": fb["total_products"],
            "index_vectors": index.ntotal,
            "embedding_dimension": index.d if index.ntotal > 0 else 384,
            "categories": fb["categories"],
            "avg_rating": fb["avg_rating"],
            "knowledge_base_entries": get_knowledge_stats()["entries"],
            "data_source": "fallback",
            "fallback_error": fb.get("last_error"),
        }


# ── Products ──────────────────────────────────────────────────────────────────

@app.get("/products", tags=["Products"])
async def list_products(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    category: Optional[str] = None,
    sort: str = Query("updated_at", pattern="^(updated_at|rating|price|title)$"),
):
    return await _get_products_snapshot(page=page, limit=limit, category=category, sort=sort)


@app.get("/products/live", tags=["Products"])
async def list_products_live(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    category: Optional[str] = None,
    sort: str = Query("updated_at", pattern="^(updated_at|rating|price|title)$"),
):
    """Realtime-friendly products snapshot endpoint (polling clients)."""
    payload = await _get_products_snapshot(page=page, limit=limit, category=category, sort=sort)
    return {
        **payload,
        "realtime": True,
        "server_time": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/products/stream", tags=["Products"])
async def stream_products_live(
    request: Request,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    category: Optional[str] = None,
    sort: str = Query("updated_at", pattern="^(updated_at|rating|price|title)$"),
    interval: float = Query(5.0, ge=1.0, le=30.0),
):
    """Server-Sent Events stream for live product snapshots."""

    async def event_generator():
        last_signature: Optional[str] = None

        while True:
            if await request.is_disconnected():
                break

            payload = await _get_products_snapshot(page=page, limit=limit, category=category, sort=sort)
            enriched = {
                **payload,
                "realtime": True,
                "server_time": datetime.now(timezone.utc).isoformat(),
            }

            ids = [str(p.get("product_id", "")) for p in enriched.get("products", [])[:20]]
            signature = f"{enriched.get('data_source')}|{enriched.get('total')}|{','.join(ids)}"
            event_name = "update" if signature != last_signature else "heartbeat"
            last_signature = signature

            yield f"event: {event_name}\n"
            yield f"data: {json.dumps(enriched, default=str)}\n\n"

            await asyncio.sleep(interval)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@app.get("/product/{product_id}", tags=["Products"])
async def get_product(product_id: str):
    try:
        doc = await get_collection("products").find_one({"product_id": product_id})
    except Exception:
        doc = None
    if not doc:
        await ensure_fallback_catalog_loaded()
        doc = get_fallback_product(product_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Product not found")
    return format_product(doc)


# ── Search ────────────────────────────────────────────────────────────────────

@app.get("/search", tags=["Search"])
async def search_products(
    q: str = Query(..., min_length=1, max_length=500),
    k: int = Query(10, ge=1, le=50),
    category: Optional[str] = None,
):
    result = await semantic_search(q, top_k=k, category=category)
    return {
        "query": result["query"],
        "results": result["products"],
        "similarity_scores": result["similarity_scores"],
        "count": result["count"],
        "confidence": result.get("confidence", 0.0),
        "understanding": result.get("understanding", {}),
        "message": result.get("message", "ok"),
    }


# ── Recommendations ───────────────────────────────────────────────────────────

@app.get("/recommendations/{user_id}", tags=["Recommendations"])
async def user_recommendations(
    user_id: str,
    k: int = Query(10, ge=1, le=30),
):
    try:
        recs = await get_recommendations_for_user(user_id, top_k=k)
        source = "mongodb"
    except Exception as exc:
        logger.warning(f"User recommendations fallback: {str(exc)[:120]}")
        await ensure_fallback_catalog_loaded()
        docs = get_fallback_recommendations_for_user(top_k=k)
        recs = []
        for doc in docs:
            ai_match = round(float(doc.get("rating", 0)) / 5 * 100, 1)
            recs.append({
                **format_product(doc, ai_match=ai_match),
                "reason": "Trending product with high ratings",
            })
        source = "fallback"
    return {
        "user_id": user_id,
        "recommendations": recs,
        "count": len(recs),
        "timestamp": datetime.utcnow().isoformat(),
        "data_source": source,
    }


@app.get("/recommendations/hybrid/{user_id}", tags=["Recommendations"])
async def user_hybrid_recommendations(
    user_id: str,
    k: int = Query(12, ge=6, le=24),
    country: str = Query("US", min_length=2, max_length=2),
):
    """
    Hybrid AI recommendation engine:
    historical dataset + live Amazon products + semantic + FAISS + ranking.
    """
    try:
        return await get_hybrid_recommendation_bundle(user_id=user_id, top_k=k, country=country.upper())
    except Exception as exc:
        logger.warning(f"Hybrid recommendations fallback: {str(exc)[:120]}")
        await ensure_fallback_catalog_loaded()
        docs = get_fallback_recommendations_for_user(top_k=k)
        recs = []
        for doc in docs:
            ai_match = round(float(doc.get("rating", 0)) / 5 * 100, 1)
            recs.append({
                **format_product(doc, ai_match=ai_match),
                "why_recommended": "Fallback recommendation from resilient catalog",
                "live_price_indicator": "DATASET",
            })

        now_iso = datetime.now(timezone.utc).isoformat()
        return {
            "user_id": user_id,
            "country": country.upper(),
            "weights": {
                "fusion": {"dataset": 0.60, "semantic": 0.20, "live": 0.20},
                "priority": {"dataset": 0.40, "live": 0.60},
            },
            "summary": {
                "products_analyzed": len(recs),
                "ai_accuracy": round(sum(float(x.get("ai_match", 0)) for x in recs) / max(1, len(recs)), 2),
                "live_product_count": 0,
                "last_update_time": now_iso,
                "fallback_chain": ["products_live", "products_dataset", "dummyjson_backup"],
                "live_cache_source": "fallback",
                "live_cache_updates": 0,
            },
            "sections": {
                "hybrid_recommendations": recs,
                "new_products": recs[: min(8, len(recs))],
                "similar_products": recs[: min(8, len(recs))],
                "trending_ai_students": recs[: min(8, len(recs))],
                "ai_product_insights": [
                    {
                        "product_id": x.get("product_id"),
                        "product_name": x.get("product_name"),
                        "pros": ["Stable fallback recommendation"],
                        "cons": ["Live API currently unavailable"],
                        "best_use_cases": ["General shopping"],
                        "value_for_money_score": round(float(x.get("rating", 0)) / 5 * 100, 1),
                        "recommendation_confidence": float(x.get("ai_match", 0.0)),
                    }
                    for x in recs[: min(6, len(recs))]
                ],
            },
        }


@app.get("/recommendations/product/{product_id}", tags=["Recommendations"])
async def product_recommendations(
    product_id: str,
    k: int = Query(8, ge=1, le=30),
):
    try:
        recs = await get_recommendations_for_product(product_id, top_k=k)
        source = "mongodb"
    except Exception as exc:
        logger.warning(f"Product recommendations fallback: {str(exc)[:120]}")
        await ensure_fallback_catalog_loaded()
        docs = get_fallback_recommendations_for_product(product_id, top_k=k)
        recs = []
        for doc in docs:
            recs.append({
                **format_product(doc, ai_match=float(doc.get("_fallback_ai_match", 0.0))),
                "reason": doc.get("_fallback_reason", "Similar catalog profile"),
            })
        source = "fallback"
    return {
        "product_id": product_id,
        "recommendations": recs,
        "count": len(recs),
        "timestamp": datetime.utcnow().isoformat(),
        "data_source": source,
    }


# ── Compare & Chat ──────────────────────────────────────────────────────────────

@app.post("/compare", tags=["AI"])
async def compare(request: CompareRequest):
    try:
        return await compare_products(request.product_a, request.product_b)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@app.post("/chat", tags=["AI"])
async def rag_chat(request: ChatRequest):
    try:
        return await chat(request.message, top_k=request.top_k)
    except Exception as exc:
        logger.warning(f"RAG chat fallback: {str(exc)[:120]}")
        await ensure_fallback_catalog_loaded()
        docs = get_fallback_recommendations_for_user(top_k=request.top_k)
        products = [
            format_product(d, ai_match=round(float(d.get("rating", 0)) / 5 * 100, 1))
            for d in docs
        ]
        reply_lines = [
            f"Based on your question about '{request.message}':",
            "",
            "MongoDB is currently unavailable, so I used the fallback live catalog.",
        ]
        if products:
            top = products[0]
            reply_lines += [
                f"✓ Top match: **{top['product_name']}** (AI Match: {top['ai_match']}%)",
                f"  Price: {top['price']} | Rating: {top['rating']}★",
            ]
        return {
            "message": request.message,
            "reply": "\n".join(reply_lines),
            "products": products,
            "response": "\n".join(reply_lines),
            "confidence": 0.55,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data_source": "fallback",
        }


@app.post("/ai/analyze-product-url", tags=["AI"])
async def analyze_product_url_endpoint(request: ProductUrlAnalysisRequest):
    """Analyze ecommerce product URLs and return AI shopping report + alternatives."""
    url = request.url.strip()
    if not (url.startswith("http://") or url.startswith("https://")):
        raise HTTPException(status_code=400, detail="A valid product URL is required")
    report = await analyze_product_url(url)
    return {
        "status": "ok",
        "report": report,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# ── Market Intelligence ─────────────────────────────────────────────────────────

@app.get("/trending", tags=["Market"])
async def trending(limit: int = Query(12, ge=1, le=50)):
    try:
        data = await get_trending(limit=limit)
        return {**data, "items": data.get("products", []), "data_source": "mongodb"}
    except Exception as exc:
        logger.warning(f"Trending fallback: {str(exc)[:120]}")
        await ensure_fallback_catalog_loaded()
        data = get_fallback_trending(limit=limit)
        return {**data, "items": data.get("products", []), "data_source": "fallback"}


@app.get("/new-arrivals", tags=["Market"])
async def new_arrivals(limit: int = Query(12, ge=1, le=50)):
    try:
        data = await get_new_arrivals(limit=limit)
        return {**data, "data_source": "mongodb"}
    except Exception as exc:
        logger.warning(f"New arrivals fallback: {str(exc)[:120]}")
        await ensure_fallback_catalog_loaded()
        data = get_fallback_new_arrivals(limit=limit)
        return {**data, "data_source": "fallback"}


@app.get("/external/amazon/product-category-list", tags=["External API"])
async def amazon_product_category_list(country: str = Query("US", min_length=2, max_length=2)):
    """
    Secure backend proxy for RapidAPI product-category-list.
    Keeps x-rapidapi-key on server and returns provider payload to frontend.
    """
    fallback_categories = [
        "Electronics",
        "Computers & Accessories",
        "Home & Kitchen",
        "Books",
        "Fashion",
        "Beauty",
        "Sports & Outdoors",
        "Toys & Games",
        "Grocery",
        "Office Products",
    ]

    requested_country = country.upper()
    now_ts = time.time()
    cache_col = get_collection("external_api_cache")
    cache_key = f"amazon_category_list::{requested_country}"

    db_cached = await cache_col.find_one({"key": cache_key})
    if db_cached and db_cached.get("expires_at") and db_cached["expires_at"].timestamp() > now_ts:
        return {
            "source": "rapidapi",
            "endpoint": "product-category-list",
            "country": requested_country,
            "fetched_at": db_cached.get("fetched_at", datetime.now(timezone.utc).isoformat()),
            "cache": {
                "status": "mongodb-hit",
                "ttl_seconds": RAPIDAPI_CATEGORY_CACHE_TTL_SECONDS,
            },
            "message": "Live categories loaded from secure cache",
            "data": db_cached.get("payload", {}),
        }

    cached = _rapidapi_category_cache.get(requested_country)
    if cached and cached.get("expires_at", 0) > now_ts:
        return {
            "source": "rapidapi",
            "endpoint": "product-category-list",
            "country": requested_country,
            "fetched_at": cached["fetched_at"],
            "cache": {
                "status": "hit",
                "ttl_seconds": RAPIDAPI_CATEGORY_CACHE_TTL_SECONDS,
            },
            "data": cached["payload"],
        }

    async def _fetch_upstream(country_code: str) -> Dict[str, Any]:
        if not RAPIDAPI_KEY:
            raise RuntimeError("RapidAPI key not configured")

        url = f"{RAPIDAPI_BASE_URL}/product-category-list"
        params = {"country": country_code}
        headers = {
            "x-rapidapi-key": RAPIDAPI_KEY,
            "x-rapidapi-host": RAPIDAPI_HOST,
            "Content-Type": "application/json",
        }
        retry_statuses = {429, 500, 503}
        attempts = 3
        wait_schedule = [0.6, 1.4, 2.5]

        last_error: Optional[str] = None
        async with httpx.AsyncClient(timeout=15.0) as client:
            for i in range(attempts):
                try:
                    upstream = await client.get(url, headers=headers, params=params)
                    if upstream.status_code < 400:
                        return upstream.json()
                    if upstream.status_code in retry_statuses and i < attempts - 1:
                        await asyncio.sleep(wait_schedule[i])
                        continue
                    last_error = f"status={upstream.status_code} body={upstream.text[:120]}"
                    break
                except httpx.TimeoutException:
                    last_error = "timeout"
                    if i < attempts - 1:
                        await asyncio.sleep(wait_schedule[i])
                        continue
                    break

        raise RuntimeError(last_error or "upstream request failed")

    async with _rapidapi_category_cache_lock:
        # Re-check after lock to avoid duplicate upstream calls
        cached = _rapidapi_category_cache.get(requested_country)
        now_ts = time.time()
        if cached and cached.get("expires_at", 0) > now_ts:
            return {
                "source": "rapidapi",
                "endpoint": "product-category-list",
                "country": requested_country,
                "fetched_at": cached["fetched_at"],
                "cache": {
                    "status": "hit",
                    "ttl_seconds": RAPIDAPI_CATEGORY_CACHE_TTL_SECONDS,
                },
                "data": cached["payload"],
            }

        try:
            payload = await _fetch_upstream(requested_country)
            fetched_at = datetime.now(timezone.utc).isoformat()
            refreshed_at_ts = time.time()
            _rapidapi_category_cache[requested_country] = {
                "payload": payload,
                "fetched_at": fetched_at,
                "expires_at": refreshed_at_ts + max(1, RAPIDAPI_CATEGORY_CACHE_TTL_SECONDS),
                "stale_until": refreshed_at_ts + max(1, RAPIDAPI_CATEGORY_CACHE_STALE_SECONDS),
            }
            result = {
                "source": "rapidapi",
                "endpoint": "product-category-list",
                "country": requested_country,
                "fetched_at": fetched_at,
                "cache": {
                    "status": "miss",
                    "ttl_seconds": RAPIDAPI_CATEGORY_CACHE_TTL_SECONDS,
                },
                "message": "Live categories loaded successfully",
                "data": payload,
            }
            await cache_col.update_one(
                {"key": cache_key},
                {
                    "$set": {
                        "key": cache_key,
                        "country": requested_country,
                        "payload": payload,
                        "fetched_at": fetched_at,
                        "expires_at": datetime.fromtimestamp(
                            refreshed_at_ts + max(1, RAPIDAPI_CATEGORY_CACHE_TTL_SECONDS), timezone.utc
                        ),
                        "stale_until": datetime.fromtimestamp(
                            refreshed_at_ts + max(1, RAPIDAPI_CATEGORY_CACHE_STALE_SECONDS), timezone.utc
                        ),
                        "updated_at": datetime.now(timezone.utc),
                    }
                },
                upsert=True,
            )
            return result
        except httpx.TimeoutException:
            if cached and cached.get("stale_until", 0) > time.time():
                logger.warning("RapidAPI category-list timeout; serving stale cache for country=%s", requested_country)
                return {
                    "source": "rapidapi",
                    "endpoint": "product-category-list",
                    "country": requested_country,
                    "fetched_at": cached["fetched_at"],
                    "cache": {
                        "status": "stale-fallback",
                        "ttl_seconds": RAPIDAPI_CATEGORY_CACHE_TTL_SECONDS,
                    },
                    "message": "Live data temporarily unavailable. Displaying cached categories.",
                    "data": cached["payload"],
                }
            if db_cached and db_cached.get("payload"):
                return {
                    "source": "rapidapi",
                    "endpoint": "product-category-list",
                    "country": requested_country,
                    "fetched_at": db_cached.get("fetched_at", datetime.now(timezone.utc).isoformat()),
                    "cache": {"status": "mongodb-stale", "ttl_seconds": RAPIDAPI_CATEGORY_CACHE_TTL_SECONDS},
                    "message": "Live data temporarily unavailable. Displaying cached categories.",
                    "data": db_cached.get("payload", {}),
                }
            return {
                "source": "fallback",
                "endpoint": "product-category-list",
                "country": requested_country,
                "fetched_at": datetime.now(timezone.utc).isoformat(),
                "cache": {"status": "fallback", "ttl_seconds": 0},
                "message": "Live data temporarily unavailable. Displaying cached categories.",
                "data": {"categories": fallback_categories},
            }
        except HTTPException as http_exc:
            if cached and cached.get("stale_until", 0) > time.time():
                logger.warning(
                    "RapidAPI category-list upstream failure; serving stale cache for country=%s detail=%s",
                    requested_country,
                    http_exc.detail,
                )
                return {
                    "source": "rapidapi",
                    "endpoint": "product-category-list",
                    "country": requested_country,
                    "fetched_at": cached["fetched_at"],
                    "cache": {
                        "status": "stale-fallback",
                        "ttl_seconds": RAPIDAPI_CATEGORY_CACHE_TTL_SECONDS,
                    },
                    "message": "Live data temporarily unavailable. Displaying cached categories.",
                    "data": cached["payload"],
                }
            if db_cached and db_cached.get("payload"):
                return {
                    "source": "rapidapi",
                    "endpoint": "product-category-list",
                    "country": requested_country,
                    "fetched_at": db_cached.get("fetched_at", datetime.now(timezone.utc).isoformat()),
                    "cache": {"status": "mongodb-stale", "ttl_seconds": RAPIDAPI_CATEGORY_CACHE_TTL_SECONDS},
                    "message": "Live data temporarily unavailable. Displaying cached categories.",
                    "data": db_cached.get("payload", {}),
                }
            return {
                "source": "fallback",
                "endpoint": "product-category-list",
                "country": requested_country,
                "fetched_at": datetime.now(timezone.utc).isoformat(),
                "cache": {"status": "fallback", "ttl_seconds": 0},
                "message": "Live data temporarily unavailable. Displaying cached categories.",
                "data": {"categories": fallback_categories},
            }
        except Exception as exc:
            logger.error(f"RapidAPI category proxy error: {exc}")
            if cached and cached.get("stale_until", 0) > time.time():
                return {
                    "source": "rapidapi",
                    "endpoint": "product-category-list",
                    "country": requested_country,
                    "fetched_at": cached["fetched_at"],
                    "cache": {
                        "status": "stale-fallback",
                        "ttl_seconds": RAPIDAPI_CATEGORY_CACHE_TTL_SECONDS,
                    },
                    "message": "Live data temporarily unavailable. Displaying cached categories.",
                    "data": cached["payload"],
                }
            if db_cached and db_cached.get("payload"):
                return {
                    "source": "rapidapi",
                    "endpoint": "product-category-list",
                    "country": requested_country,
                    "fetched_at": db_cached.get("fetched_at", datetime.now(timezone.utc).isoformat()),
                    "cache": {"status": "mongodb-stale", "ttl_seconds": RAPIDAPI_CATEGORY_CACHE_TTL_SECONDS},
                    "message": "Live data temporarily unavailable. Displaying cached categories.",
                    "data": db_cached.get("payload", {}),
                }
            return {
                "source": "fallback",
                "endpoint": "product-category-list",
                "country": requested_country,
                "fetched_at": datetime.now(timezone.utc).isoformat(),
                "cache": {"status": "fallback", "ttl_seconds": 0},
                "message": "Live data temporarily unavailable. Displaying cached categories.",
                "data": {"categories": fallback_categories},
            }


# ── Pipeline ──────────────────────────────────────────────────────────────────

@app.post("/ingest/trigger", tags=["Pipeline"])
async def trigger_ingest():
    result = await run_full_pipeline()
    if result.get("status") == "error":
        raise HTTPException(status_code=500, detail=result.get("error"))
    return result


@app.get("/pipeline/status", tags=["Pipeline"])
async def pipeline_status():
    return get_pipeline_status()


# ── Legacy compatibility (frontend may still call these) ────────────────────────

@app.post("/search", tags=["Search"])
async def search_post(body: Dict[str, Any]):
    q = body.get("query", "")
    k = body.get("top_k", 10)
    if not q:
        raise HTTPException(status_code=400, detail="query required")
    try:
        result = await semantic_search(q, top_k=k)
        return {
            "query": result["query"],
            "results": result["products"],
            "count": result["count"],
            "confidence": result.get("confidence", 0.0),
            "understanding": result.get("understanding", {}),
            "message": result.get("message", "ok"),
            "data_source": "mongodb",
        }
    except Exception as exc:
        logger.warning(f"POST /search fallback: {str(exc)[:120]}")
        await ensure_fallback_catalog_loaded()
        docs = get_fallback_recommendations_for_user(top_k=k)
        products = [
            format_product(d, ai_match=round(float(d.get("rating", 0)) / 5 * 100, 1))
            for d in docs
        ]
        return {
            "query": q,
            "results": products,
            "count": len(products),
            "confidence": 35.0 if products else 0.0,
            "understanding": {},
            "message": "Fallback catalog results",
            "data_source": "fallback",
        }


@app.get("/search-quick", tags=["Search"])
async def search_quick(
    q: str = Query(..., min_length=1, max_length=500),
    k: int = Query(5, ge=1, le=20),
):
    """Compatibility endpoint expected by frontend quick-search helper."""
    return await search_products(q=q, k=k)


@app.post("/recommend", tags=["Recommendations"])
async def recommend_legacy(body: Dict[str, Any]):
    product_id = body.get("product_id")
    top_k = body.get("top_k", 8)
    if not product_id:
        raise HTTPException(status_code=400, detail="product_id required")
    try:
        recs = await get_recommendations_for_product(product_id, top_k=top_k)
        source = "mongodb"
    except Exception as exc:
        logger.warning(f"Legacy recommend fallback: {str(exc)[:120]}")
        await ensure_fallback_catalog_loaded()
        docs = get_fallback_recommendations_for_product(product_id, top_k=top_k)
        recs = [
            {
                **format_product(d, ai_match=float(d.get("_fallback_ai_match", 0.0))),
                "reason": d.get("_fallback_reason", "Similar catalog profile"),
            }
            for d in docs
        ]
        source = "fallback"
    return {
        "query_product_id": product_id,
        "recommendations": recs,
        "count": len(recs),
        "timestamp": datetime.utcnow(),
        "data_source": source,
    }


@app.post("/copilot-advice", tags=["AI"])
async def copilot_legacy(body: Dict[str, Any]):
    q = body.get("query", "")
    top_k = body.get("top_k", 5)
    try:
        result = await chat(q, top_k=top_k)
    except Exception:
        result = await rag_chat(ChatRequest(message=q or "help me choose", top_k=top_k))
    return {
        "query": q,
        "advice": result.get("reply", ""),
        "retrieved_products": result.get("products", []),
        "confidence": result.get("confidence", 0.5),
        "timestamp": result.get("timestamp", datetime.now(timezone.utc).isoformat()),
        "response": result.get("reply", ""),
        "data_source": result.get("data_source", "mongodb"),
    }


@app.post("/analyze-reviews", tags=["AI"])
async def analyze_reviews(body: ReviewAnalysisRequest):
    """Compatibility endpoint expected by existing phase test scripts."""
    from phase3_5_integration import analyze_product_reviews

    analysis_results = analyze_product_reviews(body.reviews)

    analysis = []
    for review, (sentiment, confidence) in zip(body.reviews, analysis_results["sentiments"]):
        analysis.append(
            {
                "sentiment": sentiment,
                "confidence": confidence,
                "text": review[:200],
            }
        )

    summary = {
        "positive_count": analysis_results["positive_count"],
        "negative_count": analysis_results["negative_count"],
        "neutral_count": analysis_results["neutral_count"],
        "overall_sentiment": analysis_results["overall_sentiment"],
        "key_strengths": analysis_results["key_strengths"][:5],
        "key_weaknesses": analysis_results["key_weaknesses"][:5],
        "average_confidence": analysis_results["average_confidence"],
    }

    return {
        "product_id": body.product_id,
        "analysis": analysis,
        "summary": summary,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main_api:app",
        host=os.getenv("API_HOST", "0.0.0.0"),
        port=int(os.getenv("API_PORT", 8000)),
        reload=os.getenv("API_RELOAD", "true").lower() == "true",
    )
