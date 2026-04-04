"""User domain models."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class StapleConfig(BaseModel):
    """Single staple consumption configuration."""
    canonical_item_id: str
    canonical_name: str
    daily_consumption_estimate: float
    unit: str
    threshold_quantity: float


class HouseholdProfile(BaseModel):
    """Household size information."""
    household_size: int = 1
    adults: int = 1
    children: int = 0


class DietProfile(BaseModel):
    """Diet and staple consumption profile."""
    staples: list[StapleConfig] = Field(default_factory=list)


class UserPreferences(BaseModel):
    """User preferences for currency, locale, and notifications."""
    currency: str = "USD"
    locale: str = "en-US"
    notification_enabled: bool = True
    notification_channels: list[str] = Field(default_factory=lambda: ["in_app"])


class User(BaseModel):
    """User document model matching the MongoDB `users` collection."""
    id: Optional[str] = Field(None, alias="_id")
    email: str
    name: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    household_profile: HouseholdProfile = Field(default_factory=HouseholdProfile)
    diet_profile: DietProfile = Field(default_factory=DietProfile)
    preferences: UserPreferences = Field(default_factory=UserPreferences)

    model_config = {"populate_by_name": True}
