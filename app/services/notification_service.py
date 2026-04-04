"""Notification service – alerts and reminder business logic."""

import logging
from datetime import datetime
from typing import Optional

from app.repositories.notification_repository import notification_repo
from app.utils.exceptions import NotFoundException

logger = logging.getLogger(__name__)


class NotificationService:
    """Business logic for notifications and alerts."""

    async def list_notifications(
        self, user_id: str, page: int = 1, page_size: int = 20
    ) -> dict:
        """List notifications for a user."""
        docs, total = await notification_repo.find_by_user(user_id, page, page_size)
        total_pages = (total + page_size - 1) // page_size if total else 0
        return {
            "items": [self._to_response(d) for d in docs],
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total": total,
                "total_pages": total_pages,
            },
        }

    async def create_test(self, user_id: str, title: str, message: str) -> dict:
        """Create a test notification."""
        doc = {
            "userId": user_id,
            "type": "low_stock",
            "title": title,
            "message": message,
            "status": "pending",
            "channel": "in_app",
            "context": {"test": True},
            "createdAt": datetime.utcnow(),
        }
        nid = await notification_repo.insert(doc)
        doc["_id"] = nid

        # Simulate sending (mock email)
        await self._mock_send(doc)

        return self._to_response(doc)

    async def update_notification(self, notification_id: str, status: str) -> dict:
        """Update notification status (dismiss, mark sent, etc.)."""
        doc = await notification_repo.update_status(notification_id, status)
        if not doc:
            raise NotFoundException(f"Notification {notification_id} not found")
        return self._to_response(doc)

    async def _mock_send(self, notification: dict) -> None:
        """Simulate sending a notification (in-app or mock email)."""
        channel = notification.get("channel", "in_app")
        logger.info(
            "[%s] Notification sent: %s – %s",
            channel.upper(),
            notification.get("title", ""),
            notification.get("message", ""),
        )
        nid = notification.get("_id")
        if nid:
            await notification_repo.update_status(str(nid), "sent")

    @staticmethod
    def _to_response(doc: dict) -> dict:
        return {
            "id": str(doc.get("_id", "")),
            "user_id": doc.get("userId", ""),
            "type": doc.get("type", ""),
            "title": doc.get("title", ""),
            "message": doc.get("message", ""),
            "status": doc.get("status", ""),
            "channel": doc.get("channel", ""),
            "context": doc.get("context", {}),
            "created_at": doc.get("createdAt", datetime.utcnow()),
            "sent_at": doc.get("sentAt"),
        }


notification_service = NotificationService()
