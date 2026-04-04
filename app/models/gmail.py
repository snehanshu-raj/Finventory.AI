"""Gmail-related domain models."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


# ── Linked Account ─────────────────────────────────────────────────────

class LinkedAccountModel(BaseModel):
    """Gmail connection metadata stored in `linked_accounts`."""
    userId: str
    provider: str = "gmail"
    email: str
    scopes: list[str] = Field(default_factory=lambda: ["https://www.googleapis.com/auth/gmail.readonly"])
    accessToken: str = ""
    refreshToken: str = ""
    tokenExpiry: Optional[datetime] = None
    lastSyncedAt: Optional[datetime] = None
    syncEnabled: bool = True
    createdAt: datetime = Field(default_factory=datetime.utcnow)
    updatedAt: datetime = Field(default_factory=datetime.utcnow)


# ── Email Expense ──────────────────────────────────────────────────────

class EmailExpenseReview(BaseModel):
    needsHumanReview: bool = False
    reviewed: bool = False
    reviewedAt: Optional[datetime] = None


class EmailExpenseModel(BaseModel):
    """Parsed expense from a Gmail message, stored in `email_expenses`."""
    userId: str
    gmailMessageId: str
    gmailThreadId: Optional[str] = None
    gmailLabelIds: list[str] = Field(default_factory=list)
    source: str = "gmail"
    sender: str = ""
    subject: str = ""
    snippet: str = ""
    receivedAt: Optional[datetime] = None
    messageDate: Optional[datetime] = None
    expenseType: str = "other"  # zelle, card_alert, order_receipt, invoice, subscription, ride_share, food_delivery, other
    merchant: str = ""
    normalizedMerchant: str = ""
    amount: float = 0.0
    currency: str = "USD"
    tax: Optional[float] = None
    transactionAt: Optional[datetime] = None
    category: str = "other"
    paymentMethod: Optional[str] = None
    confidence: float = 0.0
    rawText: str = ""
    rawHtml: Optional[str] = None
    attachmentsMeta: list[dict] = Field(default_factory=list)
    parsingStatus: str = "parsed"  # parsed, needs_review, ignored, failed
    review: EmailExpenseReview = Field(default_factory=EmailExpenseReview)
    createdAt: datetime = Field(default_factory=datetime.utcnow)
    updatedAt: datetime = Field(default_factory=datetime.utcnow)


# ── Sync Run ───────────────────────────────────────────────────────────

class EmailSyncRunModel(BaseModel):
    """Tracks a single Gmail sync execution in `email_sync_runs`."""
    userId: str
    startedAt: datetime = Field(default_factory=datetime.utcnow)
    completedAt: Optional[datetime] = None
    status: str = "running"  # running, completed, failed
    queryUsed: str = ""
    messagesFound: int = 0
    messagesParsed: int = 0
    messagesStored: int = 0
    errors: list[str] = Field(default_factory=list)
