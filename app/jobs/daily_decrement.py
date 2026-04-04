"""Daily stock decrement job."""

import asyncio
import logging

from app.services.inventory_service import inventory_service

logger = logging.getLogger(__name__)


def run_daily_decrement() -> None:
    """Entry point called by APScheduler (sync wrapper for async logic)."""
    logger.info("Starting daily stock decrement job...")
    loop = asyncio.new_event_loop()
    try:
        count = loop.run_until_complete(inventory_service.daily_decrement_all())
        logger.info("Daily decrement job completed. Processed %d items.", count)
    except Exception as e:
        logger.exception("Daily decrement job failed: %s", e)
    finally:
        loop.close()
