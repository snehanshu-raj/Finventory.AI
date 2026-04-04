"""Gmail integration routes – sync and management."""

from fastapi import APIRouter, Depends, Query

from app.services.gmail_auth_service import gmail_auth_service
from app.services.gmail_sync_service import gmail_sync_service
from app.utils.deps import get_user_id
from app.utils.response import success_response

router = APIRouter()


@router.get("/gmail/status")
async def gmail_status(user_id: str = Depends(get_user_id)):
    """Check Gmail connection status."""
    result = await gmail_auth_service.get_status(user_id)
    return success_response(result)


@router.post("/gmail/sync")
async def sync_gmail(
    user_id: str = Depends(get_user_id),
    days_back: int = Query(0, ge=0, le=90),
):
    """Trigger sync of expense emails. days_back=0 means today only, 7 means last week, etc."""
    result = await gmail_sync_service.sync_emails(user_id, days_back=days_back)
    return success_response(result, "Gmail sync completed")


@router.post("/gmail/fetch-and-preview")
async def fetch_and_preview(
    user_id: str = Depends(get_user_id),
    days_back: int = Query(0, ge=0, le=90),
):
    """Fetch emails, parse expenses, store to DB, and return what was found."""
    result = await gmail_sync_service.fetch_and_preview(user_id, days_back=days_back)
    return success_response(result, f"Found {result['messages_found']} emails, stored {result['messages_stored']} expenses")


@router.get("/gmail/sync-runs")
async def get_sync_runs(
    user_id: str = Depends(get_user_id),
    limit: int = Query(10, ge=1, le=50),
):
    """Return recent sync run history."""
    runs = await gmail_sync_service.get_sync_runs(user_id, limit)
    return success_response(runs)


@router.delete("/gmail/email-expenses/reset")
async def reset_email_expenses(user_id: str = Depends(get_user_id)):
    """Delete ALL email expenses for a user (testing reset)."""
    result = await gmail_sync_service.delete_all_email_expenses(user_id)
    return success_response(result, "Email expenses reset successfully")
