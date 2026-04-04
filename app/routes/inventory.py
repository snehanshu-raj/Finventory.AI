"""Inventory routes – pantry state and adjustment APIs."""

from typing import Optional

from fastapi import APIRouter, Depends, Query

from app.schemas.inventory import ManualAdjustmentRequest
from app.services.inventory_service import inventory_service
from app.utils.deps import get_user_id
from app.utils.response import success_response

router = APIRouter()


@router.get("")
async def list_inventory(
    user_id: str = Depends(get_user_id),
    status: Optional[str] = Query(None, description="ok|low|critical|out_of_stock"),
    category: Optional[str] = Query(None),
    sort_by: Optional[str] = Query(None, description="estimatedDaysLeft|currentQuantity|name"),
):
    """Return all current inventory items for the user."""
    result = await inventory_service.get_all_items(
        user_id, status=status, category=category, sort_by=sort_by
    )
    return success_response(result)


@router.get("/low-stock")
async def low_stock(user_id: str = Depends(get_user_id)):
    """Return only low, critical, and out-of-stock items."""
    result = await inventory_service.get_low_stock(user_id)
    return success_response(result)


@router.get("/{canonical_item_id}")
async def get_inventory_item(
    canonical_item_id: str,
    user_id: str = Depends(get_user_id),
):
    """Return one item's inventory state plus recent history."""
    result = await inventory_service.get_item_detail(user_id, canonical_item_id)
    return success_response(result)


@router.patch("/{canonical_item_id}")
async def adjust_inventory(
    canonical_item_id: str,
    body: ManualAdjustmentRequest,
    user_id: str = Depends(get_user_id),
):
    """Manual adjustment of inventory quantity."""
    result = await inventory_service.manual_adjust(
        user_id,
        canonical_item_id,
        body.current_quantity,
        body.unit,
        body.reason,
    )
    return success_response(result, "Inventory adjusted")


@router.delete("/reset")
async def reset_inventory(user_id: str = Depends(get_user_id)):
    """Delete ALL inventory states and events for a user. For testing only."""
    result = await inventory_service.reset_inventory(user_id)
    return success_response(result, "Inventory reset successfully")
