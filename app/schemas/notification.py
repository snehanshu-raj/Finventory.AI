"""Notification-related schemas."""

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel


class NotificationResponse(BaseModel):
    """Notification in API responses."""
    id: str
    user_id: str
    type: str
    title: str
    message: str
    status: str
    channel: str
    context: dict[str, Any] = {}
    created_at: datetime
    sent_at: Optional[datetime] = None


class CreateTestNotificationRequest(BaseModel):
    """POST /api/v1/notifications/test body."""
    user_id: str
    title: str = "Test Notification"
    message: str = "This is a test notification."


class UpdateNotificationRequest(BaseModel):
    """PATCH /api/v1/notifications/{notification_id} body."""
    status: str  # e.g. "dismissed", "sent"
