"""Analytics routes – predictions, expenses, prices, and dashboard APIs."""

from typing import Optional

from fastapi import APIRouter, Depends, Query

from app.services.analytics_service import analytics_service
from app.utils.deps import get_user_id
from app.utils.response import success_response

router = APIRouter()


@router.get("/predictions", tags=["Predictions"])
async def get_predictions(user_id: str = Depends(get_user_id)):
    """Return predicted run-out timeline for all inventory items."""
    result = await analytics_service.get_predictions(user_id)
    return success_response(result)


@router.get("/expenses/summary")
async def expense_summary(user_id: str = Depends(get_user_id)):
    """Return spending summary by month, store, category, and top items."""
    result = await analytics_service.get_expense_summary(user_id)
    return success_response(result)


@router.get("/prices/best-store")
async def best_store(
    user_id: str = Depends(get_user_id),
    item: str = Query(..., description="canonical item id, e.g. eggs"),
    window: str = Query("30d"),
):
    """Return best store insight for an item."""
    result = await analytics_service.get_best_store(user_id, item, window)
    return success_response(result)


@router.get("/prices/compare")
async def compare_prices(
    user_id: str = Depends(get_user_id),
    item: str = Query(...),
    window: str = Query("30d"),
):
    """Return multi-store price comparison for an item."""
    result = await analytics_service.compare_prices(user_id, item, window)
    return success_response(result)


@router.get("/dashboard")
async def dashboard(user_id: str = Depends(get_user_id)):
    """Combined dashboard response."""
    result = await analytics_service.get_dashboard(user_id)
    return success_response(result)
