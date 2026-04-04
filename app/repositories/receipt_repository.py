"""Receipt repository – data access for the `receipts` collection."""

from datetime import datetime
from typing import Any, Optional

from bson import ObjectId

from app.db import get_database


class ReceiptRepository:
    """Async data access layer for the `receipts` collection."""

    def _col(self):
        return get_database().receipts

    @staticmethod
    def _from_doc(doc: dict) -> dict:
        if doc and "_id" in doc:
            doc["_id"] = str(doc["_id"])
        return doc

    async def insert(self, data: dict) -> str:
        """Insert a new receipt and return its id."""
        result = await self._col().insert_one(data)
        return str(result.inserted_id)

    async def find_by_id(self, receipt_id: str) -> Optional[dict]:
        """Find a receipt by _id."""
        doc = await self._col().find_one({"_id": ObjectId(receipt_id)})
        return self._from_doc(doc) if doc else None

    async def find_by_user(
        self,
        user_id: str,
        page: int = 1,
        page_size: int = 20,
        month: Optional[str] = None,
        store: Optional[str] = None,
    ) -> tuple[list[dict], int]:
        """List receipts for a user with pagination and optional filters."""
        query: dict[str, Any] = {"userId": user_id}
        if month:
            query["derived.monthBucket"] = month
        if store:
            query["merchant.normalizedName"] = store.lower()

        total = await self._col().count_documents(query)
        cursor = (
            self._col()
            .find(query)
            .sort("transaction.purchasedAt", -1)
            .skip((page - 1) * page_size)
            .limit(page_size)
        )
        docs = [self._from_doc(doc) async for doc in cursor]
        return docs, total

    async def update(self, receipt_id: str, update_data: dict) -> Optional[dict]:
        """Partial update and return the updated receipt."""
        result = await self._col().find_one_and_update(
            {"_id": ObjectId(receipt_id)},
            {"$set": update_data},
            return_document=True,
        )
        return self._from_doc(result) if result else None


    async def delete(self, receipt_id: str) -> bool:
        """Delete a receipt by _id."""
        result = await self._col().delete_one({"_id": ObjectId(receipt_id)})
        return result.deleted_count > 0


receipt_repo = ReceiptRepository()
