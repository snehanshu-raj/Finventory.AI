"""Inventory repository – data access for `inventory_state` and `inventory_events`."""

from datetime import datetime
from typing import Any, Optional

from bson import ObjectId

from app.db import get_database


class InventoryRepository:
    """Async data access for inventory_state and inventory_events collections."""

    # ── inventory_state helpers ────────────────────────────────────────

    def _state_col(self):
        return get_database().inventory_state

    def _events_col(self):
        return get_database().inventory_events

    @staticmethod
    def _from_doc(doc: dict) -> dict:
        if doc and "_id" in doc:
            doc["_id"] = str(doc["_id"])
        return doc

    # ── inventory_state CRUD ───────────────────────────────────────────

    async def upsert_state(self, user_id: str, canonical_item_id: str, data: dict) -> dict:
        """Upsert an inventory state document for a user-item pair."""
        data["lastUpdatedAt"] = datetime.utcnow()
        result = await self._state_col().find_one_and_update(
            {"userId": user_id, "canonicalItemId": canonical_item_id},
            {"$set": data},
            upsert=True,
            return_document=True,
        )
        return self._from_doc(result)

    async def find_state(self, user_id: str, canonical_item_id: str) -> Optional[dict]:
        """Get a single inventory state doc."""
        doc = await self._state_col().find_one(
            {"userId": user_id, "canonicalItemId": canonical_item_id}
        )
        return self._from_doc(doc) if doc else None

    async def find_all_states(
        self,
        user_id: str,
        status: Optional[str] = None,
        category: Optional[str] = None,
        sort_by: Optional[str] = None,
    ) -> list[dict]:
        """List all inventory items for a user with optional filters."""
        query: dict[str, Any] = {"userId": user_id}
        if status:
            query["status"] = status
        if category:
            query["category"] = category

        sort_field = {
            "estimatedDaysLeft": "estimatedDaysLeft",
            "currentQuantity": "currentQuantity",
            "name": "canonicalName",
        }.get(sort_by or "", "canonicalName")

        cursor = self._state_col().find(query).sort(sort_field, 1)
        return [self._from_doc(doc) async for doc in cursor]

    async def find_low_stock(self, user_id: str) -> list[dict]:
        """Return items where status is low, critical, or out_of_stock."""
        cursor = self._state_col().find(
            {"userId": user_id, "status": {"$in": ["low", "critical", "out_of_stock"]}}
        )
        return [self._from_doc(doc) async for doc in cursor]

    async def find_all_states_global(self) -> list[dict]:
        """Fetch all inventory states across all users (for daily job)."""
        cursor = self._state_col().find({})
        return [self._from_doc(doc) async for doc in cursor]

    async def update_state(self, user_id: str, canonical_item_id: str, update: dict) -> Optional[dict]:
        """Partial update of an inventory state document."""
        update["lastUpdatedAt"] = datetime.utcnow()
        result = await self._state_col().find_one_and_update(
            {"userId": user_id, "canonicalItemId": canonical_item_id},
            {"$set": update},
            return_document=True,
        )
        return self._from_doc(result) if result else None

    async def increment_quantity(self, user_id: str, canonical_item_id: str, delta: float) -> Optional[dict]:
        """Atomically increment currentQuantity (can be negative for decrement)."""
        result = await self._state_col().find_one_and_update(
            {"userId": user_id, "canonicalItemId": canonical_item_id},
            {
                "$inc": {"currentQuantity": delta},
                "$set": {"lastUpdatedAt": datetime.utcnow()},
            },
            return_document=True,
        )
        return self._from_doc(result) if result else None

    # ── inventory_events CRUD ──────────────────────────────────────────

    async def insert_event(self, data: dict) -> str:
        """Insert an inventory event and return its id."""
        result = await self._events_col().insert_one(data)
        return str(result.inserted_id)

    async def find_events(
        self,
        user_id: str,
        canonical_item_id: str,
        limit: int = 20,
    ) -> list[dict]:
        """Return recent events for a user-item pair."""
        cursor = (
            self._events_col()
            .find({"userId": user_id, "canonicalItemId": canonical_item_id})
            .sort("createdAt", -1)
            .limit(limit)
        )
        return [self._from_doc(doc) async for doc in cursor]

    async def delete_events_by_receipt(self, receipt_id: str) -> int:
        """Delete all events linked to a specific receipt (for correction replay)."""
        result = await self._events_col().delete_many(
            {"source.referenceId": receipt_id}
        )
        return result.deleted_count

    # ── Reset / delete all ─────────────────────────────────────────────

    async def delete_all_by_user(self, user_id: str) -> dict:
        """Delete all inventory states and events for a user. Returns counts."""
        states_result = await self._state_col().delete_many({"userId": user_id})
        events_result = await self._events_col().delete_many({"userId": user_id})
        return {
            "states_deleted": states_result.deleted_count,
            "events_deleted": events_result.deleted_count,
        }


inventory_repo = InventoryRepository()
