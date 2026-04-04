"""Notification domain models."""

from datetime import datetime
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field


NotificationType = Literal["low_stock", "prediction_alert", "weekly_summary"]
NotificationStatus = Literal["pending", "sent", "dismissed", "failed"]


class Notification(BaseModel):
    """Notification / alert document.

    Matches the MongoDB `notifications` collection.
    """
    id: Optional[str] = Field(None, alias="_id")
    user_id: str
    type: NotificationType
    title: str
    message: str
    status: NotificationStatus = "pending"
    channel: str = "in_app"
    context: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    sent_at: Optional[datetime] = None

    model_config = {"populate_by_name": True}
