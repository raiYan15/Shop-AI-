"""
ShopMind AI — Embedding Service
Encodes products with all-MiniLM-L6-v2, stores vectors in MongoDB, incrementally updates FAISS.
"""

import logging
import pickle
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.preprocessing import normalize

from .db import get_collection

logger = logging.getLogger(__name__)

EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
EMBEDDING_DIM = 384

DATA_DIR = Path(__file__).parent.parent.parent / "data"
FAISS_PATH = DATA_DIR / "faiss_live.idx"
ID_MAP_PATH = DATA_DIR / "id_map_live.pkl"

_model: Optional[SentenceTransformer] = None
_faiss_index: Optional[faiss.Index] = None
_id_map: List[str] = []


def get_embedding_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer(EMBEDDING_MODEL_NAME)
        logger.info(f"✓ Loaded embedding model: {EMBEDDING_MODEL_NAME}")
    return _model


def build_embedding_text(product: Dict[str, Any]) -> str:
    tags = product.get("tags") or []
    tag_str = ", ".join(str(t) for t in tags) if tags else ""
    parts = [
        product.get("title", ""),
        product.get("description", ""),
        product.get("brand", ""),
        product.get("category", ""),
        tag_str,
    ]
    return " ".join(p for p in parts if p).strip()


def _create_index() -> faiss.IndexFlatIP:
    return faiss.IndexFlatIP(EMBEDDING_DIM)


def load_faiss_index() -> Tuple[faiss.Index, List[str]]:
    """Load FAISS index and ID map from disk, or create fresh ones."""
    global _faiss_index, _id_map

    DATA_DIR.mkdir(parents=True, exist_ok=True)

    if FAISS_PATH.exists() and ID_MAP_PATH.exists():
        _faiss_index = faiss.read_index(str(FAISS_PATH))
        with open(ID_MAP_PATH, "rb") as f:
            _id_map = pickle.load(f)
        logger.info(f"✓ Loaded FAISS index: {_faiss_index.ntotal} vectors")
    else:
        _faiss_index = _create_index()
        _id_map = []
        logger.info("✓ Created new empty FAISS index")

    return _faiss_index, _id_map


def get_faiss_index() -> Tuple[faiss.Index, List[str]]:
    global _faiss_index, _id_map
    if _faiss_index is None:
        return load_faiss_index()
    return _faiss_index, _id_map


def persist_faiss_index() -> None:
    global _faiss_index, _id_map
    if _faiss_index is None:
        return
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    faiss.write_index(_faiss_index, str(FAISS_PATH))
    with open(ID_MAP_PATH, "wb") as f:
        pickle.dump(_id_map, f)
    logger.info(f"✓ Persisted FAISS index ({_faiss_index.ntotal} vectors)")


def encode_texts(texts: List[str]) -> np.ndarray:
    model = get_embedding_model()
    vectors = model.encode(texts, convert_to_numpy=True, show_progress_bar=False).astype("float32")
    return normalize(vectors)


async def embed_products(product_ids: List[str]) -> Dict[str, Any]:
    """
    Embed new/updated products and add them incrementally to FAISS.
    Skips products that already have embeddings unless forced via re-embed.
    """
    if not product_ids:
        return {"embedded": 0, "skipped": 0, "faiss_vectors": get_faiss_index()[0].ntotal}

    products_col = get_collection("products")
    embeddings_col = get_collection("product_embeddings")
    index, id_map = get_faiss_index()
    id_set = set(id_map)

    embedded = 0
    skipped = 0
    new_vectors: List[np.ndarray] = []
    new_ids: List[str] = []

    for pid in product_ids:
        existing = await embeddings_col.find_one({"product_id": pid})
        if existing and pid in id_set:
            skipped += 1
            continue

        doc = await products_col.find_one({"product_id": pid})
        if not doc:
            continue

        text = build_embedding_text(doc)
        vector = encode_texts([text])[0]

        await embeddings_col.update_one(
            {"product_id": pid},
            {
                "$set": {
                    "product_id": pid,
                    "embedding": vector.tolist(),
                    "model": EMBEDDING_MODEL_NAME,
                    "updated_at": datetime.now(timezone.utc),
                }
            },
            upsert=True,
        )

        if pid not in id_set:
            new_vectors.append(vector)
            new_ids.append(pid)
            id_set.add(pid)
            embedded += 1

    if new_vectors:
        batch = np.array(new_vectors, dtype="float32")
        index.add(batch)
        id_map.extend(new_ids)
        persist_faiss_index()

    return {
        "embedded": embedded,
        "skipped": skipped,
        "faiss_vectors": index.ntotal,
        "new_ids": new_ids,
    }


async def rebuild_faiss_from_mongodb() -> Dict[str, Any]:
    """Rebuild FAISS index from all stored embeddings (recovery path)."""
    global _faiss_index, _id_map

    embeddings_col = get_collection("product_embeddings")
    cursor = embeddings_col.find({}, {"product_id": 1, "embedding": 1})

    _faiss_index = _create_index()
    _id_map = []
    vectors = []

    async for doc in cursor:
        emb = doc.get("embedding")
        if not emb:
            continue
        vectors.append(np.array(emb, dtype="float32"))
        _id_map.append(doc["product_id"])

    if vectors:
        batch = normalize(np.array(vectors, dtype="float32"))
        _faiss_index.add(batch)

    persist_faiss_index()
    return {"faiss_vectors": _faiss_index.ntotal, "rebuilt": True}
