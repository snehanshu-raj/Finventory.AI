"""User-related request/response schemas."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


# ── Sub-schemas ────────────────────────────────────────────────────────

class StapleConfigSchema(BaseModel):
    canonical_item_id: str
    canonical_name: str
    daily_consumption_estimate: float = Field(gt=0)
    unit: str
    threshold_quantity: float = Field(ge=0)


class HouseholdProfileSchema(BaseModel):
    household_size: int = Field(ge=1)
    adults: int = Field(ge=0)
    children: int = Field(ge=0)


class DietProfileSchema(BaseModel):
    staples: list[StapleConfigSchema] = Field(default_factory=list)


class PreferencesSchema(BaseModel):
    currency: str = "USD"
    locale: str = "en-US"
    notification_enabled: bool = True
    notification_channels: list[str] = Field(default_factory=lambda: ["in_app"])


# ── Request Schemas ────────────────────────────────────────────────────

class OnboardingRequest(BaseModel):
    """POST /api/v1/users/onboarding request body."""
    name: str
    email: str
    household_profile: HouseholdProfileSchema
    diet_profile: DietProfileSchema
    preferences: PreferencesSchema = Field(default_factory=PreferencesSchema)

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "name": "John",
                    "email": "john@example.com",
                    "household_profile": {
                        "household_size": 2,
                        "adults": 2,
                        "children": 0,
                    },
                    "diet_profile": {
                        "staples": [
                            {
                                "canonical_item_id": "milk",
                                "canonical_name": "milk",
                                "daily_consumption_estimate": 0.5,
                                "unit": "liter",
                                "threshold_quantity": 1.0,
                            }
                        ]
                    },
                    "preferences": {
                        "currency": "USD",
                        "locale": "en-US",
                        "notification_enabled": True,
                        "notification_channels": ["in_app"],
                    },
                }
            ]
        }
    }


class UpdateStaplesRequest(BaseModel):
    """PATCH /api/v1/users/{user_id}/staples request body."""
    staples: list[StapleConfigSchema]


# ── Response Schemas ───────────────────────────────────────────────────

class UserResponse(BaseModel):
    """User data in API responses."""
    id: str
    email: str
    name: str
    created_at: datetime
    updated_at: datetime
    household_profile: HouseholdProfileSchema
    diet_profile: DietProfileSchema
    preferences: PreferencesSchema
