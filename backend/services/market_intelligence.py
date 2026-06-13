"""
ShopMind AI — Market Intelligence Service
Tracks price drops, new arrivals, and trending categories.
"""

import logging
from collections import Counter
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List

from .db import get_collection

logger = logging.getLogger(__name__)


async def analyze_market_trends() -> Dict[str, Any]:
    products_col = get_collection("products")
    trends_col = get_collection("market_trends")
    now = datetime.now(timezone.utc)

    all_products = await products_col.find({}).to_list(length=5000)

    category_counts: Counter = Counter()
    price_drops: List[Dict[str, Any]] = []
    high_rated: List[Dict[str, Any]] = []

    for p in all_products:
        cat = p.get("category", "general")
        category_counts[cat] += 1

        discount = float(p.get("discount", 0))
        if discount >= 10:
            price_drops.append({
                "product_id": p["product_id"],
                "title": p.get("title"),
                "discount": discount,
                "price": p.get("price"),
                "category": cat,
            })

        rating = float(p.get("rating", 0))
        if rating >= 4.5:
            high_rated.append({
                "product_id": p["product_id"],
                "title": p.get("title"),
                "rating": rating,
                "category": cat,
            })

    trending_categories = [
        {"category": cat, "product_count": count, "rank": i + 1}
        for i, (cat, count) in enumerate(category_counts.most_common(10))
    ]

    price_drops.sort(key=lambda x: x["discount"], reverse=True)
    high_rated.sort(key=lambda x: x["rating"], reverse=True)

    trend_doc = {
        "trending_categories": trending_categories,
        "price_drops": price_drops[:20],
        "top_rated": high_rated[:20],
        "total_products": len(all_products),
        "recorded_at": now,
    }

    await trends_col.insert_one(trend_doc)

    return trend_doc


async def get_trending(limit: int = 12) -> Dict[str, Any]:
    trends_col = get_collection("market_trends")
    products_col = get_collection("products")

    latest = await trends_col.find_one(sort=[("recorded_at", -1)])
    if not latest:
        latest = await analyze_market_trends()

    trending_cats = [t["category"] for t in latest.get("trending_categories", [])[:5]]
    if not trending_cats:
        cursor = products_col.find({}, sort=[("rating", -1)], limit=limit)
    else:
        cursor = products_col.find(
            {"category": {"$in": trending_cats}},
            sort=[("rating", -1), ("stock", -1)],
            limit=limit,
        )

    products = []
    async for doc in cursor:
        products.append({
            "product_id": doc["product_id"],
            "title": doc.get("title"),
            "category": doc.get("category"),
            "price": doc.get("price"),
            "rating": doc.get("rating"),
            "thumbnail": doc.get("thumbnail"),
            "discount": doc.get("discount", 0),
        })

    return {
        "trending_categories": latest.get("trending_categories", []),
        "products": products,
        "count": len(products),
    }


async def get_new_arrivals(limit: int = 12) -> Dict[str, Any]:
    products_col = get_collection("products")
    cutoff = datetime.now(timezone.utc) - timedelta(days=7)

    cursor = products_col.find(
        {"updated_at": {"$gte": cutoff}},
        sort=[("updated_at", -1)],
        limit=limit,
    )

    products = []
    async for doc in cursor:
        products.append({
            "product_id": doc["product_id"],
            "title": doc.get("title"),
            "category": doc.get("category"),
            "price": doc.get("price"),
            "rating": doc.get("rating"),
            "thumbnail": doc.get("thumbnail"),
            "updated_at": doc.get("updated_at"),
        })

    if not products:
        cursor = products_col.find({}, sort=[("updated_at", -1)], limit=limit)
        async for doc in cursor:
            products.append({
                "product_id": doc["product_id"],
                "title": doc.get("title"),
                "category": doc.get("category"),
                "price": doc.get("price"),
                "rating": doc.get("rating"),
                "thumbnail": doc.get("thumbnail"),
                "updated_at": doc.get("updated_at"),
            })

    return {"products": products, "count": len(products)}
