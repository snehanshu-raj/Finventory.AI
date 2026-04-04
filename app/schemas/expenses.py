"""Unified expense schemas – merge receipts + email expenses."""

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class UnifiedExpenseResponse(BaseModel):
    """Single expense from either receipt or Gmail."""
    id: str
    source: str  # "receipt" or "gmail"
    source_id: str  # receipt_id or gmail_message_id
    merchant: str
    normalized_merchant: str
    amount: float
    currency: str = "USD"
    transaction_at: Optional[datetime] = None
    category: Optional[str] = None
    payment_method: Optional[str] = None
    expense_type: Optional[str] = None
    confidence: float = 0.0
    meta: dict[str, Any] = Field(default_factory=dict)


class UnifiedExpenseSummaryResponse(BaseModel):
    """Combined spend summary across receipts and emails."""
    total_today: float = 0.0
    total_this_month: float = 0.0
    by_source: dict[str, float] = Field(default_factory=dict)
    by_category: list[dict] = Field(default_factory=list)
    recent_merchants: list[str] = Field(default_factory=list)
    recent_expenses: list[UnifiedExpenseResponse] = Field(default_factory=list)
