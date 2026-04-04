"""User routes – onboarding and profile APIs."""

from fastapi import APIRouter, Depends

from app.schemas.user import OnboardingRequest, UpdateStaplesRequest
from app.services.user_service import user_service
from app.utils.deps import get_user_id
from app.utils.response import success_response

router = APIRouter()


@router.post("/onboarding")
async def onboard_user(body: OnboardingRequest):
    """Create or update user profile (uses DEFAULT_USER_ID)."""
    result = await user_service.onboard_user(body.model_dump())
    return success_response(result, "Onboarding completed")


@router.get("/profile")
async def get_user(user_id: str = Depends(get_user_id)):
    """Get current user profile and onboarding config."""
    result = await user_service.get_user(user_id)
    return success_response(result)


@router.patch("/staples")
async def update_staples(body: UpdateStaplesRequest, user_id: str = Depends(get_user_id)):
    """Update staple threshold or daily consumption settings."""
    staples = [s.model_dump() for s in body.staples]
    result = await user_service.update_staples(user_id, staples)
    return success_response(result, "Staples updated")
