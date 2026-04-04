"""Weekly summary job (scaffold)."""

import asyncio
import logging
from datetime import datetime

from app.repositories.inventory_repository import inventory_repo
from app.repositories.notification_repository import notification_repo

logger = logging.getLogger(__name__)


async def _generate_weekly_summaries() -> int:
    """Generate weekly summary notifications for all users."""
    all_states = await inventory_repo.find_all_states_global()
    user_ids = list({s["userId"] for s in all_states})
    count = 0

    for user_id in user_ids:
        low_items = await inventory_repo.find_low_stock(user_id)
        low_names = [s.get("canonicalName", "") for s in low_items[:5]]

        message_parts = [f"Weekly Summary ({datetime.utcnow().strftime('%Y-%m-%d')})"]
        if low_names:
            message_parts.append(f"Low stock items: {', '.join(low_names)}")
        else:
            message_parts.append("All items well stocked!")

        await notification_repo.insert({
            "userId": user_id,
            "type": "weekly_summary",
            "title": "Weekly Pantry Summary",
            "message": ". ".join(message_parts),
            "status": "pending",
            "channel": "in_app",
            "context": {"lowStockCount": len(low_items)},
            "createdAt": datetime.utcnow(),
        })
        count += 1

    return count


def run_weekly_summary() -> None:
    """Entry point called by APScheduler."""
    logger.info("Starting weekly summary job...")
    loop = asyncio.new_event_loop()
    try:
        count = loop.run_until_complete(_generate_weekly_summaries())
        logger.info("Weekly summary job completed. Sent %d summaries.", count)
    except Exception as e:
        logger.exception("Weekly summary job failed: %s", e)
    finally:
        loop.close()
