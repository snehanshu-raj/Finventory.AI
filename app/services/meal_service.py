"""Meal and shopping suggestion service."""

import json
import logging
from typing import Optional

from app.repositories.inventory_repository import inventory_repo
from app.repositories.price_repository import price_repo
from app.services.llm_provider import get_llm_provider, MEAL_SUGGESTION_PROMPT_TEMPLATE

logger = logging.getLogger(__name__)


class MealService:
    """Business logic for meal and shopping suggestions."""

    async def suggest_meals(self, user_id: str, constraints: dict) -> dict:
        """Ask LLM for meal suggestions based on current pantry."""
        # Fetch pantry items with meaningful quantities
        states = await inventory_repo.find_all_states(user_id)
        available = [
            {
                "name": s.get("canonicalName", ""),
                "quantity": s.get("currentQuantity", 0),
                "unit": s.get("unit", ""),
            }
            for s in states
            if s.get("currentQuantity", 0) > 0
        ]

        if not available:
            return {"meals": []}

        pantry_str = "\n".join(
            f"- {item['name']}: {item['quantity']} {item['unit']}" for item in available
        )

        prompt = MEAL_SUGGESTION_PROMPT_TEMPLATE.format(
            pantry_items=pantry_str,
            max_prep_minutes=constraints.get("max_prep_minutes") or "any",
            vegetarian=constraints.get("vegetarian", False),
            budget_mode=constraints.get("budget_mode", False),
        )

        provider = get_llm_provider()
        raw_text = await provider.generate_text(prompt)

        try:
            # Parse JSON from response
            cleaned = raw_text.strip()
            if cleaned.startswith("```"):
                lines = cleaned.split("\n")
                lines = lines[1:]
                if lines and lines[-1].strip() == "```":
                    lines = lines[:-1]
                cleaned = "\n".join(lines)
            parsed = json.loads(cleaned)
        except (json.JSONDecodeError, Exception) as e:
            logger.warning("Failed to parse meal suggestions: %s", e)
            parsed = {"meals": []}

        meals = []
        for m in parsed.get("meals", []):
            meals.append({
                "title": m.get("title", ""),
                "description": m.get("description", ""),
                "pantry_ingredients_used": m.get("pantryIngredientsUsed", []),
                "missing_ingredients": m.get("missingIngredients", []),
                "prep_time_minutes": m.get("prepTimeMinutes"),
                "why_suggested": m.get("whySuggested", ""),
            })

        return {"meals": meals}

    async def suggest_shopping(
        self, user_id: str, budget_limit: Optional[float] = None
    ) -> dict:
        """Generate shopping suggestions from low stock + price insights. If no stock is low, return possible items to purchase."""
        # Get all inventory states
        states = await inventory_repo.find_all_states(user_id)

        must_buy = []
        buy_soon = []

        for s in states:
            status = s.get("status", "ok")
            if status in ("out_of_stock", "critical", "low"):
                daily_rate = s.get("dailyConsumptionEstimate", 0)
                current_qty = s.get("currentQuantity", 0)
                days_left = round(current_qty / daily_rate, 1) if daily_rate > 0 else None

                # Try to find cheapest store
                cid = s.get("canonicalItemId", "")
                cheapest = None
                est_price = None
                if cid:
                    agg = await price_repo.aggregate_by_store(user_id, cid, 30)
                    if agg:
                        cheapest = agg[0].get("_id")
                        est_price = round(agg[0].get("avgUnitPrice", 0), 2)

                item_data = {
                    "canonical_item_id": cid,
                    "canonical_name": s.get("canonicalName", ""),
                    "current_quantity": current_qty,
                    "threshold_quantity": s.get("thresholdQuantity", 0),
                    "estimated_days_left": days_left,
                    "cheapest_store": cheapest,
                    "estimated_price": est_price,
                }

                if status in ("out_of_stock", "critical"):
                    must_buy.append(item_data)
                else:
                    buy_soon.append(item_data)

        return {
            "must_buy_now": must_buy,
            "buy_soon": buy_soon,
            "states": states
        }


meal_service = MealService()
