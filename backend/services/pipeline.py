"""
ShopMind AI — Full Pipeline Orchestrator
ingest → embed → FAISS → recommendations → market intel → RAG
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict

from .product_ingestion import run_ingestion_pipeline, is_circuit_open
from .embedding_service import embed_products, load_faiss_index
from .recommendation_service import refresh_recommendations_cache
from .market_intelligence import analyze_market_trends
from .rag_service import refresh_knowledge_base

logger = logging.getLogger(__name__)

_pipeline_status: Dict[str, Any] = {
    "last_run": None,
    "last_status": "idle",
    "last_error": None,
    "runs_completed": 0,
}


def get_pipeline_status() -> Dict[str, Any]:
    return {
        **_pipeline_status,
        "circuit_breaker_open": is_circuit_open(),
    }


async def run_full_pipeline() -> Dict[str, Any]:
    """Execute the complete auto-update pipeline."""
    global _pipeline_status

    if is_circuit_open():
        return {
            "status": "skipped",
            "reason": "Circuit breaker open — ingestion temporarily disabled",
        }

    started = datetime.now(timezone.utc)
    _pipeline_status["last_status"] = "running"

    try:
        load_faiss_index()

        ingest_result = await run_ingestion_pipeline()
        if ingest_result.get("status") == "error":
            raise RuntimeError(ingest_result.get("error", "Ingestion failed"))

        new_ids = ingest_result.get("new_ids", [])

        all_products_col = await _count_products()
        embed_ids = new_ids if new_ids else await _all_product_ids()

        embed_result = await embed_products(embed_ids)
        rec_result = await refresh_recommendations_cache(new_ids if new_ids else None)
        market_result = await analyze_market_trends()
        rag_result = await refresh_knowledge_base(new_ids if new_ids else None)

        finished = datetime.now(timezone.utc)
        summary = {
            "status": "success",
            "ingestion": ingest_result,
            "embedding": embed_result,
            "recommendations": rec_result,
            "market_trends": {
                "trending_categories": len(market_result.get("trending_categories", [])),
                "price_drops": len(market_result.get("price_drops", [])),
            },
            "rag": rag_result,
            "total_products": all_products_col,
            "started_at": started.isoformat(),
            "finished_at": finished.isoformat(),
            "duration_seconds": (finished - started).total_seconds(),
        }

        _pipeline_status.update({
            "last_run": finished.isoformat(),
            "last_status": "success",
            "last_error": None,
            "runs_completed": _pipeline_status["runs_completed"] + 1,
            "last_summary": summary,
        })

        logger.info(f"✓ Pipeline complete in {summary['duration_seconds']:.1f}s")
        return summary

    except Exception as exc:
        logger.error(f"Pipeline failed: {exc}")
        _pipeline_status.update({
            "last_run": datetime.now(timezone.utc).isoformat(),
            "last_status": "error",
            "last_error": str(exc),
        })
        return {"status": "error", "error": str(exc)}


async def _count_products() -> int:
    from .db import get_collection
    return await get_collection("products").count_documents({})


async def _all_product_ids() -> list:
    from .db import get_collection
    cursor = get_collection("products").find({}, {"product_id": 1})
    return [doc["product_id"] async for doc in cursor]
