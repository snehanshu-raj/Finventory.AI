"""Notification repository – data access for the `notifications` collection."""

from datetime import datetime
from typing import Optional

from bson import ObjectId

from app.db import get_database


class NotificationRepository:
    """Async data access for the `notifications` collection."""

    def _col(self):
        return get_database().notifications

    @staticmethod
    def _from_doc(doc: dict) -> dict:
        if doc and "_id" in doc:
            doc["_id"] = str(doc["_id"])
        return doc

    async def insert(self, data: dict) -> str:
        """Insert a notification and return its id."""
        result = await self._col().insert_one(data)
        return str(result.inserted_id)

    async def find_by_user(
        self, user_id: str, page: int = 1, page_size: int = 20
    ) -> tuple[list[dict], int]:
        """List notifications for a user with pagination."""
        query = {"userId": user_id}
        total = await self._col().count_documents(query)
        cursor = (
            self._col()
            .find(query)
            .sort("createdAt", -1)
            .skip((page - 1) * page_size)
            .limit(page_size)
        )
        docs = [self._from_doc(doc) async for doc in cursor]
        return docs, total

    async def update_status(self, notification_id: str, status: str) -> Optional[dict]:
        """Update notification status."""
        update: dict = {"status": status}
        if status == "sent":
            update["sentAt"] = datetime.utcnow()
        result = await self._col().find_one_and_update(
            {"_id": ObjectId(notification_id)},
            {"$set": update},
            return_document=True,
        )
        return self._from_doc(result) if result else None

    async def find_by_id(self, notification_id: str) -> Optional[dict]:
        """Find a single notification by id."""
        doc = await self._col().find_one({"_id": ObjectId(notification_id)})
        return self._from_doc(doc) if doc else None


notification_repo = NotificationRepository()
