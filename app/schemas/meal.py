"""Meal and shopping suggestion schemas."""

from typing import Optional

from pydantic import BaseModel, Field


# ── Request Schemas ────────────────────────────────────────────────────

class MealConstraints(BaseModel):
    max_prep_minutes: Optional[int] = None
    vegetarian: bool = False
    budget_mode: bool = False


class MealSuggestRequest(BaseModel):
    """POST /api/v1/meals/suggest body."""
    user_id: str
    constraints: MealConstraints = Field(default_factory=MealConstraints)


class ShoppingSuggestRequest(BaseModel):
    """POST /api/v1/shopping/suggest body."""
    user_id: str
    budget_limit: Optional[float] = None


# ── Response Schemas ───────────────────────────────────────────────────

class SuggestedMeal(BaseModel):
    title: str
    description: str
    pantry_ingredients_used: list[str] = Field(default_factory=list)
    missing_ingredients: list[str] = Field(default_factory=list)
    prep_time_minutes: Optional[int] = None
    why_suggested: str = ""


class MealSuggestResponse(BaseModel):
    meals: list[SuggestedMeal] = Field(default_factory=list)


class ShoppingItem(BaseModel):
    canonical_item_id: str
    canonical_name: str
    current_quantity: float
    threshold_quantity: float
    estimated_days_left: Optional[float] = None
    cheapest_store: Optional[str] = None
    estimated_price: Optional[float] = None


class ShoppingSuggestResponse(BaseModel):
    must_buy_now: list[ShoppingItem] = Field(default_factory=list)
    buy_soon: list[ShoppingItem] = Field(default_factory=list)
