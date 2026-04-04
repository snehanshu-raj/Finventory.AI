"""Price repository – data access for `price_observations` and `price_insights`."""

from datetime import datetime, timedelta
from typing import Any, Optional

from bson import ObjectId

from app.db import get_database


class PriceRepository:
    """Async data access for price_observations and price_insights."""

    def _obs_col(self):
        return get_database().price_observations

    def _insights_col(self):
        return get_database().price_insights

    @staticmethod
    def _from_doc(doc: dict) -> dict:
        if doc and "_id" in doc:
            doc["_id"] = str(doc["_id"])
        return doc

    # ── price_observations ─────────────────────────────────────────────

    async def insert_observations(self, observations: list[dict]) -> int:
        """Bulk insert price observations, return count inserted."""
        if not observations:
            return 0
        result = await self._obs_col().insert_many(observations)
        return len(result.inserted_ids)

    async def delete_by_receipt(self, receipt_id: str) -> int:
        """Delete all observations for a receipt (used during correction)."""
        result = await self._obs_col().delete_many({"receiptId": receipt_id})
        return result.deleted_count

    async def find_by_item(
        self,
        user_id: str,
        canonical_item_id: str,
        window_days: int = 30,
    ) -> list[dict]:
        """Find observations for an item within a time window."""
        since = datetime.utcnow() - timedelta(days=window_days)
        cursor = self._obs_col().find(
            {
                "userId": user_id,
                "canonicalItemId": canonical_item_id,
                "purchasedAt": {"$gte": since},
            }
        ).sort("purchasedAt", -1)
        return [self._from_doc(doc) async for doc in cursor]

    async def aggregate_by_store(
        self,
        user_id: str,
        canonical_item_id: str,
        window_days: int = 30,
    ) -> list[dict]:
        """Aggregate average unit price by store for an item."""
        since = datetime.utcnow() - timedelta(days=window_days)
        pipeline = [
            {
                "$match": {
                    "userId": user_id,
                    "canonicalItemId": canonical_item_id,
                    "purchasedAt": {"$gte": since},
                    "unitPrice": {"$ne": None},
                }
            },
            {
                "$group": {
                    "_id": "$storeName",
                    "avgUnitPrice": {"$avg": "$unitPrice"},
                    "samples": {"$sum": 1},
                    "lastSeen": {"$max": "$purchasedAt"},
                }
            },
            {"$sort": {"avgUnitPrice": 1}},
        ]
        cursor = self._obs_col().aggregate(pipeline)
        return [doc async for doc in cursor]

    async def aggregate_expenses_by_store(
        self, user_id: str, since: datetime
    ) -> list[dict]:
        """Aggregate total spend by store."""
        pipeline = [
            {"$match": {"userId": user_id, "purchasedAt": {"$gte": since}}},
            {
                "$group": {
                    "_id": "$storeName",
                    "totalSpend": {"$sum": "$linePrice"},
                    "receiptIds": {"$addToSet": "$receiptId"},
                }
            },
            {"$sort": {"totalSpend": -1}},
        ]
        cursor = self._obs_col().aggregate(pipeline)
        return [doc async for doc in cursor]

    async def aggregate_expenses_by_category(
        self, user_id: str, since: datetime
    ) -> list[dict]:
        """Aggregate total spend by category."""
        pipeline = [
            {"$match": {"userId": user_id, "purchasedAt": {"$gte": since}}},
            {
                "$group": {
                    "_id": "$canonicalCategory",
                    "totalSpend": {"$sum": "$linePrice"},
                    "itemCount": {"$sum": 1},
                }
            },
            {"$sort": {"totalSpend": -1}},
        ]
        cursor = self._obs_col().aggregate(pipeline)
        return [doc async for doc in cursor]

    async def aggregate_top_items(
        self, user_id: str, since: datetime, limit: int = 10
    ) -> list[dict]:
        """Aggregate top-spend items."""
        pipeline = [
            {"$match": {"userId": user_id, "purchasedAt": {"$gte": since}}},
            {
                "$group": {
                    "_id": "$canonicalName",
                    "totalSpend": {"$sum": "$linePrice"},
                    "purchaseCount": {"$sum": 1},
                }
            },
            {"$sort": {"totalSpend": -1}},
            {"$limit": limit},
        ]
        cursor = self._obs_col().aggregate(pipeline)
        return [doc async for doc in cursor]

    async def total_spend_since(self, user_id: str, since: datetime) -> float:
        """Sum linePrice for a user since a given date."""
        pipeline = [
            {"$match": {"userId": user_id, "purchasedAt": {"$gte": since}}},
            {"$group": {"_id": None, "total": {"$sum": "$linePrice"}}},
        ]
        cursor = self._obs_col().aggregate(pipeline)
        result = [doc async for doc in cursor]
        return result[0]["total"] if result else 0.0

    async def aggregate_all_items_by_store(
        self, user_id: str, window_days: int = 30
    ) -> list[dict]:
        """Aggregate all items grouped by canonicalItemId then by store."""
        since = datetime.utcnow() - timedelta(days=window_days)
        pipeline = [
            {
                "$match": {
                    "userId": user_id,
                    "purchasedAt": {"$gte": since},
                    "unitPrice": {"$ne": None},
                }
            },
            {
                "$group": {
                    "_id": {
                        "item": "$canonicalItemId",
                        "itemName": "$canonicalName",
                        "store": "$storeName",
                    },
                    "avgUnitPrice": {"$avg": "$unitPrice"},
                    "samples": {"$sum": 1},
                    "lastSeen": {"$max": "$purchasedAt"},
                }
            },
            {"$sort": {"_id.item": 1, "avgUnitPrice": 1}},
        ]
        cursor = self._obs_col().aggregate(pipeline)
        return [doc async for doc in cursor]

    # ── price_insights ─────────────────────────────────────────────────

    async def upsert_insight(self, user_id: str, canonical_item_id: str, window: str, data: dict) -> dict:
        """Upsert a price insight document."""
        result = await self._insights_col().find_one_and_update(
            {"userId": user_id, "canonicalItemId": canonical_item_id, "window": window},
            {"$set": data},
            upsert=True,
            return_document=True,
        )
        return self._from_doc(result)

    async def find_insight(self, user_id: str, canonical_item_id: str, window: str = "30d") -> Optional[dict]:
        """Find a precomputed price insight."""
        doc = await self._insights_col().find_one(
            {"userId": user_id, "canonicalItemId": canonical_item_id, "window": window}
        )
        return self._from_doc(doc) if doc else None


price_repo = PriceRepository()
