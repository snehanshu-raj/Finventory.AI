"""Gmail integration request/response schemas."""

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


# ── Request Schemas ────────────────────────────────────────────────────

class GmailConnectRequest(BaseModel):
    """POST /api/v1/integrations/gmail/connect"""
    user_id: str
    auth_code: str
    redirect_uri: Optional[str] = None


class EmailExpenseReviewRequest(BaseModel):
    """PATCH /api/v1/email-expenses/{id}/review"""
    merchant: Optional[str] = None
    amount: Optional[float] = None
    currency: Optional[str] = None
    category: Optional[str] = None
    expense_type: Optional[str] = None
    transaction_at: Optional[datetime] = None


# ── Response Schemas ───────────────────────────────────────────────────

class GmailStatusResponse(BaseModel):
    connected: bool
    email: Optional[str] = None
    sync_enabled: bool = False
    last_synced_at: Optional[datetime] = None


class SyncSummaryResponse(BaseModel):
    messages_found: int = 0
    messages_parsed: int = 0
    messages_stored: int = 0
    errors: list[str] = Field(default_factory=list)
    expenses: list[dict] = Field(default_factory=list)


class SyncRunResponse(BaseModel):
    id: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    status: str
    query_used: str
    messages_found: int
    messages_parsed: int
    messages_stored: int
    errors: list[str] = Field(default_factory=list)


class EmailExpenseResponse(BaseModel):
    id: str
    user_id: str
    gmail_message_id: str
    source: str = "gmail"
    sender: str
    subject: str
    snippet: str
    received_at: Optional[datetime] = None
    expense_type: str
    merchant: str
    normalized_merchant: str
    amount: float
    currency: str
    tax: Optional[float] = None
    transaction_at: Optional[datetime] = None
    category: str
    payment_method: Optional[str] = None
    confidence: float
    parsing_status: str
    review: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
