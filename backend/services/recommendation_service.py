"""
ShopMind AI — Recommendation Service
Category + brand + price similarity. No retraining — reads live from MongoDB.
"""

import logging
import os
from collections import Counter, defaultdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import httpx

from .db import get_collection
from .embedding_service import encode_texts, get_faiss_index, persist_faiss_index
from .search_service import compute_ai_match_score, format_product

logger = logging.getLogger(__name__)

RAPIDAPI_HOST = os.getenv("RAPIDAPI_HOST", "real-time-amazon-data.p.rapidapi.com")
RAPIDAPI_BASE_URL = f"https://{RAPIDAPI_HOST}"
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY", "")
LIVE_PRODUCTS_REFRESH_SECONDS = int(os.getenv("LIVE_PRODUCTS_REFRESH_SECONDS", "1800"))


def _price_similarity(a: float, b: float) -> float:
    if a <= 0 or b <= 0:
        return 0.5
    ratio = min(a, b) / max(a, b)
    return ratio


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if isinstance(value, str):
            cleaned = "".join(ch for ch in value if ch.isdigit() or ch in ".-")
            return float(cleaned) if cleaned else default
        return float(value)
    except Exception:
        return default


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        if isinstance(value, str):
            cleaned = "".join(ch for ch in value if ch.isdigit() or ch == "-")
            return int(cleaned) if cleaned else default
        return int(value)
    except Exception:
        return default


def _bound01(v: float) -> float:
    return max(0.0, min(1.0, v))


def _parse_live_item(raw: Dict[str, Any], country: str) -> Dict[str, Any]:
    asin = str(raw.get("asin") or raw.get("product_id") or raw.get("id") or raw.get("slug") or "").strip()
    if not asin:
        title_seed = str(raw.get("product_title") or raw.get("title") or "item").strip().lower().replace(" ", "-")
        asin = f"generated-{title_seed[:40]}"

    title = str(raw.get("product_title") or raw.get("title") or "Live Product")
    desc = str(raw.get("product_description") or raw.get("description") or "")
    brand = str(raw.get("product_byline") or raw.get("brand") or raw.get("manufacturer") or "")
    category = str(raw.get("product_category") or raw.get("category") or "general").lower()

    price = _safe_float(
        raw.get("product_price")
        or raw.get("price")
        or raw.get("product_minimum_offer_price")
        or raw.get("typical_price"),
        0.0,
    )

    rating = _safe_float(raw.get("product_star_rating") or raw.get("rating") or 0.0, 0.0)
    rating_count = _safe_int(raw.get("product_num_ratings") or raw.get("rating_count") or raw.get("reviews") or 0)
    popularity = min(1.0, rating_count / 5000.0)

    image = str(raw.get("product_photo") or raw.get("thumbnail") or raw.get("image") or "")
    product_url = str(raw.get("product_url") or raw.get("url") or "")
    availability = str(raw.get("availability") or raw.get("delivery") or "In Stock")

    return {
        "product_id": f"live::{country}::{asin}",
        "asin": asin,
        "title": title,
        "description": desc,
        "brand": brand,
        "category": category,
        "price": price,
        "rating": rating,
        "rating_count": str(max(0, rating_count)),
        "stock": 100 if "out" not in availability.lower() else 0,
        "thumbnail": image,
        "images": [image] if image else [],
        "tags": ["new-arrival", "live-amazon"],
        "availability": availability,
        "country": country,
        "source": "live_api",
        "product_url": product_url,
        "popularity": popularity,
        "updated_at": datetime.now(timezone.utc),
        "created_at": datetime.now(timezone.utc),
    }


async def _fetch_live_products_from_api(country: str, keywords: List[str], limit: int = 40) -> List[Dict[str, Any]]:
    if not RAPIDAPI_KEY:
        return []

    search_terms = [k.strip() for k in keywords if k and k.strip()]
    if not search_terms:
        search_terms = ["electronics", "laptop", "headphones"]

    headers = {
        "x-rapidapi-key": RAPIDAPI_KEY,
        "x-rapidapi-host": RAPIDAPI_HOST,
        "Content-Type": "application/json",
    }

    candidates: List[Dict[str, Any]] = []
    seen: set[str] = set()

    async with httpx.AsyncClient(timeout=15.0) as client:
        for term in search_terms[:4]:
            if len(candidates) >= limit:
                break

            paths = ["/search", "/product-search"]
            params_variants = [
                {"query": term, "country": country, "page": "1"},
                {"query": term, "country": country, "sort_by": "RELEVANCE", "page": "1"},
            ]

            for path in paths:
                if len(candidates) >= limit:
                    break
                for params in params_variants:
                    try:
                        response = await client.get(f"{RAPIDAPI_BASE_URL}{path}", headers=headers, params=params)
                    except Exception:
                        continue

                    if response.status_code >= 400:
                        continue

                    try:
                        payload = response.json()
                    except Exception:
                        continue

                    raw_items = (
                        payload.get("data", {}).get("products")
                        or payload.get("data", {}).get("items")
                        or payload.get("products")
                        or payload.get("items")
                        or []
                    )

                    if not isinstance(raw_items, list) or not raw_items:
                        continue

                    for raw in raw_items:
                        parsed = _parse_live_item(raw, country=country)
                        pid = parsed["product_id"]
                        if pid in seen:
                            continue
                        seen.add(pid)
                        candidates.append(parsed)
                        if len(candidates) >= limit:
                            break

    return candidates[:limit]


async def _cache_live_products(country: str, user_keywords: List[str], min_items: int = 24) -> Dict[str, Any]:
    live_col = get_collection("products_live")
    now = datetime.now(timezone.utc)
    fresh_after = datetime.fromtimestamp(now.timestamp() - max(60, LIVE_PRODUCTS_REFRESH_SECONDS), tz=timezone.utc)

    fresh_docs = await live_col.find(
        {"country": country, "updated_at": {"$gte": fresh_after}},
        sort=[("updated_at", -1), ("rating", -1)],
        limit=max(min_items * 2, 50),
    ).to_list(length=max(min_items * 2, 50))

    if len(fresh_docs) >= min_items:
        return {"items": fresh_docs, "source": "mongo_live_cache", "updated": 0}

    live_items = await _fetch_live_products_from_api(country=country, keywords=user_keywords, limit=max(40, min_items * 2))

    upserts = 0
    for item in live_items:
        await live_col.update_one(
            {"product_id": item["product_id"]},
            {
                "$set": {
                    **item,
                    "updated_at": now,
                },
                "$setOnInsert": {
                    "created_at": now,
                },
            },
            upsert=True,
        )
        upserts += 1

    if upserts:
        await _incremental_embed_live_products(live_items)

    cached = await live_col.find(
        {"country": country},
        sort=[("updated_at", -1), ("rating", -1)],
        limit=max(min_items * 2, 60),
    ).to_list(length=max(min_items * 2, 60))

    return {
        "items": cached,
        "source": "live_api" if upserts else "mongo_live_cache",
        "updated": upserts,
    }


async def _incremental_embed_live_products(live_docs: List[Dict[str, Any]]) -> int:
    if not live_docs:
        return 0

    embeddings_col = get_collection("product_embeddings")
    index, id_map = get_faiss_index()
    existing_ids = set(id_map)

    batch_texts: List[str] = []
    batch_ids: List[str] = []
    for doc in live_docs:
        pid = str(doc.get("product_id") or "")
        if not pid:
            continue
        text = " ".join(
            p
            for p in [
                str(doc.get("title", "")),
                str(doc.get("description", "")),
                str(doc.get("category", "")),
                str(doc.get("brand", "")),
                " ".join(str(t) for t in (doc.get("tags") or [])),
            ]
            if p
        )
        if not text:
            continue
        batch_texts.append(text)
        batch_ids.append(pid)

    if not batch_texts:
        return 0

    vectors = encode_texts(batch_texts)

    new_vectors = []
    new_ids = []
    for idx, pid in enumerate(batch_ids):
        vector = vectors[idx]
        await embeddings_col.update_one(
            {"product_id": pid},
            {
                "$set": {
                    "product_id": pid,
                    "embedding": vector.tolist(),
                    "model": "sentence-transformers/all-MiniLM-L6-v2",
                    "updated_at": datetime.now(timezone.utc),
                }
            },
            upsert=True,
        )

        if pid not in existing_ids:
            new_vectors.append(vector)
            new_ids.append(pid)
            existing_ids.add(pid)

    if new_vectors:
        import numpy as np

        index.add(np.array(new_vectors, dtype="float32"))
        id_map.extend(new_ids)
        persist_faiss_index()

    return len(new_ids)


def _get_price_affinity(price: float, preferred_price: float) -> float:
    if price <= 0 or preferred_price <= 0:
        return 0.5
    ratio = min(price, preferred_price) / max(price, preferred_price)
    return _bound01(ratio)


async def _build_user_profile(user_id: str) -> Dict[str, Any]:
    search_col = get_collection("search_history")
    wishlist_col = get_collection("wishlist")
    cart_col = get_collection("cart")

    recent_searches = await search_col.find(
        {"user_id": user_id} if user_id and user_id != "guest" else {},
        sort=[("timestamp", -1)],
        limit=25,
    ).to_list(length=25)

    wishlist_items = []
    cart_items = []
    if user_id and user_id != "guest":
        wishlist_items = await wishlist_col.find({"user_id": user_id}, limit=30).to_list(length=30)
        cart_items = await cart_col.find({"user_id": user_id}, limit=30).to_list(length=30)

    query_terms: List[str] = []
    for item in recent_searches:
        q = str(item.get("query") or "").strip()
        if q:
            query_terms.append(q)

    category_counter: Counter[str] = Counter()
    brand_counter: Counter[str] = Counter()
    price_points: List[float] = []

    for item in wishlist_items + cart_items:
        category = str(item.get("category") or "").strip().lower()
        brand = str(item.get("brand") or "").strip().lower()
        if category:
            category_counter[category] += 1
        if brand:
            brand_counter[brand] += 1
        price = _safe_float(item.get("price") or item.get("price_value"), 0.0)
        if price > 0:
            price_points.append(price)

    interactions = len(recent_searches) + len(wishlist_items) + len(cart_items)
    is_existing = interactions >= 3

    if price_points:
        sorted_points = sorted(price_points)
        preferred_price = sorted_points[len(sorted_points) // 2]
    else:
        preferred_price = 100.0

    return {
        "user_id": user_id,
        "is_existing_user": is_existing,
        "interactions": interactions,
        "query_terms": query_terms[:12],
        "top_categories": [c for c, _ in category_counter.most_common(6)],
        "top_brands": [b for b, _ in brand_counter.most_common(6)],
        "preferred_price": preferred_price,
        "activity_score": _bound01(interactions / 20.0),
    }


def _dataset_user_weights(is_existing: bool) -> Dict[str, float]:
    if is_existing:
        return {"dataset": 0.70, "live": 0.30}
    return {"dataset": 0.40, "live": 0.60}


def _derive_reasons(item: Dict[str, Any], user_profile: Dict[str, Any], score_parts: Dict[str, float]) -> str:
    reasons: List[str] = []
    category = str(item.get("category", "")).lower()
    if category and category in set(user_profile.get("top_categories", [])):
        reasons.append("Matches your category affinity")
    if score_parts.get("semantic_similarity", 0.0) >= 0.72:
        reasons.append("Strong semantic similarity")
    if score_parts.get("rating_score", 0.0) >= 0.82:
        reasons.append("Highly rated product")
    if item.get("source") == "live_api":
        reasons.append("Live Amazon signal")
    if score_parts.get("price_affinity", 0.0) >= 0.8:
        reasons.append("Fits your price preference")
    return "; ".join(reasons[:3]) or "Balanced hybrid recommendation"


async def get_hybrid_recommendation_bundle(
    user_id: str,
    top_k: int = 12,
    country: str = "US",
) -> Dict[str, Any]:
    country = country.upper()
    top_k = max(6, min(24, top_k))

    user_profile = await _build_user_profile(user_id)
    query_terms = user_profile.get("query_terms") or []

    dataset_candidates = await get_recommendations_for_user(user_id=user_id, top_k=max(30, top_k * 3))
    dataset_map = {str(x.get("product_id")): x for x in dataset_candidates}

    live_snapshot = await _cache_live_products(country=country, user_keywords=query_terms, min_items=max(20, top_k * 2))
    live_items = live_snapshot.get("items", [])

    candidates: Dict[str, Dict[str, Any]] = {}
    for doc in dataset_candidates:
        pid = str(doc.get("product_id") or "")
        if pid:
            base_doc = {
                "product_id": pid,
                "title": doc.get("product_name") or doc.get("title") or "",
                "description": doc.get("description") or "",
                "brand": doc.get("brand") or "",
                "category": doc.get("category") or "general",
                "price": _safe_float(doc.get("price_value") or doc.get("price"), 0.0),
                "rating": _safe_float(doc.get("rating"), 0.0),
                "rating_count": str(doc.get("rating_count") or "0"),
                "stock": _safe_int(doc.get("stock"), 0),
                "thumbnail": doc.get("thumbnail") or "",
                "images": doc.get("images") or [],
                "tags": doc.get("tags") or [],
                "source": "dataset",
                "updated_at": datetime.now(timezone.utc),
            }
            candidates[pid] = base_doc

    for item in live_items:
        pid = str(item.get("product_id") or "")
        if not pid:
            continue
        candidates[pid] = item

    candidate_list = list(candidates.values())
    if not candidate_list:
        return {
            "user_id": user_id,
            "country": country,
            "summary": {
                "products_analyzed": 0,
                "ai_accuracy": 0.0,
                "live_product_count": 0,
                "last_update_time": datetime.now(timezone.utc).isoformat(),
                "fallback_chain": ["dataset_products", "dummyjson_backup"],
            },
            "weights": {
                "fusion": {"dataset": 0.60, "semantic": 0.20, "live": 0.20},
                "priority": _dataset_user_weights(False),
            },
            "sections": {
                "hybrid_recommendations": [],
                "new_products": [],
                "similar_products": [],
                "trending_ai_students": [],
                "ai_product_insights": [],
            },
        }

    query_context = " ".join(query_terms[:5]) or "popular products"
    query_vec = encode_texts([query_context])[0]

    candidate_texts = [
        " ".join(
            p
            for p in [
                str(item.get("title") or ""),
                str(item.get("description") or ""),
                str(item.get("category") or ""),
                str(item.get("brand") or ""),
                " ".join(str(t) for t in (item.get("tags") or [])),
            ]
            if p
        )
        for item in candidate_list
    ]
    candidate_vecs = encode_texts(candidate_texts)

    priority = _dataset_user_weights(user_profile.get("is_existing_user", False))

    fused: List[Dict[str, Any]] = []
    category_affinity = set(user_profile.get("top_categories") or [])
    preferred_price = _safe_float(user_profile.get("preferred_price"), 100.0)

    for idx, item in enumerate(candidate_list):
        pid = str(item.get("product_id") or "")
        semantic_similarity = float((query_vec * candidate_vecs[idx]).sum())
        semantic_similarity = _bound01((semantic_similarity + 1.0) / 2.0)

        dataset_score = _bound01(_safe_float(dataset_map.get(pid, {}).get("ai_match"), 45.0) / 100.0)

        rating_score = _bound01(_safe_float(item.get("rating"), 0.0) / 5.0)
        popularity_score = _bound01(
            max(
                _safe_float(item.get("popularity"), 0.0),
                _safe_int(item.get("rating_count"), 0) / 5000.0,
                _safe_int(item.get("stock"), 0) / 300.0,
            )
        )
        live_product_score = _bound01(0.55 * rating_score + 0.45 * popularity_score)

        base_fusion = 0.60 * dataset_score + 0.20 * semantic_similarity + 0.20 * live_product_score
        adaptive_signal = priority["dataset"] * dataset_score + priority["live"] * live_product_score
        recommendation_score = _bound01(0.70 * base_fusion + 0.30 * adaptive_signal)

        user_interest_match = 1.0 if str(item.get("category", "")).lower() in category_affinity else 0.55
        price_affinity = _get_price_affinity(_safe_float(item.get("price"), 0.0), preferred_price)

        ai_match = _bound01(
            0.35 * recommendation_score
            + 0.25 * semantic_similarity
            + 0.15 * user_interest_match
            + 0.10 * rating_score
            + 0.10 * popularity_score
            + 0.05 * price_affinity
        )

        score_parts = {
            "recommendation_score": recommendation_score,
            "semantic_similarity": semantic_similarity,
            "user_interest_match": user_interest_match,
            "rating_score": rating_score,
            "popularity_score": popularity_score,
            "price_affinity": price_affinity,
        }

        reasons = _derive_reasons(item, user_profile, score_parts)
        formatted = format_product(item, ai_match=round(ai_match * 100, 1), semantic_score=semantic_similarity)
        formatted.update(
            {
                "score_components": score_parts,
                "recommendation_score": round(recommendation_score * 100, 2),
                "ai_match_label": f"AI Match: {round(ai_match * 100)}%",
                "live_price_indicator": "LIVE" if item.get("source") == "live_api" else "DATASET",
                "why_recommended": reasons,
                "is_new_arrival": item.get("source") == "live_api",
            }
        )
        fused.append(formatted)

    fused.sort(key=lambda x: x.get("ai_match", 0.0), reverse=True)

    hybrid = fused[:top_k]
    new_products = [p for p in fused if p.get("live_price_indicator") == "LIVE"][: min(8, top_k)]

    similar_products = []
    if hybrid:
        anchor_query = f"{hybrid[0].get('title', '')} {hybrid[0].get('category', '')}".strip()
        from .search_service import semantic_search

        try:
            sim_result = await semantic_search(anchor_query or query_context, top_k=8)
            similar_products = sim_result.get("products", [])
        except Exception:
            similar_products = fused[1:9]

    # Trending among AI students (proxy through search-history + ratings/popularity)
    search_col = get_collection("search_history")
    recent_searches = await search_col.find({}, sort=[("timestamp", -1)], limit=300).to_list(length=300)
    trend_counter: Counter[str] = Counter()
    for row in recent_searches:
        q = str(row.get("query") or "").strip().lower()
        if q:
            trend_counter[q] += 1

    trending_pool = fused[:]
    for p in trending_pool:
        trend_signal = 0.0
        name_tokens = str(p.get("title") or "").lower().split()[:3]
        for t in name_tokens:
            trend_signal += trend_counter.get(t, 0)
        p["_trend_signal"] = trend_signal

    trending_ai_students = sorted(
        trending_pool,
        key=lambda p: (p.get("_trend_signal", 0.0), p.get("ai_match", 0.0), p.get("rating", 0.0)),
        reverse=True,
    )[: min(8, top_k)]

    ai_product_insights = []
    for p in hybrid[: min(6, top_k)]:
        rating = _safe_float(p.get("rating"), 0.0)
        price_val = _safe_float(p.get("price_value"), 0.0)
        pros = []
        cons = []
        if rating >= 4.2:
            pros.append("Consistently high customer ratings")
        if p.get("live_price_indicator") == "LIVE":
            pros.append("Fresh live marketplace signal")
        if p.get("score_components", {}).get("price_affinity", 0) >= 0.75:
            pros.append("Aligned with your price preference")
        if rating < 3.8:
            cons.append("Mixed customer sentiment")
        if _safe_int(p.get("stock"), 0) <= 0:
            cons.append("Potential stock constraints")
        if price_val > preferred_price * 1.4:
            cons.append("Price is above your usual spend")

        if not pros:
            pros = ["Balanced performance across recommendation signals"]
        if not cons:
            cons = ["No major risk indicators detected"]

        ai_product_insights.append(
            {
                "product_id": p.get("product_id"),
                "product_name": p.get("product_name"),
                "pros": pros[:3],
                "cons": cons[:3],
                "best_use_cases": [
                    f"Best for {str(p.get('category') or 'general shopping').replace('-', ' ')} buyers",
                    "High-confidence recommendation shortlist",
                ],
                "value_for_money_score": round(
                    100
                    * _bound01(
                        0.5 * _safe_float(p.get("score_components", {}).get("price_affinity"), 0.5)
                        + 0.5 * (_safe_float(p.get("rating"), 0.0) / 5.0)
                    ),
                    1,
                ),
                "recommendation_confidence": round(_safe_float(p.get("ai_match"), 0.0), 1),
            }
        )

    summary = {
        "products_analyzed": len(candidate_list),
        "ai_accuracy": round(sum(_safe_float(p.get("ai_match"), 0.0) for p in hybrid) / max(1, len(hybrid)), 2),
        "live_product_count": len([x for x in candidate_list if x.get("source") == "live_api"]),
        "last_update_time": datetime.now(timezone.utc).isoformat(),
        "fallback_chain": ["products_live", "products_dataset", "dummyjson_backup"],
        "live_cache_source": live_snapshot.get("source", "mongo_live_cache"),
        "live_cache_updates": live_snapshot.get("updated", 0),
    }

    await get_collection("recommendations").update_one(
        {"user_id": user_id, "kind": "hybrid_recommendation_bundle"},
        {
            "$set": {
                "user_id": user_id,
                "kind": "hybrid_recommendation_bundle",
                "country": country,
                "summary": summary,
                "recommendations": hybrid,
                "updated_at": datetime.now(timezone.utc),
            }
        },
        upsert=True,
    )

    return {
        "user_id": user_id,
        "country": country,
        "weights": {
            "fusion": {
                "dataset": 0.60,
                "semantic": 0.20,
                "live": 0.20,
            },
            "priority": priority,
        },
        "summary": summary,
        "sections": {
            "hybrid_recommendations": hybrid,
            "new_products": new_products,
            "similar_products": similar_products,
            "trending_ai_students": trending_ai_students,
            "ai_product_insights": ai_product_insights,
        },
    }


async def get_recommendations_for_product(
    product_id: str,
    top_k: int = 8,
) -> List[Dict[str, Any]]:
    products_col = get_collection("products")

    anchor = await products_col.find_one({"product_id": product_id})
    if not anchor:
        return []

    category = anchor.get("category", "")
    brand = anchor.get("brand", "")
    price = float(anchor.get("price", 0))

    cursor = products_col.find(
        {"product_id": {"$ne": product_id}, "category": category},
        limit=top_k * 4,
    )

    candidates: List[Dict[str, Any]] = []
    async for doc in cursor:
        brand_match = 1.0 if doc.get("brand") == brand else 0.5
        cat_match = 1.0
        price_match = _price_similarity(price, float(doc.get("price", 0)))
        rating_score = float(doc.get("rating", 0)) / 5.0
        stock_score = min(float(doc.get("stock", 0)) / 100.0, 1.0)

        raw_score = (
            0.3 * cat_match
            + 0.25 * brand_match
            + 0.25 * price_match
            + 0.1 * rating_score
            + 0.1 * stock_score
        )
        ai_match = round(raw_score * 100, 1)

        reason_parts = [f"Same category: {category}"]
        if brand_match == 1.0:
            reason_parts.append(f"Same brand: {brand}")
        if price_match > 0.8:
            reason_parts.append("Similar price range")
        if rating_score > 0.8:
            reason_parts.append("Highly rated")

        candidates.append({
            **format_product(doc, ai_match=ai_match),
            "reason": "; ".join(reason_parts),
        })

    candidates.sort(key=lambda x: x["ai_match"], reverse=True)
    return candidates[:top_k]


async def get_recommendations_for_user(
    user_id: str,
    top_k: int = 10,
) -> List[Dict[str, Any]]:
    """
    User-based recommendations from search history + trending fallback.
    """
    products_col = get_collection("products")
    history_col = get_collection("search_history")

    recent = await history_col.find(
        {"user_id": user_id} if user_id else {},
        sort=[("timestamp", -1)],
        limit=5,
    ).to_list(length=5)

    if recent:
        from .search_service import semantic_search

        all_recs: Dict[str, Dict[str, Any]] = {}
        for entry in recent:
            q = entry.get("query", "")
            if not q:
                continue
            search_result = await semantic_search(q, top_k=5)
            for prod in search_result["products"]:
                pid = prod["product_id"]
                if pid not in all_recs or prod["ai_match"] > all_recs[pid]["ai_match"]:
                    all_recs[pid] = {**prod, "reason": f"Based on your search: '{q}'"}

        ranked = sorted(all_recs.values(), key=lambda x: x["ai_match"], reverse=True)
        if ranked:
            return ranked[:top_k]

    cursor = products_col.find({}, sort=[("rating", -1), ("stock", -1)], limit=top_k)
    results = []
    async for doc in cursor:
        ai_match = compute_ai_match_score(doc, 0.7, "trending")
        results.append({
            **format_product(doc, ai_match=ai_match),
            "reason": "Trending product with high ratings",
        })
    return results


async def refresh_recommendations_cache(product_ids: Optional[List[str]] = None) -> Dict[str, Any]:
    """Pre-compute recommendations for recently ingested products."""
    recs_col = get_collection("recommendations")
    products_col = get_collection("products")

    if product_ids:
        query = {"product_id": {"$in": product_ids}}
    else:
        query = {}

    updated = 0
    cursor = products_col.find(query, {"product_id": 1})
    async for doc in cursor:
        pid = doc["product_id"]
        recs = await get_recommendations_for_product(pid, top_k=5)
        await recs_col.update_one(
            {"product_id": pid},
            {"$set": {
                "product_id": pid,
                "recommendations": recs,
                "updated_at": datetime.now(timezone.utc),
            }},
            upsert=True,
        )
        updated += 1

    return {"cached": updated}
