"""Inventory-related request/response schemas."""

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


# ── Request Schemas ────────────────────────────────────────────────────

class ManualAdjustmentRequest(BaseModel):
    """PATCH /api/v1/inventory/{canonical_item_id} body."""
    current_quantity: float = Field(ge=0)
    unit: str
    reason: str = "manual correction"


# ── Response Schemas ───────────────────────────────────────────────────

class InventoryItemResponse(BaseModel):
    """Single inventory item in responses."""
    canonical_item_id: str
    canonical_name: str
    category: Optional[str] = None
    current_quantity: float
    unit: str
    threshold_quantity: float
    daily_consumption_estimate: float
    estimated_days_left: Optional[float] = None
    status: str
    last_updated_at: datetime
    last_receipt_at: Optional[datetime] = None
    reminder_enabled: bool
    last_reminder_sent_at: Optional[datetime] = None


class InventoryEventResponse(BaseModel):
    """Single inventory event in responses."""
    id: str
    canonical_item_id: str
    canonical_name: str
    event_type: str
    delta_quantity: float
    unit: str
    created_at: datetime
    source: dict[str, Any] = Field(default_factory=dict)


class InventoryDetailResponse(BaseModel):
    """Detailed view of a single inventory item with history."""
    item: InventoryItemResponse
    recent_events: list[InventoryEventResponse] = Field(default_factory=list)
