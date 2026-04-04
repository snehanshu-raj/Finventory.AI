"""Receipt-related request/response schemas."""

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


# ── Extracted receipt schema (from OCR/LLM) ────────────────────────────

class ExtractedMerchant(BaseModel):
    name: str = ""
    address: Optional[str] = None
    phone: Optional[str] = None


class ExtractedTransaction(BaseModel):
    receipt_number: Optional[str] = None
    purchased_at: Optional[datetime] = None
    currency: str = "USD"
    subtotal: float = 0.0
    tax: float = 0.0
    tip: float = 0.0
    total: float = 0.0
    payment_method: Optional[str] = None


class ExtractedLineItem(BaseModel):
    raw_text: str = ""
    canonical_name: str = ""
    category: Optional[str] = None
    brand: Optional[str] = None
    quantity: float = 1.0
    unit: str = "count"
    normalized_quantity: Optional[float] = None
    normalized_unit: Optional[str] = None
    line_price: float = 0.0
    unit_price: Optional[float] = None
    confidence: float = 0.0
    is_grocery: bool = True


class ExtractedReceipt(BaseModel):
    """Schema returned by the OCR/LLM extraction pipeline."""
    merchant: ExtractedMerchant = Field(default_factory=ExtractedMerchant)
    transaction: ExtractedTransaction = Field(default_factory=ExtractedTransaction)
    items: list[ExtractedLineItem] = Field(default_factory=list)


# ── Request schemas ────────────────────────────────────────────────────

class ReceiptReviewRequest(BaseModel):
    """PATCH /api/v1/receipts/{receipt_id}/review body."""
    merchant_name: Optional[str] = None
    items: Optional[list[ExtractedLineItem]] = None
    transaction: Optional[ExtractedTransaction] = None


# ── Response schemas ───────────────────────────────────────────────────

class LineItemResponse(BaseModel):
    raw_text: str
    canonical_item_id: Optional[str] = None
    canonical_name: Optional[str] = None
    category: Optional[str] = None
    brand: Optional[str] = None
    quantity: float
    unit: str
    normalized_quantity: Optional[float] = None
    normalized_unit: Optional[str] = None
    unit_price: Optional[float] = None
    line_price: float
    confidence: float
    is_grocery: bool


class MerchantResponse(BaseModel):
    name: str
    normalized_name: str
    store_id: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None


class TransactionResponse(BaseModel):
    receipt_number: Optional[str] = None
    purchased_at: Optional[datetime] = None
    currency: str
    subtotal: float
    tax: float
    tip: float
    total: float
    payment_method: Optional[str] = None


class ReceiptResponse(BaseModel):
    """Full receipt in API responses."""
    id: str
    user_id: str
    merchant: MerchantResponse
    transaction: TransactionResponse
    items: list[LineItemResponse]
    totals: dict[str, int]
    review: dict[str, Any]
    image_url: Optional[str] = None
    created_at: Optional[datetime] = None


class ReceiptListItem(BaseModel):
    """Abbreviated receipt for list views."""
    id: str
    merchant_name: str
    total: float
    item_count: int
    purchased_at: Optional[datetime] = None
    image_url: Optional[str] = None
