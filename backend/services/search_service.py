"""
ShopMind AI — Retrieval Service
LLM-assisted query understanding + taxonomy-aware filtering + verified semantic retrieval.
"""

import json
import logging
import os
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Sequence, Tuple

import httpx
import numpy as np

from .db import get_collection

logger = logging.getLogger(__name__)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

SEARCH_WEIGHTS = {
    "category": 0.40,
    "brand": 0.25,
    "semantic": 0.20,
    "rating": 0.10,
    "popularity": 0.05,
}

MIN_RETRIEVAL_CONFIDENCE = 0.50

ATTRIBUTE_TERMS = [
    "gaming", "organic", "gentle", "oil free", "hydrating", "wireless", "bluetooth",
    "budget", "premium", "waterproof", "noise cancelling", "lightweight", "anti dandruff",
]

INR_TO_USD = float(os.getenv("INR_TO_USD", "0.012"))

TAXONOMY: Dict[str, Dict[str, Any]] = {
    "facewash": {
        "supercategory": "beauty",
        "aliases": ["facewash", "face wash", "facial cleanser", "cleanser"],
        "catalog_categories": ["skin-care", "beauty"],
        "required_terms": ["facewash", "face wash", "facial cleanser", "cleanser"],
        "include_any": ["facewash", "face wash", "facial cleanser"],
        "include_all_groups": [["face", "wash"], ["face", "cleanser"]],
        "exclude_any": ["body wash", "hand soap", "lipstick", "nail polish", "mascara", "eyeshadow", "tissue"],
        "strict": True,
    },
    "moisturizer": {
        "supercategory": "beauty",
        "aliases": ["moisturizer", "moisturiser", "face cream", "cream", "lotion"],
        "catalog_categories": ["skin-care", "beauty"],
        "required_terms": ["moisturizer", "moisturiser", "cream", "lotion"],
        "include_any": ["moisturizer", "moisturiser", "face cream"],
        "include_all_groups": [["face", "cream"]],
        "exclude_any": ["body wash", "hand soap", "coffee", "soft drinks"],
        "strict": True,
    },
    "serum": {
        "supercategory": "beauty",
        "aliases": ["serum", "face serum", "vitamin c serum"],
        "catalog_categories": ["skin-care", "beauty"],
        "required_terms": ["serum"],
        "include_any": ["serum", "face serum"],
        "exclude_any": ["soft drinks", "coffee", "tissue", "soap"],
        "strict": True,
    },
    "shampoo": {
        "supercategory": "beauty",
        "aliases": ["shampoo", "hair wash", "hair cleanser"],
        "catalog_categories": ["beauty"],
        "required_terms": ["shampoo"],
        "include_any": ["shampoo", "hair wash"],
        "exclude_any": ["facewash", "coffee", "soft drinks"],
        "strict": True,
    },
    "laptop": {
        "supercategory": "electronics",
        "aliases": ["laptop", "notebook", "ultrabook", "computer"],
        "catalog_categories": ["laptops"],
        "required_terms": ["laptop", "notebook", "ultrabook"],
        "include_any": ["laptop", "notebook", "ultrabook"],
        "exclude_any": ["phone", "shampoo", "facewash", "coffee", "tissue"],
        "strict": True,
    },
    "gaming laptop": {
        "supercategory": "electronics",
        "aliases": ["gaming laptop", "gaming notebook"],
        "catalog_categories": ["laptops"],
        "required_terms": ["gaming", "laptop"],
        "include_any": ["gaming laptop", "gaming notebook"],
        "include_all_groups": [["gaming", "laptop"], ["gaming", "notebook"]],
        "exclude_any": ["office chair", "coffee", "soap", "phone"],
        "strict": True,
    },
    "phone": {
        "supercategory": "electronics",
        "aliases": ["phone", "smartphone", "mobile phone", "mobile"],
        "catalog_categories": ["smartphones"],
        "required_terms": ["phone", "smartphone", "mobile"],
        "include_any": ["phone", "smartphone", "mobile"],
        "exclude_any": ["laptop", "facewash", "coffee"],
        "strict": True,
    },
    "headphones": {
        "supercategory": "electronics",
        "aliases": ["headphones", "headsets", "headset", "earbuds", "earphones"],
        "catalog_categories": ["mobile-accessories", "sports-accessories"],
        "required_terms": ["headphones", "headset", "earbuds", "earphones"],
        "include_any": ["headphones", "headset", "earbuds", "earphones"],
        "exclude_any": ["facewash", "coffee", "juice"],
        "strict": True,
    },
    "tablet": {
        "supercategory": "electronics",
        "aliases": ["tablet", "ipad", "tab"],
        "catalog_categories": ["tablets"],
        "required_terms": ["tablet", "ipad", "tab"],
        "include_any": ["tablet", "ipad", "tab"],
        "exclude_any": ["facewash", "coffee", "soap"],
        "strict": True,
    },
    "shoes": {
        "supercategory": "fashion",
        "aliases": ["shoes", "sneakers", "footwear", "running shoes"],
        "catalog_categories": ["mens-shoes", "womens-shoes"],
        "required_terms": ["shoes", "sneakers", "footwear"],
        "include_any": ["shoes", "sneakers", "footwear"],
        "exclude_any": ["coffee", "facewash", "soap"],
        "strict": True,
    },
    "shirt": {
        "supercategory": "fashion",
        "aliases": ["shirt", "t-shirt", "tee", "top"],
        "catalog_categories": ["mens-shirts", "tops"],
        "required_terms": ["shirt", "t-shirt", "tee", "top"],
        "include_any": ["shirt", "t-shirt", "tee", "top"],
        "exclude_any": ["coffee", "soap", "facewash"],
        "strict": True,
    },
    "bag": {
        "supercategory": "fashion",
        "aliases": ["bag", "handbag", "purse"],
        "catalog_categories": ["womens-bags"],
        "required_terms": ["bag", "handbag", "purse"],
        "include_any": ["bag", "handbag", "purse"],
        "exclude_any": ["coffee", "soap", "facewash"],
        "strict": True,
    },
    "watch": {
        "supercategory": "fashion",
        "aliases": ["watch", "watches", "timepiece"],
        "catalog_categories": ["mens-watches", "womens-watches"],
        "required_terms": ["watch", "watches", "timepiece"],
        "include_any": ["watch", "watches", "timepiece"],
        "exclude_any": ["coffee", "facewash", "soap"],
        "strict": True,
    },
    "groceries": {
        "supercategory": "grocery",
        "aliases": ["grocery", "groceries", "food", "beverage", "coffee", "juice", "snacks"],
        "catalog_categories": ["groceries"],
        "required_terms": ["grocery", "coffee", "juice", "snacks", "food"],
        "include_any": ["grocery", "groceries", "coffee", "juice", "snacks", "food", "beverage"],
        "strict": False,
    },
}

CATALOG_CATEGORY_ALIASES: Dict[str, List[str]] = {
    "beauty": ["beauty", "cosmetics", "makeup"],
    "skin-care": ["skin care", "skincare"],
    "laptops": ["laptops"],
    "smartphones": ["smartphones", "phones", "mobiles"],
    "tablets": ["tablets"],
    "groceries": ["groceries", "grocery"],
    "furniture": ["furniture", "bed", "sofa", "chair", "table"],
    "home-decoration": ["home decor", "decor"],
    "kitchen-accessories": ["kitchen", "cookware", "kitchen accessories"],
    "mens-shirts": ["mens shirts", "men shirts", "shirts"],
    "mens-shoes": ["mens shoes", "men shoes"],
    "womens-shoes": ["womens shoes", "women shoes"],
    "womens-bags": ["bags", "women bags", "handbags"],
    "mens-watches": ["mens watches", "men watches"],
    "womens-watches": ["womens watches", "women watches"],
    "mobile-accessories": ["mobile accessories", "chargers", "cases", "headphones", "earbuds"],
    "sports-accessories": ["sports accessories", "fitness accessories"],
}


def _normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9₹$&+\- ]+", " ", (value or "").lower())).strip()


def _normalize_score(value: float, lo: float = 0.0, hi: float = 1.0) -> float:
    if hi <= lo:
        return 0.0
    return max(0.0, min(1.0, (value - lo) / (hi - lo)))


def _tokenize(value: str) -> List[str]:
    return [token for token in _normalize_text(value).split() if token]


def _lexical_similarity(query: str, text: str) -> float:
    q_tokens = set(_tokenize(query))
    t_tokens = set(_tokenize(text))
    if not q_tokens or not t_tokens:
        return 0.0
    overlap = len(q_tokens & t_tokens)
    coverage = overlap / max(1, len(q_tokens))
    jaccard = overlap / max(1, len(q_tokens | t_tokens))
    return round(min(1.0, 0.7 * coverage + 0.3 * jaccard), 4)


def _safe_build_embedding_text(product: Dict[str, Any]) -> str:
    try:
        from .embedding_service import build_embedding_text as _build_embedding_text

        return _build_embedding_text(product)
    except Exception:
        parts = [
            str(product.get("title", "")),
            str(product.get("description", "")),
            str(product.get("brand", "")),
            str(product.get("category", "")),
            " ".join(str(t) for t in (product.get("tags") or [])),
        ]
        return " ".join(p for p in parts if p).strip()


def _safe_encode_texts(texts: List[str]) -> Optional[np.ndarray]:
    try:
        from .embedding_service import encode_texts as _encode_texts

        return _encode_texts(texts)
    except Exception as exc:
        logger.warning("Embedding encode unavailable, using lexical fallback: %s", str(exc)[:180])
        return None


def _extract_price_constraints(query: str) -> Tuple[Optional[float], Optional[float]]:
    text = _normalize_text(query).replace(",", "")
    between = re.search(r"between\s*[₹$]?\s*(\d+(?:\.\d+)?)\s*(?:and|to|-)\s*[₹$]?\s*(\d+(?:\.\d+)?)", text)
    if between:
        low = float(between.group(1))
        high = float(between.group(2))
        return (min(low, high), max(low, high))

    max_match = re.search(r"(?:under|below|max|upto|up to|less than)\s*[₹$]?\s*(\d+(?:\.\d+)?)", text)
    min_match = re.search(r"(?:above|over|more than|min)\s*[₹$]?\s*(\d+(?:\.\d+)?)", text)
    min_price = float(min_match.group(1)) if min_match else None
    max_price = float(max_match.group(1)) if max_match else None
    return min_price, max_price


def _normalize_budget_for_catalog(query: str, min_price: Optional[float], max_price: Optional[float]) -> Tuple[Optional[float], Optional[float]]:
    q = _normalize_text(query)
    uses_inr = "₹" in query or "inr" in q or "rs" in q
    if not uses_inr:
        return min_price, max_price

    def _convert(v: Optional[float]) -> Optional[float]:
        if v is None:
            return None
        if v > 1000:
            return round(v * INR_TO_USD, 2)
        return round(v, 2)

    return _convert(min_price), _convert(max_price)


async def _load_known_brands() -> List[str]:
    try:
        brands = await get_collection("products").distinct("brand")
        return sorted([str(b).strip() for b in brands if str(b).strip()], key=len, reverse=True)
    except Exception as exc:
        logger.warning("Unable to load brands for query understanding: %s", str(exc)[:120])
        return []


def _find_matching_brand(query: str, brands: Sequence[str]) -> Optional[str]:
    q = _normalize_text(query)
    for brand in brands:
        brand_norm = _normalize_text(brand)
        if brand_norm and brand_norm in q:
            return brand
    return None


def _infer_explicit_brand_token(query: str, category: Optional[str]) -> Optional[str]:
    q = _normalize_text(query)
    if not q:
        return None

    stop = {
        "best", "products", "product", "under", "below", "above", "with", "for", "and",
        "price", "range", "gaming", "laptop", "phone", "headphones", "facewash", "face", "wash",
    }
    if category:
        stop.add(_normalize_text(category))

    m = re.search(r"^([a-z0-9][a-z0-9&\-]{2,})\s+products?\b", q)
    if m:
        token = m.group(1).strip()
        if token and token not in stop:
            return token

    # Do not infer brand from general singleton tokens; this causes false filters
    # for queries like "laptop for programming" or "wireless headphones".
    return None


def _infer_category_from_query(query: str) -> Tuple[Optional[str], float]:
    q = _normalize_text(query)
    best: Optional[str] = None
    best_score = 0.0

    for canonical, spec in TAXONOMY.items():
        for alias in spec["aliases"]:
            alias_norm = _normalize_text(alias)
            if alias_norm and alias_norm in q:
                score = min(1.0, 0.65 + len(alias_norm) / 40)
                if score > best_score:
                    best = canonical
                    best_score = score

    if best:
        return best, best_score

    for catalog_category, aliases in CATALOG_CATEGORY_ALIASES.items():
        for alias in aliases:
            alias_norm = _normalize_text(alias)
            if alias_norm and alias_norm in q:
                return catalog_category, 0.7

    return None, 0.0


def _extract_attributes(query: str, brand: Optional[str], category: Optional[str]) -> List[str]:
    q = _normalize_text(query)
    attrs = [term for term in ATTRIBUTE_TERMS if term in q]
    skip_terms = {_normalize_text(brand or ""), _normalize_text(category or "")}
    words = [w for w in q.split() if len(w) > 2 and w not in skip_terms]
    for word in words:
        if word not in attrs and word not in {"best", "products", "under", "with", "for", "and"}:
            if word in {"gaming", "wireless", "organic", "gentle", "hydrating", "budget", "premium"}:
                attrs.append(word)
    return attrs[:8]


async def _classify_query_with_gemini(query: str, known_brands: Sequence[str]) -> Dict[str, Any]:
    if not GEMINI_API_KEY:
        return {}

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"
    prompt = (
        "Classify this shopping query into strict JSON only.\n"
        "Return keys: intent, category, brand, product_type, min_price, max_price, attributes, category_confidence.\n"
        "Rules: if brand/category unknown return null; category should be a product category like facewash, laptop, phone.\n"
        f"Known brands sample: {', '.join(list(known_brands)[:80])}\n"
        f"Query: {query}"
    )
    body = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.0, "maxOutputTokens": 250, "responseMimeType": "application/json"},
    }
    headers = {"x-goog-api-key": GEMINI_API_KEY, "Content-Type": "application/json"}
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            res = await client.post(url, headers=headers, json=body)
        res.raise_for_status()
        data = res.json()
        candidates = data.get("candidates") or []
        parts = candidates[0].get("content", {}).get("parts", []) if candidates else []
        text = "\n".join(str(p.get("text", "")) for p in parts if p.get("text"))
        if not text.strip():
            return {}
        match = re.search(r"\{.*\}", text, re.DOTALL)
        parsed = json.loads(match.group(0) if match else text)
        return parsed if isinstance(parsed, dict) else {}
    except Exception as exc:
        logger.warning("Gemini query classification failed: %s", str(exc)[:180])
        return {}


async def understand_query(query: str) -> Dict[str, Any]:
    known_brands = await _load_known_brands()
    brand = _find_matching_brand(query, known_brands)
    category, category_conf = _infer_category_from_query(query)
    min_price, max_price = _extract_price_constraints(query)
    min_price, max_price = _normalize_budget_for_catalog(query, min_price, max_price)
    llm = await _classify_query_with_gemini(query, known_brands)

    llm_category = llm.get("category") if isinstance(llm.get("category"), str) else None
    if not category and llm_category:
        inferred, inferred_conf = _infer_category_from_query(llm_category)
        category = inferred or _normalize_text(llm_category)
        category_conf = max(category_conf, inferred_conf or float(llm.get("category_confidence", 0.0) or 0.0))

    if not brand and isinstance(llm.get("brand"), str) and llm.get("brand"):
        brand = str(llm.get("brand")).strip()

    if not brand:
        brand = _infer_explicit_brand_token(query, category)

    if min_price is None and llm.get("min_price") not in (None, ""):
        try:
            min_price = float(llm.get("min_price"))
        except Exception:
            pass
    if max_price is None and llm.get("max_price") not in (None, ""):
        try:
            max_price = float(llm.get("max_price"))
        except Exception:
            pass

    intent = "product_search"
    q = _normalize_text(query)
    if "compare" in q or " vs " in q:
        intent = "compare"
    elif any(x in q for x in ["recommend", "best", "top", "suggest"]):
        intent = "product_search"
    if isinstance(llm.get("intent"), str) and llm.get("intent"):
        intent = _normalize_text(str(llm.get("intent"))).replace(" ", "_")

    attributes = _extract_attributes(query, brand, category)
    llm_attrs = llm.get("attributes") if isinstance(llm.get("attributes"), list) else []
    for attr in llm_attrs:
        if isinstance(attr, str) and attr.strip() and attr.strip() not in attributes:
            attributes.append(attr.strip())

    taxonomy_spec = TAXONOMY.get(category or "", None)
    allowed_categories = list(taxonomy_spec.get("catalog_categories", [])) if taxonomy_spec else []
    if not allowed_categories and category in CATALOG_CATEGORY_ALIASES:
        allowed_categories = [str(category)]

    product_type = category or (str(llm.get("product_type")) if llm.get("product_type") else None)

    return {
        "query": query,
        "intent": intent,
        "category": category,
        "brand": brand,
        "min_price": min_price,
        "max_price": max_price,
        "product_type": product_type,
        "attributes": attributes[:8],
        "category_confidence": round(max(category_conf, float(llm.get("category_confidence", 0.0) or 0.0)), 3),
        "allowed_catalog_categories": allowed_categories,
        "llm_classification": llm,
    }


def _product_text(doc: Dict[str, Any]) -> str:
    return _normalize_text(
        " ".join(
            [
                str(doc.get("title", "")),
                str(doc.get("description", "")),
                str(doc.get("brand", "")),
                str(doc.get("category", "")),
                " ".join(str(t) for t in (doc.get("tags") or [])),
            ]
        )
    )


def _product_category_signals(doc: Dict[str, Any]) -> List[str]:
    text = _product_text(doc)
    matches: List[str] = []
    for canonical, spec in TAXONOMY.items():
        required_terms = [_normalize_text(x) for x in spec.get("required_terms", [])]
        if required_terms and all(term in text for term in required_terms if term in {"gaming", "laptop"}):
            if canonical not in matches:
                matches.append(canonical)
            continue
        if any(term in text for term in required_terms):
            matches.append(canonical)
    catalog_category = str(doc.get("category", "")).strip().lower()
    if catalog_category and catalog_category not in matches:
        matches.append(catalog_category)
    return matches


def _category_relevance_score(doc: Dict[str, Any], understanding: Dict[str, Any]) -> float:
    requested = understanding.get("category")
    if not requested:
        return 1.0

    spec = TAXONOMY.get(str(requested), {})
    text = _product_text(doc)
    doc_category = str(doc.get("category", "")).strip().lower()
    allowed_categories = set(understanding.get("allowed_catalog_categories") or [])

    include_any = [_normalize_text(x) for x in spec.get("include_any", [])]
    include_all_groups = [[_normalize_text(y) for y in group] for group in spec.get("include_all_groups", [])]
    exclude_any = [_normalize_text(x) for x in spec.get("exclude_any", [])]
    strict = bool(spec.get("strict", False))

    if any(term and term in text for term in exclude_any):
        return 0.0

    any_hit = any(term and term in text for term in include_any) if include_any else False
    all_group_hit = any(all(term in text for term in group if term) for group in include_all_groups) if include_all_groups else False
    cat_hit = doc_category == requested or doc_category in allowed_categories

    if strict:
        if any_hit or all_group_hit:
            return 1.0
        if cat_hit:
            return 0.25
        return 0.0

    if any_hit or all_group_hit:
        return 1.0
    if cat_hit:
        return 0.75
    return 0.0


def _verify_product(doc: Dict[str, Any], understanding: Dict[str, Any]) -> bool:
    brand = understanding.get("brand")
    min_price = understanding.get("min_price")
    max_price = understanding.get("max_price")
    category = understanding.get("category")
    category_conf = float(understanding.get("category_confidence", 0.0) or 0.0)

    doc_brand = str(doc.get("brand", "")).strip().lower()
    doc_price = float(doc.get("price", 0) or 0)
    category_score = _category_relevance_score(doc, understanding)

    if brand and _normalize_text(str(brand)) != doc_brand:
        return False
    if min_price is not None and doc_price < float(min_price):
        return False
    if max_price is not None and doc_price > float(max_price):
        return False
    if int(doc.get("stock", 0) or 0) <= 0:
        return False
    if category:
        if category_conf >= 0.35 and category_score < 0.6:
            return False
    return True


def _category_match_score(doc: Dict[str, Any], understanding: Dict[str, Any]) -> float:
    return _category_relevance_score(doc, understanding)


def _brand_match_score(doc: Dict[str, Any], understanding: Dict[str, Any]) -> float:
    requested = understanding.get("brand")
    if not requested:
        return 1.0
    doc_brand = str(doc.get("brand", "")).strip().lower()
    return 1.0 if doc_brand == _normalize_text(str(requested)) else 0.0


def _popularity_score(doc: Dict[str, Any]) -> float:
    stock = float(doc.get("stock", 0) or 0)
    rating_count = float(doc.get("rating_count", 0) or doc.get("stock", 0) or 0)
    return max(_normalize_score(stock, 0, 100), _normalize_score(rating_count, 0, 500))


def format_product(
    product: Dict[str, Any],
    ai_match: float = 0.0,
    semantic_score: float = 0.0,
    why_recommended: str = "",
    category_match_score: float = 0.0,
    brand_match_score: float = 0.0,
    retrieval_confidence: float = 0.0,
) -> Dict[str, Any]:
    price = float(product.get("price", 0) or 0)
    discount = float(product.get("discount", 0) or 0)
    original = price / (1 - discount / 100) if discount > 0 else price
    return {
        "product_id": product.get("product_id"),
        "product_name": product.get("title", ""),
        "title": product.get("title", ""),
        "description": product.get("description", ""),
        "brand": product.get("brand", ""),
        "category": product.get("category", ""),
        "price": f"${price:.2f}",
        "price_value": price,
        "original_price": f"${original:.2f}",
        "rating": float(product.get("rating", 0) or 0),
        "rating_count": str(product.get("rating_count", product.get("stock", 0))),
        "stock": int(product.get("stock", 0) or 0),
        "thumbnail": product.get("thumbnail", ""),
        "images": product.get("images", []),
        "tags": product.get("tags", []),
        "source": product.get("source", ""),
        "ai_match": round(ai_match, 1),
        "similarity_score": round(semantic_score, 4),
        "semantic_match_percent": round(max(0.0, semantic_score) * 100, 1),
        "category_match_percent": round(max(0.0, category_match_score) * 100, 1),
        "brand_match_percent": round(max(0.0, brand_match_score) * 100, 1),
        "retrieval_confidence": round(retrieval_confidence, 1),
        "why_recommended": why_recommended,
    }


async def _fetch_candidate_documents(understanding: Dict[str, Any]) -> List[Dict[str, Any]]:
    products_col = get_collection("products")
    mongo_query: Dict[str, Any] = {"stock": {"$gt": 0}}

    brand = understanding.get("brand")
    if brand:
        mongo_query["brand"] = {"$regex": f"^{re.escape(str(brand).strip())}$", "$options": "i"}

    allowed_categories = understanding.get("allowed_catalog_categories") or []
    if allowed_categories:
        mongo_query["category"] = {"$in": allowed_categories}

    max_price = understanding.get("max_price")
    min_price = understanding.get("min_price")
    if max_price is not None or min_price is not None:
        price_filter: Dict[str, Any] = {}
        if min_price is not None:
            price_filter["$gte"] = float(min_price)
        if max_price is not None:
            price_filter["$lte"] = float(max_price)
        mongo_query["price"] = price_filter

    docs = await products_col.find(mongo_query).limit(400).to_list(length=400)

    requested_category = understanding.get("category")
    if requested_category and requested_category in TAXONOMY:
        spec = TAXONOMY.get(requested_category, {})
        include_any = [_normalize_text(x) for x in spec.get("include_any", [])]
        include_all_groups = [[_normalize_text(y) for y in g] for g in spec.get("include_all_groups", [])]

        narrowed: List[Dict[str, Any]] = []
        for doc in docs:
            text = _product_text(doc)
            any_hit = any(term and term in text for term in include_any) if include_any else False
            all_hit = any(all(term in text for term in group if term) for group in include_all_groups) if include_all_groups else False
            if any_hit or all_hit or not spec.get("strict", False):
                narrowed.append(doc)
        if narrowed:
            docs = narrowed

    verified = [doc for doc in docs if _verify_product(doc, understanding)]
    return verified


def compute_ai_match_score(doc: Dict[str, Any], semantic_similarity: float = 0.7, reason: str = "") -> float:
    rating_score = _normalize_score(float(doc.get("rating", 0) or 0), 0, 5)
    popularity_score = _popularity_score(doc)
    heuristic = 0.65 * _bound01(semantic_similarity) + 0.20 * rating_score + 0.15 * popularity_score
    if reason and "trending" in reason.lower():
        heuristic = max(heuristic, 0.58)
    return round(_bound01(heuristic) * 100, 1)


async def _semantic_similarity_over_subset(query: str, docs: Sequence[Dict[str, Any]]) -> Dict[str, float]:
    if not docs:
        return {}

    query_vectors = _safe_encode_texts([query])
    if query_vectors is None:
        return {
            str(doc.get("product_id")): _lexical_similarity(query, _safe_build_embedding_text(doc))
            for doc in docs
        }

    embeddings_col = get_collection("product_embeddings")
    query_vec = query_vectors[0]
    pid_list = [str(doc.get("product_id")) for doc in docs if doc.get("product_id")]
    stored = await embeddings_col.find({"product_id": {"$in": pid_list}}).to_list(length=len(pid_list))
    stored_map = {str(doc.get("product_id")): np.array(doc.get("embedding", []), dtype="float32") for doc in stored if doc.get("embedding")}

    missing_docs = [doc for doc in docs if str(doc.get("product_id")) not in stored_map]
    if missing_docs:
        texts = [_safe_build_embedding_text(doc) for doc in missing_docs]
        vecs = _safe_encode_texts(texts)
        if vecs is not None:
            for doc, vec in zip(missing_docs, vecs):
                stored_map[str(doc.get("product_id"))] = vec

    similarities: Dict[str, float] = {}
    for doc in docs:
        pid = str(doc.get("product_id"))
        vec = stored_map.get(pid)
        if vec is None or vec.size == 0:
            similarities[pid] = _lexical_similarity(query, _safe_build_embedding_text(doc))
            continue
        score = float(np.dot(query_vec, vec))
        similarities[pid] = max(0.0, min(1.0, score))
    return similarities


def _build_reason(doc: Dict[str, Any], understanding: Dict[str, Any], category_score: float, brand_score: float, semantic: float) -> str:
    reasons: List[str] = []
    if category_score >= 0.95 and understanding.get("category"):
        reasons.append(f"Category match: {understanding['category']}")
    if brand_score >= 0.95 and understanding.get("brand"):
        reasons.append(f"Brand match: {understanding['brand']}")
    if understanding.get("max_price") is not None:
        reasons.append(f"Within budget under {understanding['max_price']}")
    if semantic >= 0.65:
        reasons.append("Strong semantic relevance")
    elif semantic >= 0.45:
        reasons.append("Moderate semantic relevance")
    if float(doc.get("rating", 0) or 0) >= 4.5:
        reasons.append("Highly rated")
    return "; ".join(reasons) if reasons else "Best verified match after category, brand, and semantic checks"


async def semantic_search(
    query: str,
    top_k: int = 10,
    category: Optional[str] = None,
) -> Dict[str, Any]:
    top_k = max(1, min(top_k, 50))
    understanding = await understand_query(query)

    if category:
        understanding["category"] = _normalize_text(category)
        understanding["allowed_catalog_categories"] = TAXONOMY.get(understanding["category"], {}).get("catalog_categories", [understanding["category"]])
        understanding["category_confidence"] = max(float(understanding.get("category_confidence", 0.0) or 0.0), 0.85)

    candidates = await _fetch_candidate_documents(understanding)
    if not candidates:
        await get_collection("search_history").insert_one({
            "query": query,
            "result_count": 0,
            "timestamp": datetime.now(timezone.utc),
            "query_understanding": understanding,
            "retrieval_confidence": 0.0,
        })
        return {
            "query": query,
            "products": [],
            "similarity_scores": [],
            "count": 0,
            "confidence": 0.0,
            "understanding": understanding,
            "message": "I could not find matching products.",
        }

    similarities = await _semantic_similarity_over_subset(query, candidates)

    ranked: List[Tuple[float, Dict[str, Any], float, float, float]] = []
    for doc in candidates:
        pid = str(doc.get("product_id"))
        semantic = float(similarities.get(pid, 0.0))
        category_score = _category_match_score(doc, understanding)
        brand_score = _brand_match_score(doc, understanding)
        rating_score = _normalize_score(float(doc.get("rating", 0) or 0), 0, 5)
        popularity = _popularity_score(doc)

        final_score = (
            SEARCH_WEIGHTS["category"] * category_score
            + SEARCH_WEIGHTS["brand"] * brand_score
            + SEARCH_WEIGHTS["semantic"] * semantic
            + SEARCH_WEIGHTS["rating"] * rating_score
            + SEARCH_WEIGHTS["popularity"] * popularity
        )
        ranked.append((final_score, doc, semantic, category_score, brand_score))

    ranked.sort(key=lambda x: x[0], reverse=True)

    results: List[Dict[str, Any]] = []
    raw_scores: List[float] = []
    for final_score, doc, semantic, category_score, brand_score in ranked:
        if understanding.get("category") and category_score <= 0.05:
            continue
        if understanding.get("brand") and brand_score <= 0.0:
            continue
        if not _verify_product(doc, understanding):
            continue
        retrieval_confidence = round(final_score * 100, 1)
        reason = _build_reason(doc, understanding, category_score, brand_score, semantic)
        results.append(
            format_product(
                doc,
                ai_match=retrieval_confidence,
                semantic_score=semantic,
                why_recommended=reason,
                category_match_score=category_score,
                brand_match_score=brand_score,
                retrieval_confidence=retrieval_confidence,
            )
        )
        raw_scores.append(semantic)
        if len(results) >= top_k:
            break

    top_confidence = max((float(r.get("retrieval_confidence", 0.0)) for r in results), default=0.0)
    overall_conf = round(top_confidence / 100, 4)

    if understanding.get("brand"):
        # With explicit brand intent, enforce near-zero tolerance for off-brand retrieval.
        if top_confidence < 70:
            results = []
            raw_scores = []
            overall_conf = min(overall_conf, 0.49)

    if overall_conf < MIN_RETRIEVAL_CONFIDENCE:
        results = []
        raw_scores = []

    await get_collection("search_history").insert_one({
        "query": query,
        "result_count": len(results),
        "timestamp": datetime.now(timezone.utc),
        "query_understanding": understanding,
        "retrieval_confidence": round(overall_conf * 100, 1),
        "top_product_ids": [r.get("product_id") for r in results[:10]],
    })

    return {
        "query": query,
        "products": results,
        "similarity_scores": raw_scores,
        "count": len(results),
        "confidence": round(overall_conf * 100, 1),
        "understanding": understanding,
        "message": "I could not find matching products." if not results else "ok",
    }
