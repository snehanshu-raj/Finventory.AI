"""Shared FastAPI dependencies."""

from typing import Optional

from fastapi import Query

from app.config import settings
from app.utils.exceptions import ValidationException


def get_user_id(user_id: Optional[str] = Query(None)) -> str:
    """Resolve user ID: use query param if given, else fall back to DEFAULT_USER_ID."""
    uid = user_id or settings.default_user_id
    if not uid:
        raise ValidationException("user_id is required (or set DEFAULT_USER_ID in .env)")
    return uid
