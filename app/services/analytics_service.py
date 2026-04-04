"""Analytics service – expense summaries, price insights, predictions, and dashboard."""

import logging
from datetime import datetime, timedelta
from typing import Optional

from app.config import settings
from app.repositories.inventory_repository import inventory_repo
from app.repositories.price_repository import price_repo

logger = logging.getLogger(__name__)


class AnalyticsService:
    """Business logic for analytics, predictions, and price insights."""

    # ── Predictions ────────────────────────────────────────────────────

    async def get_predictions(self, user_id: str) -> list[dict]:
        """Return run-out timeline for all inventory items."""
        states = await inventory_repo.find_all_states(user_id)
        predictions = []
        for s in states:
            daily_rate = s.get("dailyConsumptionEstimate", 0)
            current_qty = max(s.get("currentQuantity", 0), 0)
            if daily_rate > 0:
                days_left = round(current_qty / daily_rate, 1)
                run_out_date = datetime.utcnow() + timedelta(days=days_left)
            else:
                days_left = None
                run_out_date = None

            threshold = s.get("thresholdQuantity", 0)
            if current_qty <= 0:
                status = "out_of_stock"
            elif threshold > 0 and current_qty <= threshold * 0.5:
                status = "critical"
            elif threshold > 0 and current_qty <= threshold:
                status = "low"
            else:
                status = "ok"

            predictions.append({
                "canonical_item_id": s.get("canonicalItemId", ""),
                "canonical_name": s.get("canonicalName", ""),
                "current_quantity": current_qty,
                "daily_consumption_estimate": daily_rate,
                "estimated_days_left": days_left,
                "predicted_run_out_date": run_out_date,
                "status": status,
            })
        return predictions

    # ── Expense Summary ────────────────────────────────────────────────

    async def get_expense_summary(self, user_id: str) -> dict:
        """Return spending summaries by month, store, category, and top items."""
        now = datetime.utcnow()
        current_month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        if now.month == 1:
            prev_month_start = current_month_start.replace(year=now.year - 1, month=12)
        else:
            prev_month_start = current_month_start.replace(month=now.month - 1)

        current_total = await price_repo.total_spend_since(user_id, current_month_start)
        previous_total = await price_repo.total_spend_since(user_id, prev_month_start)
        # Subtract current month from "since prev month" total
        previous_total = max(previous_total - current_total, 0)

        by_store_raw = await price_repo.aggregate_expenses_by_store(user_id, current_month_start)
        by_store = [
            {
                "store_name": s["_id"] or "Unknown",
                "total_spend": round(s["totalSpend"], 2),
                "receipt_count": len(s.get("receiptIds", [])),
            }
            for s in by_store_raw
        ]

        by_category_raw = await price_repo.aggregate_expenses_by_category(user_id, current_month_start)
        by_category = [
            {
                "category": c["_id"] or "uncategorized",
                "total_spend": round(c["totalSpend"], 2),
                "item_count": c.get("itemCount", 0),
            }
            for c in by_category_raw
        ]

        top_items_raw = await price_repo.aggregate_top_items(user_id, current_month_start)
        top_spend_items = [
            {
                "canonical_name": t["_id"] or "unknown",
                "total_spend": round(t["totalSpend"], 2),
                "purchase_count": t.get("purchaseCount", 0),
            }
            for t in top_items_raw
        ]

        return {
            "current_month_total": round(current_total, 2),
            "previous_month_total": round(previous_total, 2),
            "by_store": by_store,
            "by_category": by_category,
            "top_spend_items": top_spend_items,
        }

    # ── Best Store ─────────────────────────────────────────────────────

    async def get_best_store(
        self, user_id: str, item: str, window: str = "30d"
    ) -> dict:
        """Find the cheapest store for an item based on recent observations."""
        window_days = self._parse_window(window)
        agg = await price_repo.aggregate_by_store(user_id, item, window_days)

        min_samples = settings.min_price_samples
        stores = [
            {
                "store_name": s["_id"] or "Unknown",
                "avg_unit_price": round(s["avgUnitPrice"], 4),
                "samples": s["samples"],
                "last_seen": s.get("lastSeen"),
            }
            for s in agg
        ]

        best = None
        confidence = None
        for s in stores:
            if s["samples"] >= min_samples:
                best = s["store_name"]
                total_samples = sum(x["samples"] for x in stores)
                confidence = round(s["samples"] / total_samples, 2) if total_samples else None
                break

        return {
            "canonical_item_id": item,
            "canonical_name": item,
            "best_store": best,
            "stores": stores,
            "confidence": confidence,
            "insight": f"Best store for {item} is {best}" if best else "Not enough data",
        }

    # ── Price Compare ──────────────────────────────────────────────────

    async def compare_prices(
        self, user_id: str, item: str, window: str = "30d"
    ) -> dict:
        """Multi-store price comparison for an item."""
        window_days = self._parse_window(window)
        agg = await price_repo.aggregate_by_store(user_id, item, window_days)
        stores = [
            {
                "store_name": s["_id"] or "Unknown",
                "avg_unit_price": round(s["avgUnitPrice"], 4),
                "samples": s["samples"],
                "last_seen": s.get("lastSeen"),
            }
            for s in agg
        ]
        return {
            "canonical_item_id": item,
            "canonical_name": item,
            "stores": stores,
        }

    # ── Dashboard ──────────────────────────────────────────────────────

    async def get_dashboard(self, user_id: str) -> dict:
        """Combined dashboard with spend, low stock, run-outs, and savings."""
        now = datetime.utcnow()
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        monthly_spend = await price_repo.total_spend_since(user_id, month_start)
        low_stock_items = await inventory_repo.find_low_stock(user_id)
        predictions = await self.get_predictions(user_id)

        running_out_7d = [
            p for p in predictions
            if p["estimated_days_left"] is not None and p["estimated_days_left"] <= 7
        ]

        by_store_raw = await price_repo.aggregate_expenses_by_store(user_id, month_start)
        top_stores = [
            {
                "store_name": s["_id"] or "Unknown",
                "total_spend": round(s["totalSpend"], 2),
                "receipt_count": len(s.get("receiptIds", [])),
            }
            for s in by_store_raw[:5]
        ]

        return {
            "monthly_spend": round(monthly_spend, 2),
            "low_stock_count": len(low_stock_items),
            "items_running_out_7days": running_out_7d,
            "top_stores": top_stores,
            "savings_opportunities": [],  # populated by price insight job
        }

    # ── Helpers ────────────────────────────────────────────────────────

    @staticmethod
    def _parse_window(window: str) -> int:
        """Parse a window string like '30d' into days."""
        try:
            return int(window.rstrip("d"))
        except ValueError:
            return 30


analytics_service = AnalyticsService()
