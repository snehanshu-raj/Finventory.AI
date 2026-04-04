"""Meal and shopping suggestion routes."""

from fastapi import APIRouter

from app.schemas.meal import MealSuggestRequest, ShoppingSuggestRequest
from app.services.meal_service import meal_service
from app.utils.response import success_response

router = APIRouter()


@router.post("/meals/suggest")
async def suggest_meals(body: MealSuggestRequest):
    """Suggest meals from current pantry items."""
    result = await meal_service.suggest_meals(
        body.user_id,
        body.constraints.model_dump(),
    )
    return success_response(result)


@router.post("/shopping/suggest")
async def suggest_shopping(body: ShoppingSuggestRequest):
    """Generate smart shopping suggestions."""
    result = await meal_service.suggest_shopping(body.user_id, body.budget_limit)
    return success_response(result)
