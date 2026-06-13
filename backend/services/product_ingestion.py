"""
ShopMind AI — Product Ingestion Service
Fetches from DummyJSON (+ future APIs), normalises, and upserts into MongoDB.
"""

import logging
import asyncio
import os
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

import httpx

from .db import get_collection

logger = logging.getLogger(__name__)

# ── Circuit Breaker ───────────────────────────────────────────────────────────
_consecutive_failures = 0
_circuit_open = False
CIRCUIT_THRESHOLD = 3

def is_circuit_open() -> bool:
    return _circuit_open

def _record_success():
    global _consecutive_failures, _circuit_open
    _consecutive_failures = 0
    _circuit_open = False

def _record_failure():
    global _consecutive_failures, _circuit_open
    _consecutive_failures += 1
    if _consecutive_failures >= CIRCUIT_THRESHOLD:
        _circuit_open = True
        logger.error(f"Circuit breaker OPEN after {_consecutive_failures} consecutive failures")

# ── Constants ─────────────────────────────────────────────────────────────────
DUMMYJSON_BASE  = "https://dummyjson.com"
RAPIDAPI_HOST = os.getenv("RAPIDAPI_HOST", "real-time-amazon-data.p.rapidapi.com")
RAPIDAPI_BASE = f"https://{RAPIDAPI_HOST}"
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY", "")
PAGE_LIMIT      = 100        # max per DummyJSON page
MAX_RETRIES     = 3
RETRY_BACKOFF   = 2.0        # seconds (exponential)
REQUEST_TIMEOUT = 20.0       # seconds

# ── Unified Schema ────────────────────────────────────────────────────────────
def normalise_dummyjson(raw: Dict[str, Any]) -> Dict[str, Any]:
    """Map a DummyJSON product dict → unified ShopMind schema."""
    return {
        "product_id"  : f"dj_{raw['id']}",
        "title"       : str(raw.get("title", "")).strip(),
        "description" : str(raw.get("description", "")).strip(),
        "brand"       : str(raw.get("brand", "Unknown")).strip(),
        "category"    : str(raw.get("category", "general")).strip().lower(),
        "price"       : float(raw.get("price", 0.0)),
        "rating"      : float(raw.get("rating", 0.0)),
        "stock"       : int(raw.get("stock", 0)),
        "thumbnail"   : str(raw.get("thumbnail", "")),
        "images"      : raw.get("images", []),
        "tags"        : raw.get("tags", []),
        "discount"    : float(raw.get("discountPercentage", 0.0)),
        "source"      : "dummyjson",
        "updated_at"  : datetime.now(timezone.utc),
    }


def _safe_float(v: Any, default: float = 0.0) -> float:
    try:
        if isinstance(v, str):
            cleaned = "".join(ch for ch in v if ch.isdigit() or ch in ".-")
            return float(cleaned) if cleaned else default
        return float(v)
    except Exception:
        return default


def _safe_int(v: Any, default: int = 0) -> int:
    try:
        if isinstance(v, str):
            cleaned = "".join(ch for ch in v if ch.isdigit() or ch == "-")
            return int(cleaned) if cleaned else default
        return int(v)
    except Exception:
        return default


def normalise_rapidapi(raw: Dict[str, Any], country: str = "US") -> Dict[str, Any]:
    asin = str(raw.get("asin") or raw.get("product_asin") or raw.get("id") or "").strip()
    title = str(raw.get("product_title") or raw.get("title") or raw.get("product_name") or "Live Product").strip()
    if not asin:
        asin = f"generated-{abs(hash((title, country))) % 10**10}"

    price = _safe_float(raw.get("product_price") or raw.get("price") or raw.get("sale_price"), 0.0)
    rating = _safe_float(raw.get("product_star_rating") or raw.get("rating"), 0.0)
    ratings = _safe_int(raw.get("product_num_ratings") or raw.get("rating_count") or 0, 0)

    image = str(raw.get("product_photo") or raw.get("thumbnail") or raw.get("image") or "")
    availability = str(raw.get("product_availability") or raw.get("availability") or "In Stock")
    in_stock = "out" not in availability.lower()

    category = str(raw.get("product_category") or raw.get("category") or "general").strip().lower()
    brand = str(raw.get("product_byline") or raw.get("brand") or "Amazon").strip()

    return {
        "product_id": f"live_{country}_{asin}",
        "title": title,
        "description": str(raw.get("product_description") or raw.get("description") or "").strip(),
        "brand": brand,
        "category": category,
        "price": price,
        "rating": rating,
        "stock": 100 if in_stock else 0,
        "rating_count": str(ratings),
        "thumbnail": image,
        "images": [image] if image else [],
        "tags": ["live", "rapidapi", country.lower()],
        "source": "rapidapi_live",
        "country": country,
        "availability": availability,
        "updated_at": datetime.now(timezone.utc),
    }

# ── HTTP fetch with retry ─────────────────────────────────────────────────────
async def _fetch_json(
    client: httpx.AsyncClient,
    url: str,
    params: dict = None,
    headers: Optional[Dict[str, str]] = None,
) -> Any:
    last_exc = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            r = await client.get(url, params=params, headers=headers, timeout=REQUEST_TIMEOUT)
            r.raise_for_status()
            return r.json()
        except Exception as exc:
            last_exc = exc
            wait = RETRY_BACKOFF ** attempt
            logger.warning(f"Fetch attempt {attempt} failed ({exc}); retrying in {wait}s …")
            await asyncio.sleep(wait)
    raise RuntimeError(f"All {MAX_RETRIES} attempts failed for {url}: {last_exc}")

# ── Ingest DummyJSON ──────────────────────────────────────────────────────────
async def ingest_dummyjson() -> List[str]:
    """
    Fetch every product from DummyJSON, normalise, and upsert into MongoDB.
    Returns list of product_ids that were NEW (not previously seen).
    """
    collection   = get_collection("products")
    new_ids: List[str] = []
    total_fetched = 0
    skip = 0

    async with httpx.AsyncClient() as client:
        while True:
            data = await _fetch_json(
                client,
                f"{DUMMYJSON_BASE}/products",
                {"limit": PAGE_LIMIT, "skip": skip},
            )
            items: List[Dict] = data.get("products", [])
            if not items:
                break

            for raw in items:
                product = normalise_dummyjson(raw)
                pid     = product["product_id"]

                result = await collection.update_one(
                    {"product_id": pid},
                    {"$set": product},
                    upsert=True,
                )
                if result.upserted_id is not None:
                    new_ids.append(pid)

            total_fetched += len(items)
            skip          += PAGE_LIMIT

            # DummyJSON reports total in response
            if total_fetched >= data.get("total", 0):
                break

            await asyncio.sleep(0.2)   # polite rate-limiting

    logger.info(f"✓ Ingestion complete: {total_fetched} fetched, {len(new_ids)} new")
    return new_ids


async def ingest_rapidapi_live(country: str = "US", query: str = "electronics", limit: int = 60) -> List[str]:
    """
    Pull live products from RapidAPI and cache into products_live + unified products.
    """
    if not RAPIDAPI_KEY or RAPIDAPI_KEY.startswith("replace-with-"):
        return []

    products_col = get_collection("products")
    live_col = get_collection("products_live")
    new_ids: List[str] = []

    request_headers = {
        "x-rapidapi-key": RAPIDAPI_KEY,
        "x-rapidapi-host": RAPIDAPI_HOST,
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
        response = await _fetch_json(
            client,
            f"{RAPIDAPI_BASE}/search",
            {"query": query, "country": country, "page": "1"},
            headers=request_headers,
        )

    items = (
        response.get("data", {}).get("products")
        or response.get("products")
        or []
    )

    count = 0
    for raw in items:
        if count >= limit:
            break
        normalized = normalise_rapidapi(raw, country=country)
        pid = normalized["product_id"]

        r_live = await live_col.update_one(
            {"product_id": pid},
            {"$set": normalized},
            upsert=True,
        )
        await products_col.update_one(
            {"product_id": pid},
            {"$set": normalized},
            upsert=True,
        )

        if r_live.upserted_id is not None:
            new_ids.append(pid)
        count += 1

    logger.info("✓ RapidAPI live ingest: %s items (%s new)", count, len(new_ids))
    return new_ids

# ── Search-based ingest (for query-driven discovery) ─────────────────────────
async def ingest_dummyjson_search(query: str) -> List[str]:
    """Ingest products matching a DummyJSON search query."""
    collection = get_collection("products")
    new_ids: List[str] = []

    async with httpx.AsyncClient() as client:
        data = await _fetch_json(
            client,
            f"{DUMMYJSON_BASE}/products/search",
            {"q": query},
        )
        for raw in data.get("products", []):
            product = normalise_dummyjson(raw)
            pid     = product["product_id"]
            result  = await collection.update_one(
                {"product_id": pid}, {"$set": product}, upsert=True
            )
            if result.upserted_id is not None:
                new_ids.append(pid)

    return new_ids

# ── Full pipeline trigger ─────────────────────────────────────────────────────
async def run_ingestion_pipeline() -> Dict[str, Any]:
    """
    Entry point called by the scheduler and the manual trigger endpoint.
    Returns a summary dict.
    """
    started = datetime.now(timezone.utc)
    if _circuit_open:
        return {
            "status"     : "skipped",
            "reason"     : "Circuit breaker open",
            "started_at" : started.isoformat(),
        }

    try:
        new_dummyjson_ids = await ingest_dummyjson()

        live_queries = ["laptop", "smartphone", "headphones", "gaming"]
        new_live_ids: List[str] = []
        for q in live_queries:
            try:
                ids = await ingest_rapidapi_live(country="US", query=q, limit=25)
                new_live_ids.extend(ids)
            except Exception as live_exc:
                logger.warning("RapidAPI ingest warning for query=%s: %s", q, str(live_exc)[:120])

        # de-duplicate
        merged_ids = list(dict.fromkeys(new_dummyjson_ids + new_live_ids))

        _record_success()
        return {
            "status"        : "success",
            "new_products"  : len(merged_ids),
            "new_ids"       : merged_ids,
            "new_dataset_products": len(new_dummyjson_ids),
            "new_live_products": len(new_live_ids),
            "started_at"    : started.isoformat(),
            "finished_at"   : datetime.now(timezone.utc).isoformat(),
        }
    except Exception as exc:
        _record_failure()
        logger.error(f"Ingestion pipeline failed: {exc}")
        return {
            "status"     : "error",
            "error"      : str(exc),
            "started_at" : started.isoformat(),
        }
