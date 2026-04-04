"""Background job – poll Gmail for new expense emails."""

import asyncio
import logging

from app.repositories.gmail_repository import linked_account_repo
from app.services.gmail_sync_service import gmail_sync_service

logger = logging.getLogger(__name__)


def run_gmail_poll():
    """APScheduler entry point – sync all users with Gmail enabled."""
    loop = asyncio.new_event_loop()
    try:
        loop.run_until_complete(_poll_all_users())
    finally:
        loop.close()


async def _poll_all_users():
    """Find all sync-enabled accounts and trigger sync for each."""
    try:
        accounts = await linked_account_repo.find_all_sync_enabled()
        logger.info("Gmail poll: found %d accounts with sync enabled", len(accounts))

        for account in accounts:
            user_id = account.get("userId")
            try:
                result = await gmail_sync_service.sync_current_day(user_id)
                logger.info(
                    "Gmail poll for user %s: found=%d stored=%d",
                    user_id,
                    result.get("messages_found", 0),
                    result.get("messages_stored", 0),
                )
            except Exception as e:
                logger.error("Gmail poll failed for user %s: %s", user_id, e)

    except Exception as e:
        logger.exception("Gmail poll job failed: %s", e)
