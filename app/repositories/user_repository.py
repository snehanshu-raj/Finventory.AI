"""User repository – data access for the `users` collection."""

from datetime import datetime
from typing import Any, Optional

from bson import ObjectId

from app.db import get_database


class UserRepository:
    """Async data access layer for the `users` collection."""

    def _col(self):
        return get_database().users

    # ── Helpers ────────────────────────────────────────────────────────

    @staticmethod
    def _to_doc(data: dict) -> dict:
        """Convert camelCase schema keys to snake_case MongoDB fields."""
        return data

    @staticmethod
    def _from_doc(doc: dict) -> dict:
        """Normalise a MongoDB document for API consumption."""
        if doc and "_id" in doc:
            doc["_id"] = str(doc["_id"])
        return doc

    # ── CRUD ───────────────────────────────────────────────────────────

    async def upsert_by_email(self, email: str, data: dict, fixed_id: str = None) -> dict:
        """Create or update a user by email, returning the document.
        If fixed_id is provided, use it as _id instead of auto-generating.
        """
        now = datetime.utcnow()
        data["updatedAt"] = now

        filter_query = {"email": email}
        set_on_insert = {"createdAt": now}

        # Use fixed _id if provided (single-user mode)
        if fixed_id:
            filter_query = {"_id": ObjectId(fixed_id)}
            set_on_insert["email"] = email
            # Remove email from $set to avoid conflict with $setOnInsert
            data.pop("email", None)

        result = await self._col().find_one_and_update(
            filter_query,
            {"$set": data, "$setOnInsert": set_on_insert},
            upsert=True,
            return_document=True,
        )
        return self._from_doc(result)

    async def find_by_id(self, user_id: str) -> Optional[dict]:
        """Find a user by _id."""
        doc = await self._col().find_one({"_id": ObjectId(user_id)})
        return self._from_doc(doc) if doc else None

    async def find_by_email(self, email: str) -> Optional[dict]:
        """Find a user by email."""
        doc = await self._col().find_one({"email": email})
        return self._from_doc(doc) if doc else None

    async def update_staples(self, user_id: str, staples: list[dict]) -> Optional[dict]:
        """Update dietProfile.staples for a user."""
        result = await self._col().find_one_and_update(
            {"_id": ObjectId(user_id)},
            {
                "$set": {
                    "dietProfile.staples": staples,
                    "updatedAt": datetime.utcnow(),
                },
            },
            return_document=True,
        )
        return self._from_doc(result) if result else None


user_repo = UserRepository()
