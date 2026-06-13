"""
ShopMind AI — APScheduler
Runs the full ingest → embed → FAISS → recommendations → RAG pipeline every 6 hours.
"""

import logging
import os
from pathlib import Path

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger(__name__)

INTERVAL_HOURS = int(os.getenv("PIPELINE_INTERVAL_HOURS", "6"))

scheduler = AsyncIOScheduler()


async def scheduled_pipeline():
    from services.pipeline import run_full_pipeline
    logger.info("⏰ Scheduled pipeline starting …")
    result = await run_full_pipeline()
    logger.info(f"⏰ Scheduled pipeline finished: {result.get('status')}")


def start_scheduler(run_on_startup: bool = False):
    scheduler.add_job(
        scheduled_pipeline,
        trigger=IntervalTrigger(hours=INTERVAL_HOURS),
        id="shopmind_pipeline",
        name="ShopMind Full Pipeline",
        replace_existing=True,
    )
    scheduler.start()
    logger.info(f"✓ Scheduler started — pipeline every {INTERVAL_HOURS}h")


def stop_scheduler():
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("Scheduler stopped")
