"""Inventory service – stock management business logic."""

import logging
from datetime import datetime, timedelta
from typing import Optional

from app.config import settings
from app.repositories.inventory_repository import inventory_repo
from app.repositories.notification_repository import notification_repo
from app.utils.exceptions import NotFoundException

logger = logging.getLogger(__name__)


class InventoryService:
    """Business logic for inventory and stock management."""

    # ── Status computation ─────────────────────────────────────────────

    @staticmethod
    def compute_status(current_qty: float, threshold: float) -> str:
        """Determine inventory status from quantity and threshold."""
        if current_qty <= 0:
            return "out_of_stock"
        if threshold > 0 and current_qty <= threshold * 0.5:
            return "critical"
        if threshold > 0 and current_qty <= threshold:
            return "low"
        return "ok"

    @staticmethod
    def compute_days_left(current_qty: float, daily_rate: float) -> Optional[float]:
        """Estimate days left before running out."""
        if daily_rate <= 0:
            return None
        return round(max(current_qty, 0) / daily_rate, 1)

    # ── Apply purchases from receipt ───────────────────────────────────

    async def apply_receipt_purchases(
        self,
        user_id: str,
        receipt_id: str,
        items: list[dict],
        store_name: str = "",
    ) -> None:
        """Add purchased quantities to inventory and log events."""
        for item in items:
            if not item.get("is_grocery", True):
                continue

            cid = item.get("canonical_name", "").lower().replace(" ", "_")
            if not cid:
                continue

            qty = item.get("normalized_quantity") or item.get("quantity", 0)
            unit = item.get("normalized_unit") or item.get("unit", "count")

            # Upsert inventory state
            existing = await inventory_repo.find_state(user_id, cid)
            if existing:
                new_qty = existing.get("currentQuantity", 0) + qty
                daily_rate = existing.get("dailyConsumptionEstimate", 0)
                status = self.compute_status(new_qty, existing.get("thresholdQuantity", 0))
                days_left = self.compute_days_left(new_qty, daily_rate)
                await inventory_repo.update_state(user_id, cid, {
                    "currentQuantity": new_qty,
                    "status": status,
                    "estimatedDaysLeft": days_left,
                    "lastReceiptAt": datetime.utcnow(),
                    "metadata.lastPurchaseStore": store_name,
                    "metadata.lastPurchasePrice": item.get("line_price", 0),
                    "metadata.sourceConfidence": item.get("confidence", 0),
                })
            else:
                new_qty = qty
                await inventory_repo.upsert_state(user_id, cid, {
                    "userId": user_id,
                    "canonicalItemId": cid,
                    "canonicalName": item.get("canonical_name", cid),
                    "category": item.get("category"),
                    "currentQuantity": new_qty,
                    "unit": unit,
                    "thresholdQuantity": 0,
                    "dailyConsumptionEstimate": 0,
                    "estimatedDaysLeft": None,
                    "status": "ok",
                    "lastReceiptAt": datetime.utcnow(),
                    "reminderEnabled": True,
                    "metadata": {
                        "sourceConfidence": item.get("confidence", 0),
                        "lastPurchaseStore": store_name,
                        "lastPurchasePrice": item.get("line_price", 0),
                    },
                })

            # Log event
            await inventory_repo.insert_event({
                "userId": user_id,
                "canonicalItemId": cid,
                "canonicalName": item.get("canonical_name", cid),
                "eventType": "purchase",
                "deltaQuantity": qty,
                "unit": unit,
                "createdAt": datetime.utcnow(),
                "source": {"type": "receipt", "referenceId": receipt_id},
                "meta": {"storeName": store_name},
            })

    # ── Manual adjustment ──────────────────────────────────────────────

    async def manual_adjust(
        self, user_id: str, canonical_item_id: str, new_qty: float, unit: str, reason: str
    ) -> dict:
        """Manually set inventory quantity and recompute status."""
        state = await inventory_repo.find_state(user_id, canonical_item_id)
        if not state:
            raise NotFoundException(f"Inventory item '{canonical_item_id}' not found")

        old_qty = state.get("currentQuantity", 0)
        delta = new_qty - old_qty
        daily_rate = state.get("dailyConsumptionEstimate", 0)
        threshold = state.get("thresholdQuantity", 0)
        status = self.compute_status(new_qty, threshold)
        days_left = self.compute_days_left(new_qty, daily_rate)

        updated = await inventory_repo.update_state(user_id, canonical_item_id, {
            "currentQuantity": new_qty,
            "unit": unit,
            "status": status,
            "estimatedDaysLeft": days_left,
        })

        await inventory_repo.insert_event({
            "userId": user_id,
            "canonicalItemId": canonical_item_id,
            "canonicalName": state.get("canonicalName", canonical_item_id),
            "eventType": "manual_adjustment",
            "deltaQuantity": delta,
            "unit": unit,
            "createdAt": datetime.utcnow(),
            "source": {"type": "manual", "referenceId": None},
            "meta": {"reason": reason, "oldQuantity": old_qty},
        })

        return self._to_response(updated)

    # ── Daily decrement (called by job) ────────────────────────────────

    async def daily_decrement_all(self) -> int:
        """Decrement all inventory items and create events. Returns count processed."""
        states = await inventory_repo.find_all_states_global()
        count = 0

        for state in states:
            daily_rate = state.get("dailyConsumptionEstimate", 0)
            if daily_rate <= 0:
                continue

            user_id = state["userId"]
            cid = state["canonicalItemId"]
            old_qty = state.get("currentQuantity", 0)

            if old_qty <= 0:
                continue

            new_qty = max(old_qty - daily_rate, 0)
            threshold = state.get("thresholdQuantity", 0)
            old_status = state.get("status", "ok")
            new_status = self.compute_status(new_qty, threshold)
            days_left = self.compute_days_left(new_qty, daily_rate)

            await inventory_repo.update_state(user_id, cid, {
                "currentQuantity": new_qty,
                "status": new_status,
                "estimatedDaysLeft": days_left,
            })

            await inventory_repo.insert_event({
                "userId": user_id,
                "canonicalItemId": cid,
                "canonicalName": state.get("canonicalName", cid),
                "eventType": "daily_decrement",
                "deltaQuantity": -daily_rate,
                "unit": state.get("unit", "count"),
                "createdAt": datetime.utcnow(),
                "source": {"type": "system", "referenceId": None},
                "meta": {"oldQuantity": old_qty, "newQuantity": new_qty},
            })

            # Trigger low-stock notification if crossed threshold
            if (
                old_status == "ok"
                and new_status in ("low", "critical", "out_of_stock")
                and state.get("reminderEnabled", True)
            ):
                await self._maybe_send_reminder(user_id, cid, state, new_qty, new_status)

            count += 1

        logger.info("Daily decrement processed %d items", count)
        return count

    async def _maybe_send_reminder(
        self,
        user_id: str,
        canonical_item_id: str,
        state: dict,
        current_qty: float,
        status: str,
    ) -> None:
        """Send a low-stock reminder if cooldown has passed."""
        last_reminder = state.get("lastReminderSentAt")
        cooldown = timedelta(days=settings.reminder_cooldown_days)

        if last_reminder and (datetime.utcnow() - last_reminder) < cooldown:
            return

        name = state.get("canonicalName", canonical_item_id)
        await notification_repo.insert({
            "userId": user_id,
            "type": "low_stock",
            "title": f"Low stock: {name}",
            "message": f"{name} is {status}. Current quantity: {current_qty} {state.get('unit', '')}.",
            "status": "pending",
            "channel": "in_app",
            "context": {
                "canonicalItemId": canonical_item_id,
                "currentQuantity": current_qty,
                "status": status,
            },
            "createdAt": datetime.utcnow(),
        })

        await inventory_repo.update_state(user_id, canonical_item_id, {
            "lastReminderSentAt": datetime.utcnow(),
        })
        logger.info("Low-stock reminder sent for user=%s item=%s", user_id, canonical_item_id)

    # ── Reverse receipt effects (for correction) ───────────────────────

    async def reverse_receipt_effects(self, user_id: str, receipt_id: str, items: list[dict]) -> None:
        """Reverse inventory changes from a receipt (for edit/replay)."""
        for item in items:
            if not item.get("isGrocery", True):
                continue
            cid = item.get("canonicalItemId") or item.get("canonicalName", "").lower().replace(" ", "_")
            if not cid:
                continue

            qty = item.get("normalizedQuantity") or item.get("quantity", 0)
            state = await inventory_repo.find_state(user_id, cid)
            if state:
                new_qty = max(state.get("currentQuantity", 0) - qty, 0)
                threshold = state.get("thresholdQuantity", 0)
                daily_rate = state.get("dailyConsumptionEstimate", 0)
                await inventory_repo.update_state(user_id, cid, {
                    "currentQuantity": new_qty,
                    "status": self.compute_status(new_qty, threshold),
                    "estimatedDaysLeft": self.compute_days_left(new_qty, daily_rate),
                })

        await inventory_repo.delete_events_by_receipt(receipt_id)

    # ── Query helpers ──────────────────────────────────────────────────

    async def get_all_items(self, user_id: str, **filters) -> list[dict]:
        """Get all inventory items for a user."""
        states = await inventory_repo.find_all_states(user_id, **filters)
        return [self._to_response(s) for s in states]

    async def get_low_stock(self, user_id: str) -> list[dict]:
        """Get low/critical/out-of-stock items."""
        states = await inventory_repo.find_low_stock(user_id)
        return [self._to_response(s) for s in states]

    async def get_item_detail(self, user_id: str, canonical_item_id: str) -> dict:
        """Get a single item with recent events."""
        state = await inventory_repo.find_state(user_id, canonical_item_id)
        if not state:
            raise NotFoundException(f"Inventory item '{canonical_item_id}' not found")
        events = await inventory_repo.find_events(user_id, canonical_item_id, limit=20)
        return {
            "item": self._to_response(state),
            "recent_events": [
                {
                    "id": e["_id"],
                    "canonical_item_id": e.get("canonicalItemId", ""),
                    "canonical_name": e.get("canonicalName", ""),
                    "event_type": e.get("eventType", ""),
                    "delta_quantity": e.get("deltaQuantity", 0),
                    "unit": e.get("unit", ""),
                    "created_at": e.get("createdAt", datetime.utcnow()),
                    "source": e.get("source", {}),
                }
                for e in events
            ],
        }

    # ── Reset / wipe all inventory ───────────────────────────────────

    async def reset_inventory(self, user_id: str) -> dict:
        """Delete all inventory states and events for a user (for testing)."""
        result = await inventory_repo.delete_all_by_user(user_id)
        logger.info("Inventory reset for user %s: %s", user_id, result)
        return result

    @staticmethod
    def _to_response(state: dict) -> dict:
        """Convert a MongoDB inventory_state doc to API response format."""
        return {
            "canonical_item_id": state.get("canonicalItemId", ""),
            "canonical_name": state.get("canonicalName", ""),
            "category": state.get("category"),
            "current_quantity": state.get("currentQuantity", 0),
            "unit": state.get("unit", ""),
            "threshold_quantity": state.get("thresholdQuantity", 0),
            "daily_consumption_estimate": state.get("dailyConsumptionEstimate", 0),
            "estimated_days_left": state.get("estimatedDaysLeft"),
            "status": state.get("status", "ok"),
            "last_updated_at": state.get("lastUpdatedAt", datetime.utcnow()),
            "last_receipt_at": state.get("lastReceiptAt"),
            "reminder_enabled": state.get("reminderEnabled", True),
            "last_reminder_sent_at": state.get("lastReminderSentAt"),
        }


inventory_service = InventoryService()
