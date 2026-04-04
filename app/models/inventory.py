"""Inventory domain models."""

from datetime import datetime
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field


InventoryStatus = Literal["ok", "low", "critical", "out_of_stock"]
EventType = Literal[
    "purchase",
    "daily_decrement",
    "manual_adjustment",
    "receipt_deleted",
    "consumption_correction",
    "waste_discarded",
]


class InventoryMetadata(BaseModel):
    """Extra metadata on an inventory state document."""
    source_confidence: Optional[float] = None
    last_purchase_store: Optional[str] = None
    last_purchase_price: Optional[float] = None


class InventoryState(BaseModel):
    """Current pantry state for one user-item pair.

    Matches the MongoDB `inventory_state` collection.
    """
    id: Optional[str] = Field(None, alias="_id")
    user_id: str
    canonical_item_id: str
    canonical_name: str
    category: Optional[str] = None
    current_quantity: float = 0.0
    unit: str = "count"
    threshold_quantity: float = 0.0
    daily_consumption_estimate: float = 0.0
    estimated_days_left: Optional[float] = None
    status: InventoryStatus = "ok"
    last_updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_receipt_at: Optional[datetime] = None
    reminder_enabled: bool = True
    last_reminder_sent_at: Optional[datetime] = None
    metadata: InventoryMetadata = Field(default_factory=InventoryMetadata)

    model_config = {"populate_by_name": True}


class EventSource(BaseModel):
    """Source reference for an inventory event."""
    type: str = ""
    reference_id: Optional[str] = None


class InventoryEvent(BaseModel):
    """Append-only event log entry for inventory changes.

    Matches the MongoDB `inventory_events` collection.
    """
    id: Optional[str] = Field(None, alias="_id")
    user_id: str
    canonical_item_id: str
    canonical_name: str
    event_type: EventType
    delta_quantity: float
    unit: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    source: EventSource = Field(default_factory=EventSource)
    meta: dict[str, Any] = Field(default_factory=dict)

    model_config = {"populate_by_name": True}
