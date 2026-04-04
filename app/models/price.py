"""Price observation and insight models."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class PriceObservation(BaseModel):
    """Flattened normalized line-item observation for analytics.

    Matches the MongoDB `price_observations` collection.
    """
    id: Optional[str] = Field(None, alias="_id")
    user_id: str
    receipt_id: str
    canonical_item_id: str
    canonical_name: str
    canonical_category: Optional[str] = None
    store_name: str = ""
    store_id: Optional[str] = None
    purchased_at: Optional[datetime] = None
    quantity: float = 1.0
    unit: str = "count"
    normalized_quantity: Optional[float] = None
    normalized_unit: Optional[str] = None
    line_price: float = 0.0
    unit_price: Optional[float] = None
    promo_flag: bool = False
    brand: Optional[str] = None
    confidence: float = 0.0

    model_config = {"populate_by_name": True}


class StoreInsight(BaseModel):
    """Per-store price summary inside a price insight."""
    store_name: str
    avg_unit_price: float
    samples: int
    last_seen: Optional[datetime] = None


class PriceInsight(BaseModel):
    """Precomputed store-level summary per item.

    Matches the MongoDB `price_insights` collection.
    """
    id: Optional[str] = Field(None, alias="_id")
    user_id: str
    canonical_item_id: str
    canonical_name: str
    window: str = "30d"
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    stores: list[StoreInsight] = Field(default_factory=list)
    best_store: Optional[str] = None
    confidence: Optional[float] = None
    insight: Optional[str] = None

    model_config = {"populate_by_name": True}
