"""Admin routes – destructive operations for testing/development."""

import logging

from fastapi import APIRouter, Query

from app.db import get_database
from app.utils.response import success_response

logger = logging.getLogger(__name__)

router = APIRouter()

# All collections in the system
ALL_COLLECTIONS = [
    "users",
    "receipts",
    "price_observations",
    "price_insights",
    "inventory_states",
    "inventory_events",
    "notifications",
    "linked_accounts",
    "email_expenses",
    "email_sync_runs",
]


@router.delete("/reset")
async def reset_all_data():
    """⚠️ DANGER: Delete ALL data from ALL collections. For development/testing only."""
    db = get_database()
    results = {}

    for col_name in ALL_COLLECTIONS:
        result = await db[col_name].delete_many({})
        results[col_name] = result.deleted_count

    total = sum(results.values())
    logger.warning("ADMIN RESET: Deleted %d documents across %d collections", total, len(ALL_COLLECTIONS))

    return success_response({
        "total_deleted": total,
        "collections": results,
    }, "All data deleted")


@router.delete("/users")
async def delete_all_users():
    """Delete all users only."""
    db = get_database()
    result = await db.users.delete_many({})
    logger.warning("ADMIN: Deleted %d users", result.deleted_count)
    return success_response({"deleted": result.deleted_count}, "All users deleted")


@router.delete("/users/{user_id}")
async def delete_user(user_id: str):
    """Delete a specific user and all their data across every collection."""
    db = get_database()
    results = {}

    for col_name in ALL_COLLECTIONS:
        result = await db[col_name].delete_many({"userId": user_id})
        results[col_name] = result.deleted_count

    # Users collection uses _id not userId
    from bson import ObjectId
    try:
        user_result = await db.users.delete_one({"_id": ObjectId(user_id)})
        results["users"] = user_result.deleted_count
    except Exception:
        pass

    total = sum(results.values())
    logger.warning("ADMIN: Deleted %d documents for user %s", total, user_id)

    return success_response({
        "user_id": user_id,
        "total_deleted": total,
        "collections": results,
    }, f"User {user_id} and all related data deleted")
