"""Email expense routes – list, detail, review for Gmail-parsed expenses."""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query
from fastapi.exceptions import HTTPException

from app.repositories.gmail_repository import email_expense_repo
from app.schemas.gmail import EmailExpenseReviewRequest
from app.utils.deps import get_user_id
from app.utils.exceptions import NotFoundException
from app.utils.response import success_response

router = APIRouter()


def _to_response(doc: dict) -> dict:
    """Convert MongoDB doc to API response."""
    return {
        "id": str(doc.get("_id", "")),
        "user_id": doc.get("userId", ""),
        "gmail_message_id": doc.get("gmailMessageId", ""),
        "source": "gmail",
        "sender": doc.get("sender", ""),
        "subject": doc.get("subject", ""),
        "snippet": doc.get("snippet", ""),
        "received_at": doc.get("receivedAt"),
        "expense_type": doc.get("expenseType", "other"),
        "merchant": doc.get("merchant", ""),
        "normalized_merchant": doc.get("normalizedMerchant", ""),
        "amount": doc.get("amount", 0),
        "currency": doc.get("currency", "USD"),
        "tax": doc.get("tax"),
        "transaction_at": doc.get("transactionAt"),
        "category": doc.get("category", "other"),
        "payment_method": doc.get("paymentMethod"),
        "confidence": doc.get("confidence", 0),
        "parsing_status": doc.get("parsingStatus", "parsed"),
        "review": doc.get("review", {}),
        "raw_text": doc.get("rawText", ""),
        "created_at": doc.get("createdAt"),
    }


@router.get("")
async def list_email_expenses(
    user_id: str = Depends(get_user_id),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    category: Optional[str] = None,
    from_date: Optional[datetime] = None,
    to_date: Optional[datetime] = None,
    merchant: Optional[str] = None,
):
    """List Gmail-derived expenses only."""
    docs, total = await email_expense_repo.find_by_user(
        user_id, page, page_size, category, from_date, to_date, merchant,
    )
    return success_response({
        "items": [_to_response(d) for d in docs],
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total": total,
            "total_pages": (total + page_size - 1) // page_size,
        },
    })


@router.get("/{email_expense_id}")
async def get_email_expense(email_expense_id: str):
    """Return one email expense with full details."""
    doc = await email_expense_repo.find_by_id(email_expense_id)
    if not doc:
        raise NotFoundException(f"Email expense {email_expense_id} not found")
    return success_response(_to_response(doc))


@router.patch("/{email_expense_id}/review")
async def review_email_expense(email_expense_id: str, body: EmailExpenseReviewRequest):
    """Correct/review a parsed email expense."""
    doc = await email_expense_repo.find_by_id(email_expense_id)
    if not doc:
        raise NotFoundException(f"Email expense {email_expense_id} not found")

    update: dict = {
        "review.reviewed": True,
        "review.reviewedAt": datetime.utcnow(),
        "review.needsHumanReview": False,
        "parsingStatus": "parsed",
    }

    if body.merchant is not None:
        update["merchant"] = body.merchant
        update["normalizedMerchant"] = body.merchant.lower().replace("'", "").replace("  ", " ")
    if body.amount is not None:
        update["amount"] = body.amount
    if body.currency is not None:
        update["currency"] = body.currency
    if body.category is not None:
        update["category"] = body.category
    if body.expense_type is not None:
        update["expenseType"] = body.expense_type
    if body.transaction_at is not None:
        update["transactionAt"] = body.transaction_at

    updated = await email_expense_repo.update(email_expense_id, update)
    return success_response(_to_response(updated), "Email expense reviewed")


@router.delete("/{email_expense_id}")
async def delete_email_expense(
    email_expense_id: str,
    user_id: str = Depends(get_user_id),
):
    """Delete a specific Gmail expense by ID."""
    doc = await email_expense_repo.find_by_id(email_expense_id)
    if not doc:
        raise NotFoundException(f"Email expense {email_expense_id} not found")
    
    # Verify the expense belongs to the requesting user
    if doc.get("userId") != user_id:
        raise HTTPException(status_code=403, detail="Unauthorized to delete this expense")
    
    deleted = await email_expense_repo.delete_by_id(email_expense_id)
    if not deleted:
        raise NotFoundException(f"Failed to delete email expense {email_expense_id}")
    
    return success_response({"deleted": True}, "Email expense deleted successfully")
