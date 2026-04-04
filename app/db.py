"""MongoDB connection management using Motor async driver."""

import logging

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from app.config import settings

logger = logging.getLogger(__name__)

_client: AsyncIOMotorClient | None = None
_database: AsyncIOMotorDatabase | None = None


async def connect_db() -> None:
    """Initialize the MongoDB connection and create indexes."""
    global _client, _database
    _client = AsyncIOMotorClient(settings.mongodb_url)
    _database = _client[settings.mongodb_db_name]
    logger.info("Connected to MongoDB: %s", settings.mongodb_db_name)
    await create_indexes()


async def close_db() -> None:
    """Close the MongoDB connection."""
    global _client, _database
    if _client:
        _client.close()
        _client = None
        _database = None
        logger.info("MongoDB connection closed")


def get_database() -> AsyncIOMotorDatabase:
    """Return the active database instance."""
    if _database is None:
        raise RuntimeError("Database not initialized. Call connect_db() first.")
    return _database


async def create_indexes() -> None:
    """Create MongoDB indexes for hot queries."""
    db = get_database()

    # receipts indexes
    await db.receipts.create_index(
        [("userId", 1), ("transaction.purchasedAt", -1)]
    )

    # inventory_state indexes
    await db.inventory_state.create_index(
        [("userId", 1), ("canonicalItemId", 1)], unique=True
    )
    await db.inventory_state.create_index(
        [("userId", 1), ("status", 1)]
    )

    # inventory_events indexes
    await db.inventory_events.create_index(
        [("userId", 1), ("canonicalItemId", 1), ("createdAt", -1)]
    )

    # price_observations indexes
    await db.price_observations.create_index(
        [("userId", 1), ("canonicalItemId", 1), ("purchasedAt", -1)]
    )

    # price_insights indexes
    await db.price_insights.create_index(
        [("userId", 1), ("canonicalItemId", 1), ("window", 1)]
    )

    # users index
    await db.users.create_index([("email", 1)], unique=True)

    # notifications index
    await db.notifications.create_index(
        [("userId", 1), ("createdAt", -1)]
    )

    # linked_accounts index
    await db.linked_accounts.create_index(
        [("userId", 1), ("provider", 1)], unique=True
    )

    # email_expenses indexes
    await db.email_expenses.create_index(
        [("userId", 1), ("gmailMessageId", 1)], unique=True
    )
    await db.email_expenses.create_index(
        [("userId", 1), ("transactionAt", -1)]
    )
    await db.email_expenses.create_index(
        [("userId", 1), ("category", 1), ("transactionAt", -1)]
    )

    # email_sync_runs index
    await db.email_sync_runs.create_index(
        [("userId", 1), ("startedAt", -1)]
    )

    logger.info("MongoDB indexes created")
