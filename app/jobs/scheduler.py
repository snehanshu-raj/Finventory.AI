"""APScheduler setup and job registration."""

import logging

from apscheduler.schedulers.background import BackgroundScheduler

from app.jobs.daily_decrement import run_daily_decrement
from app.jobs.price_aggregation import run_price_aggregation
from app.jobs.weekly_summary import run_weekly_summary
from app.jobs.gmail_poll import run_gmail_poll
from app.config import settings

logger = logging.getLogger(__name__)

_scheduler: BackgroundScheduler | None = None


def start_scheduler() -> None:
    """Start the APScheduler background scheduler with all jobs."""
    global _scheduler
    _scheduler = BackgroundScheduler()

    # Daily stock decrement – runs every day at 2:00 AM
    _scheduler.add_job(
        run_daily_decrement,
        "cron",
        hour=2,
        minute=0,
        id="daily_decrement",
        replace_existing=True,
    )

    # Price insight aggregation – runs every day at 3:00 AM
    _scheduler.add_job(
        run_price_aggregation,
        "cron",
        hour=3,
        minute=0,
        id="price_aggregation",
        replace_existing=True,
    )

    # Weekly summary – runs every Monday at 8:00 AM
    _scheduler.add_job(
        run_weekly_summary,
        "cron",
        day_of_week="mon",
        hour=8,
        minute=0,
        id="weekly_summary",
        replace_existing=True,
    )

    # Gmail poll – runs every N hours (default: 6)
    _scheduler.add_job(
        run_gmail_poll,
        "interval",
        hours=settings.gmail_sync_interval_hours,
        id="gmail_poll",
        replace_existing=True,
    )

    _scheduler.start()
    logger.info(
        "Scheduler started with %d jobs",
        len(_scheduler.get_jobs()),
    )


def shutdown_scheduler() -> None:
    """Gracefully shut down the scheduler."""
    global _scheduler
    if _scheduler:
        _scheduler.shutdown(wait=False)
        _scheduler = None
        logger.info("Scheduler shut down")
