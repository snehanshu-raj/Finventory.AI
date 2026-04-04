"""Analytics-related response schemas."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


# ── Predictions ────────────────────────────────────────────────────────

class PredictionItem(BaseModel):
    canonical_item_id: str
    canonical_name: str
    current_quantity: float
    daily_consumption_estimate: float
    estimated_days_left: Optional[float] = None
    predicted_run_out_date: Optional[datetime] = None
    status: str


# ── Expense Summary ───────────────────────────────────────────────────

class StoreSummary(BaseModel):
    store_name: str
    total_spend: float
    receipt_count: int


class CategorySummary(BaseModel):
    category: str
    total_spend: float
    item_count: int


class TopSpendItem(BaseModel):
    canonical_name: str
    total_spend: float
    purchase_count: int


class ExpenseSummaryResponse(BaseModel):
    current_month_total: float = 0.0
    previous_month_total: float = 0.0
    by_store: list[StoreSummary] = Field(default_factory=list)
    by_category: list[CategorySummary] = Field(default_factory=list)
    top_spend_items: list[TopSpendItem] = Field(default_factory=list)


# ── Price Insights ─────────────────────────────────────────────────────

class StorePrice(BaseModel):
    store_name: str
    avg_unit_price: float
    samples: int
    last_seen: Optional[datetime] = None


class BestStoreResponse(BaseModel):
    canonical_item_id: str
    canonical_name: str
    best_store: Optional[str] = None
    stores: list[StorePrice] = Field(default_factory=list)
    confidence: Optional[float] = None
    insight: Optional[str] = None


class PriceCompareResponse(BaseModel):
    canonical_item_id: str
    canonical_name: str
    stores: list[StorePrice] = Field(default_factory=list)


# ── Dashboard ──────────────────────────────────────────────────────────

class DashboardResponse(BaseModel):
    monthly_spend: float = 0.0
    low_stock_count: int = 0
    items_running_out_7days: list[PredictionItem] = Field(default_factory=list)
    top_stores: list[StoreSummary] = Field(default_factory=list)
    savings_opportunities: list[BestStoreResponse] = Field(default_factory=list)
