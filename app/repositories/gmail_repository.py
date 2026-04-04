"""Gmail repositories – data access for linked_accounts, email_expenses, email_sync_runs."""

from datetime import datetime
from typing import Optional

from bson import ObjectId

from app.db import get_database


class LinkedAccountRepository:
    """CRUD for the `linked_accounts` collection."""

    def _col(self):
        return get_database().linked_accounts

    @staticmethod
    def _from_doc(doc: dict) -> dict:
        if doc and "_id" in doc:
            doc["_id"] = str(doc["_id"])
        return doc

    async def upsert(self, user_id: str, data: dict) -> dict:
        result = await self._col().find_one_and_update(
            {"userId": user_id, "provider": "gmail"},
            {"$set": {**data, "updatedAt": datetime.utcnow()}},
            upsert=True,
            return_document=True,
        )
        return self._from_doc(result)

    async def find_by_user(self, user_id: str) -> Optional[dict]:
        doc = await self._col().find_one({"userId": user_id, "provider": "gmail"})
        return self._from_doc(doc) if doc else None

    async def update(self, user_id: str, update: dict) -> Optional[dict]:
        update["updatedAt"] = datetime.utcnow()
        result = await self._col().find_one_and_update(
            {"userId": user_id, "provider": "gmail"},
            {"$set": update},
            return_document=True,
        )
        return self._from_doc(result) if result else None

    async def delete(self, user_id: str) -> bool:
        result = await self._col().delete_one({"userId": user_id, "provider": "gmail"})
        return result.deleted_count > 0

    async def find_all_sync_enabled(self) -> list[dict]:
        cursor = self._col().find({"syncEnabled": True, "provider": "gmail"})
        return [self._from_doc(doc) async for doc in cursor]


class EmailExpenseRepository:
    """CRUD for the `email_expenses` collection."""

    def _col(self):
        return get_database().email_expenses

    @staticmethod
    def _from_doc(doc: dict) -> dict:
        if doc and "_id" in doc:
            doc["_id"] = str(doc["_id"])
        return doc

    async def insert(self, data: dict) -> str:
        result = await self._col().insert_one(data)
        return str(result.inserted_id)

    async def exists_by_gmail_id(self, user_id: str, gmail_message_id: str) -> bool:
        doc = await self._col().find_one(
            {"userId": user_id, "gmailMessageId": gmail_message_id},
            {"_id": 1},
        )
        return doc is not None

    async def find_by_id(self, expense_id: str) -> Optional[dict]:
        doc = await self._col().find_one({"_id": ObjectId(expense_id)})
        return self._from_doc(doc) if doc else None

    async def find_by_user(
        self,
        user_id: str,
        page: int = 1,
        page_size: int = 20,
        category: Optional[str] = None,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        merchant: Optional[str] = None,
    ) -> tuple[list[dict], int]:
        query: dict = {"userId": user_id}
        if category:
            query["category"] = category
        if merchant:
            query["normalizedMerchant"] = {"$regex": merchant.lower(), "$options": "i"}
        if from_date or to_date:
            date_q: dict = {}
            if from_date:
                date_q["$gte"] = from_date
            if to_date:
                date_q["$lte"] = to_date
            query["transactionAt"] = date_q

        total = await self._col().count_documents(query)
        cursor = (
            self._col()
            .find(query)
            .sort("transactionAt", -1)
            .skip((page - 1) * page_size)
            .limit(page_size)
        )
        docs = [self._from_doc(doc) async for doc in cursor]
        return docs, total

    async def update(self, expense_id: str, update: dict) -> Optional[dict]:
        update["updatedAt"] = datetime.utcnow()
        result = await self._col().find_one_and_update(
            {"_id": ObjectId(expense_id)},
            {"$set": update},
            return_document=True,
        )
        return self._from_doc(result) if result else None

    async def delete_by_id(self, expense_id: str) -> bool:
        """Delete a specific email expense by ID."""
        result = await self._col().delete_one({"_id": ObjectId(expense_id)})
        return result.deleted_count > 0

    async def delete_all_by_user(self, user_id: str) -> int:
        """Delete all email expenses for a user (testing reset)."""
        result = await self._col().delete_many({"userId": user_id})
        return result.deleted_count

    async def total_spend_since(self, user_id: str, since: datetime) -> float:
        pipeline = [
            {"$match": {"userId": user_id, "transactionAt": {"$gte": since}}},
            {"$group": {"_id": None, "total": {"$sum": "$amount"}}},
        ]
        async for doc in self._col().aggregate(pipeline):
            return doc.get("total", 0)
        return 0

    async def aggregate_by_category(self, user_id: str, since: datetime) -> list[dict]:
        pipeline = [
            {"$match": {"userId": user_id, "transactionAt": {"$gte": since}}},
            {"$group": {
                "_id": "$category",
                "totalSpend": {"$sum": "$amount"},
                "count": {"$sum": 1},
            }},
            {"$sort": {"totalSpend": -1}},
        ]
        return [doc async for doc in self._col().aggregate(pipeline)]


class SyncRunRepository:
    """CRUD for the `email_sync_runs` collection."""

    def _col(self):
        return get_database().email_sync_runs

    @staticmethod
    def _from_doc(doc: dict) -> dict:
        if doc and "_id" in doc:
            doc["_id"] = str(doc["_id"])
        return doc

    async def insert(self, data: dict) -> str:
        result = await self._col().insert_one(data)
        return str(result.inserted_id)

    async def update(self, run_id: str, update: dict) -> Optional[dict]:
        result = await self._col().find_one_and_update(
            {"_id": ObjectId(run_id)},
            {"$set": update},
            return_document=True,
        )
        return self._from_doc(result) if result else None

    async def find_by_user(self, user_id: str, limit: int = 10) -> list[dict]:
        cursor = (
            self._col()
            .find({"userId": user_id})
            .sort("startedAt", -1)
            .limit(limit)
        )
        return [self._from_doc(doc) async for doc in cursor]


linked_account_repo = LinkedAccountRepository()
email_expense_repo = EmailExpenseRepository()
sync_run_repo = SyncRunRepository()
