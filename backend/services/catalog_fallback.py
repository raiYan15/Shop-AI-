"""
ShopMind AI — Catalog Fallback Service
Keeps search/products/recommendation APIs available when MongoDB is unavailable.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

import httpx

logger = logging.getLogger(__name__)

_catalog_loaded = False
_catalog_lock = asyncio.Lock()
_catalog: Dict[str, Dict[str, Any]] = {}
_last_error: Optional[str] = None

_DUMMYJSON_BASE = "https://dummyjson.com"
_PAGE_LIMIT = 100


def _normalize_dummyjson(raw: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "product_id": f"dj_{raw['id']}",
        "title": str(raw.get("title", "")).strip(),
        "description": str(raw.get("description", "")).strip(),
        "brand": str(raw.get("brand", "Unknown")).strip(),
        "category": str(raw.get("category", "general")).strip().lower(),
        "price": float(raw.get("price", 0.0)),
        "rating": float(raw.get("rating", 0.0)),
        "stock": int(raw.get("stock", 0)),
        "thumbnail": str(raw.get("thumbnail", "")),
        "images": raw.get("images", []),
        "tags": raw.get("tags", []),
        "discount": float(raw.get("discountPercentage", 0.0)),
        "source": "dummyjson",
        "updated_at": datetime.now(timezone.utc),
    }


async def ensure_fallback_catalog_loaded(force: bool = False) -> Dict[str, Any]:
    """Warm in-memory DummyJSON catalog used when MongoDB is unavailable."""
    global _catalog_loaded, _catalog, _last_error

    if _catalog_loaded and _catalog and not force:
        return {"loaded": True, "count": len(_catalog), "error": None}

    async with _catalog_lock:
        if _catalog_loaded and _catalog and not force:
            return {"loaded": True, "count": len(_catalog), "error": None}

        try:
            catalog: Dict[str, Dict[str, Any]] = {}
            skip = 0

            async with httpx.AsyncClient(timeout=20.0) as client:
                while True:
                    resp = await client.get(
                        f"{_DUMMYJSON_BASE}/products",
                        params={"limit": _PAGE_LIMIT, "skip": skip},
                    )
                    resp.raise_for_status()
                    data = resp.json()

                    products = data.get("products", [])
                    if not products:
                        break

                    for raw in products:
                        doc = _normalize_dummyjson(raw)
                        catalog[doc["product_id"]] = doc

                    skip += _PAGE_LIMIT
                    total = int(data.get("total", 0))
                    if total and skip >= total:
                        break

            if catalog:
                _catalog = catalog
                _catalog_loaded = True
                _last_error = None
                logger.info(f"✓ Fallback catalog loaded: {len(_catalog)} products")
                return {"loaded": True, "count": len(_catalog), "error": None}

            _catalog_loaded = False
            _last_error = "No products returned from DummyJSON"
            logger.warning("Fallback catalog load returned 0 products")
            return {"loaded": False, "count": len(_catalog), "error": _last_error}

        except Exception as exc:
            _catalog_loaded = bool(_catalog)
            _last_error = str(exc)
            logger.warning(f"Fallback catalog load failed: {_last_error}")
            return {"loaded": _catalog_loaded, "count": len(_catalog), "error": _last_error}


def fallback_catalog_stats() -> Dict[str, Any]:
    products = list(_catalog.values())
    total = len(products)
    if total == 0:
        return {
            "total_products": 0,
            "categories": 0,
            "avg_rating": 0.0,
            "loaded": False,
            "last_error": _last_error,
        }

    categories = len({str(p.get("category", "")) for p in products})
    avg_rating = round(
        sum(float(p.get("rating", 0.0)) for p in products) / total,
        2,
    )
    return {
        "total_products": total,
        "categories": categories,
        "avg_rating": avg_rating,
        "loaded": True,
        "last_error": _last_error,
    }


def get_fallback_product(product_id: str) -> Optional[Dict[str, Any]]:
    return _catalog.get(product_id)


def list_fallback_products(
    page: int = 1,
    limit: int = 20,
    category: Optional[str] = None,
    sort: str = "updated_at",
) -> Tuple[List[Dict[str, Any]], int]:
    products = list(_catalog.values())

    if category:
        products = [p for p in products if str(p.get("category", "")).lower() == category.lower()]

    reverse = sort in ("updated_at", "rating", "price")
    if sort == "rating":
        key_fn = lambda p: float(p.get("rating", 0.0))
    elif sort == "price":
        key_fn = lambda p: float(p.get("price", 0.0))
    elif sort == "title":
        key_fn = lambda p: str(p.get("title", "")).lower()
        reverse = False
    else:
        key_fn = lambda p: str(p.get("product_id", ""))

    products.sort(key=key_fn, reverse=reverse)

    total = len(products)
    start = (max(1, page) - 1) * max(1, limit)
    end = start + max(1, limit)
    return products[start:end], total


def _price_similarity(a: float, b: float) -> float:
    if a <= 0 or b <= 0:
        return 0.5
    return min(a, b) / max(a, b)


def get_fallback_recommendations_for_product(product_id: str, top_k: int = 8) -> List[Dict[str, Any]]:
    anchor = _catalog.get(product_id)
    if not anchor:
        return []

    category = str(anchor.get("category", ""))
    brand = str(anchor.get("brand", ""))
    price = float(anchor.get("price", 0.0))

    candidates: List[Dict[str, Any]] = []
    for pid, doc in _catalog.items():
        if pid == product_id:
            continue

        category_score = 1.0 if str(doc.get("category", "")) == category else 0.2
        brand_score = 1.0 if str(doc.get("brand", "")) == brand else 0.5
        price_score = _price_similarity(price, float(doc.get("price", 0.0)))
        rating_score = float(doc.get("rating", 0.0)) / 5.0
        stock_score = min(float(doc.get("stock", 0.0)) / 100.0, 1.0)

        raw_score = (
            0.3 * category_score
            + 0.25 * brand_score
            + 0.25 * price_score
            + 0.1 * rating_score
            + 0.1 * stock_score
        )
        ai_match = round(raw_score * 100, 1)

        reason_parts = []
        if category_score == 1.0:
            reason_parts.append(f"Same category: {category}")
        if brand_score == 1.0 and brand:
            reason_parts.append(f"Same brand: {brand}")
        if price_score > 0.8:
            reason_parts.append("Similar price range")
        if rating_score > 0.8:
            reason_parts.append("Highly rated")
        if not reason_parts:
            reason_parts.append("Similar catalog profile")

        enriched = {
            **doc,
            "_fallback_ai_match": ai_match,
            "_fallback_reason": "; ".join(reason_parts),
        }
        candidates.append(enriched)

    candidates.sort(key=lambda d: float(d.get("_fallback_ai_match", 0.0)), reverse=True)
    return candidates[: max(1, top_k)]


def get_fallback_recommendations_for_user(top_k: int = 10) -> List[Dict[str, Any]]:
    products = list(_catalog.values())
    products.sort(
        key=lambda d: (float(d.get("rating", 0.0)), float(d.get("stock", 0.0))),
        reverse=True,
    )
    return products[: max(1, top_k)]


def get_fallback_trending(limit: int = 12) -> Dict[str, Any]:
    products = list(_catalog.values())
    category_counts: Dict[str, int] = {}
    for p in products:
        c = str(p.get("category", "general"))
        category_counts[c] = category_counts.get(c, 0) + 1

    trending_categories = [
        {"category": cat, "product_count": count, "rank": i + 1}
        for i, (cat, count) in enumerate(
            sorted(category_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        )
    ]

    top_categories = {c["category"] for c in trending_categories[:5]}
    if top_categories:
        subset = [p for p in products if str(p.get("category", "")) in top_categories]
    else:
        subset = products

    subset.sort(
        key=lambda d: (float(d.get("rating", 0.0)), float(d.get("stock", 0.0))),
        reverse=True,
    )
    chosen = subset[: max(1, limit)]

    return {
        "trending_categories": trending_categories,
        "products": chosen,
        "count": len(chosen),
    }


def get_fallback_new_arrivals(limit: int = 12) -> Dict[str, Any]:
    products = list(_catalog.values())

    def _pid_rank(doc: Dict[str, Any]) -> int:
        pid = str(doc.get("product_id", "dj_0"))
        try:
            return int(pid.split("dj_")[1])
        except Exception:
            return 0

    products.sort(key=_pid_rank, reverse=True)
    chosen = products[: max(1, limit)]
    return {"products": chosen, "count": len(chosen)}
