"""Receipt domain models."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ReceiptSource(BaseModel):
    """Upload and OCR metadata."""
    filename: str = ""
    content_type: str = ""
    storage_path: str = ""
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)
    ocr_provider: str = ""
    ocr_status: str = "pending"
    ocr_confidence: Optional[float] = None
    raw_text: Optional[str] = None


class Merchant(BaseModel):
    """Merchant / store information."""
    name: str = ""
    normalized_name: str = ""
    store_id: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None


class Transaction(BaseModel):
    """Transaction-level totals."""
    receipt_number: Optional[str] = None
    purchased_at: Optional[datetime] = None
    currency: str = "USD"
    subtotal: float = 0.0
    tax: float = 0.0
    tip: float = 0.0
    total: float = 0.0
    payment_method: Optional[str] = None


class ReceiptLineItem(BaseModel):
    """A single line item extracted from a receipt."""
    raw_text: str = ""
    canonical_item_id: Optional[str] = None
    canonical_name: Optional[str] = None
    category: Optional[str] = None
    brand: Optional[str] = None
    quantity: float = 1.0
    unit: str = "count"
    normalized_quantity: Optional[float] = None
    normalized_unit: Optional[str] = None
    unit_price: Optional[float] = None
    line_price: float = 0.0
    confidence: float = 0.0
    is_grocery: bool = True


class ReceiptTotals(BaseModel):
    """Aggregated receipt-level counts."""
    item_count: int = 0
    grocery_items_count: int = 0
    non_grocery_items_count: int = 0


class ReceiptDerived(BaseModel):
    """Derived / computed flags."""
    month_bucket: Optional[str] = None
    price_observation_created: bool = False
    inventory_applied: bool = False


class ReceiptReview(BaseModel):
    """Human review status."""
    needs_human_review: bool = False
    reviewed: bool = False
    reviewed_at: Optional[datetime] = None


class Receipt(BaseModel):
    """Receipt document model matching the MongoDB `receipts` collection."""
    id: Optional[str] = Field(None, alias="_id")
    user_id: str
    source: ReceiptSource = Field(default_factory=ReceiptSource)
    merchant: Merchant = Field(default_factory=Merchant)
    transaction: Transaction = Field(default_factory=Transaction)
    items: list[ReceiptLineItem] = Field(default_factory=list)
    totals: ReceiptTotals = Field(default_factory=ReceiptTotals)
    derived: ReceiptDerived = Field(default_factory=ReceiptDerived)
    review: ReceiptReview = Field(default_factory=ReceiptReview)

    model_config = {"populate_by_name": True}
