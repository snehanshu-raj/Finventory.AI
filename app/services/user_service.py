"""User service – onboarding and profile business logic."""

import logging
from datetime import datetime

from app.config import settings
from app.repositories.user_repository import user_repo
from app.repositories.inventory_repository import inventory_repo
from app.utils.exceptions import NotFoundException

logger = logging.getLogger(__name__)


class UserService:
    """Business logic for user onboarding and management."""

    async def onboard_user(self, data: dict) -> dict:
        """Create or update a user via onboarding and initialise inventory for staples."""
        email = data["email"]

        # Build MongoDB document in camelCase
        doc = {
            "name": data["name"],
            "email": email,
            "householdProfile": {
                "householdSize": data["household_profile"]["household_size"],
                "adults": data["household_profile"]["adults"],
                "children": data["household_profile"]["children"],
            },
            "dietProfile": {
                "staples": [
                    {
                        "canonicalItemId": s["canonical_item_id"],
                        "canonicalName": s["canonical_name"],
                        "dailyConsumptionEstimate": s["daily_consumption_estimate"],
                        "unit": s["unit"],
                        "thresholdQuantity": s["threshold_quantity"],
                    }
                    for s in data["diet_profile"].get("staples", [])
                ]
            },
            "preferences": {
                "currency": data["preferences"]["currency"],
                "locale": data["preferences"]["locale"],
                "notificationEnabled": data["preferences"]["notification_enabled"],
                "notificationChannels": data["preferences"]["notification_channels"],
            },
        }

        user = await user_repo.upsert_by_email(
            email, doc, fixed_id=settings.default_user_id or None
        )
        user_id = user["_id"]

        # Initialise inventory_state for each staple that doesn't already exist
        for staple in data["diet_profile"].get("staples", []):
            existing = await inventory_repo.find_state(
                user_id, staple["canonical_item_id"]
            )
            if not existing:
                await inventory_repo.upsert_state(
                    user_id,
                    staple["canonical_item_id"],
                    {
                        "userId": user_id,
                        "canonicalItemId": staple["canonical_item_id"],
                        "canonicalName": staple["canonical_name"],
                        "currentQuantity": 0.0,
                        "unit": staple["unit"],
                        "thresholdQuantity": staple["threshold_quantity"],
                        "dailyConsumptionEstimate": staple["daily_consumption_estimate"],
                        "estimatedDaysLeft": 0,
                        "status": "out_of_stock",
                        "reminderEnabled": True,
                    },
                )
                logger.info(
                    "Created inventory state for user=%s item=%s",
                    user_id,
                    staple["canonical_item_id"],
                )

        return self._to_response(user)

    async def get_user(self, user_id: str) -> dict:
        """Get a user by id."""
        user = await user_repo.find_by_id(user_id)
        if not user:
            raise NotFoundException(f"User {user_id} not found")
        return self._to_response(user)

    async def update_staples(self, user_id: str, staples: list[dict]) -> dict:
        """Update staple configs and sync inventory_state thresholds."""
        mongo_staples = [
            {
                "canonicalItemId": s["canonical_item_id"],
                "canonicalName": s["canonical_name"],
                "dailyConsumptionEstimate": s["daily_consumption_estimate"],
                "unit": s["unit"],
                "thresholdQuantity": s["threshold_quantity"],
            }
            for s in staples
        ]

        user = await user_repo.update_staples(user_id, mongo_staples)
        if not user:
            raise NotFoundException(f"User {user_id} not found")

        # Sync inventory_state for each staple
        for s in staples:
            await inventory_repo.upsert_state(
                user_id,
                s["canonical_item_id"],
                {
                    "userId": user_id,
                    "canonicalItemId": s["canonical_item_id"],
                    "canonicalName": s["canonical_name"],
                    "unit": s["unit"],
                    "thresholdQuantity": s["threshold_quantity"],
                    "dailyConsumptionEstimate": s["daily_consumption_estimate"],
                },
            )

        return self._to_response(user)

    # ── Helpers ────────────────────────────────────────────────────────

    @staticmethod
    def _to_response(user: dict) -> dict:
        """Normalize a MongoDB user doc into API response format."""
        hp = user.get("householdProfile", {})
        dp = user.get("dietProfile", {})
        prefs = user.get("preferences", {})
        return {
            "id": user["_id"],
            "email": user.get("email", ""),
            "name": user.get("name", ""),
            "created_at": user.get("createdAt", datetime.utcnow()),
            "updated_at": user.get("updatedAt", datetime.utcnow()),
            "household_profile": {
                "household_size": hp.get("householdSize", 1),
                "adults": hp.get("adults", 1),
                "children": hp.get("children", 0),
            },
            "diet_profile": {
                "staples": [
                    {
                        "canonical_item_id": s.get("canonicalItemId", ""),
                        "canonical_name": s.get("canonicalName", ""),
                        "daily_consumption_estimate": s.get("dailyConsumptionEstimate", 0),
                        "unit": s.get("unit", ""),
                        "threshold_quantity": s.get("thresholdQuantity", 0),
                    }
                    for s in dp.get("staples", [])
                ]
            },
            "preferences": {
                "currency": prefs.get("currency", "USD"),
                "locale": prefs.get("locale", "en-US"),
                "notification_enabled": prefs.get("notificationEnabled", True),
                "notification_channels": prefs.get("notificationChannels", ["in_app"]),
            },
        }


user_service = UserService()
