"""Unified expense routes – merged receipts + email expenses."""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query

from app.services.unified_expense_service import unified_expense_service
from app.utils.deps import get_user_id
from app.utils.response import success_response

router = APIRouter()


@router.get("")
async def list_expenses(
    user_id: str = Depends(get_user_id),
    source: str = Query("all", regex="^(all|receipt|gmail)$"),
    category: Optional[str] = None,
    from_date: Optional[datetime] = None,
    to_date: Optional[datetime] = None,
    merchant: Optional[str] = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    """Return unified expense feed from all sources."""
    result = await unified_expense_service.list_expenses(
        user_id=user_id,
        source=source,
        category=category,
        from_date=from_date,
        to_date=to_date,
        merchant=merchant,
        limit=limit,
        offset=offset,
    )
    return success_response(result)


@router.get("/summary")
async def expense_summary(user_id: str = Depends(get_user_id)):
    """Combined expense summary across receipts and emails."""
    result = await unified_expense_service.get_summary(user_id)
    return success_response(result)


@router.get("/{expense_id}")
async def get_expense(expense_id: str):
    """Get single expense by prefixed ID (gmail_<id> or receipt_<id>)."""
    result = await unified_expense_service.get_expense(expense_id)
    return success_response(result)
