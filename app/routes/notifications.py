"""Notification routes – list, test, and update APIs."""

from typing import Optional

from fastapi import APIRouter, Depends, Query

from app.schemas.notification import (
    CreateTestNotificationRequest,
    UpdateNotificationRequest,
)
from app.services.notification_service import notification_service
from app.utils.deps import get_user_id
from app.utils.response import success_response

router = APIRouter()


@router.get("")
async def list_notifications(
    user_id: str = Depends(get_user_id),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """List notifications for a user."""
    result = await notification_service.list_notifications(user_id, page, page_size)
    return success_response(result)


@router.post("/test")
async def create_test_notification(body: CreateTestNotificationRequest):
    """Create a mock test notification."""
    result = await notification_service.create_test(
        body.user_id, body.title, body.message
    )
    return success_response(result, "Test notification created")


@router.patch("/{notification_id}")
async def update_notification(notification_id: str, body: UpdateNotificationRequest):
    """Mark notification as dismissed or read."""
    result = await notification_service.update_notification(
        notification_id, body.status
    )
    return success_response(result, "Notification updated")
