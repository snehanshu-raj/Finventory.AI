"""Receipt routes – upload, list, detail, and review APIs."""

from typing import Optional

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile

from app.schemas.receipt import ReceiptReviewRequest
from app.services.receipt_service import receipt_service
from app.utils.deps import get_user_id
from app.utils.response import success_response
from fastapi.responses import Response

router = APIRouter()


@router.post("/upload")
async def upload_receipt(
    file: UploadFile = File(...),
    user_id: str = Depends(get_user_id),
):
    """Upload a receipt image and extract structured data."""
    content = await file.read()
    result = await receipt_service.upload_receipt(
        user_id=user_id,
        filename=file.filename or "receipt.jpg",
        content_type=file.content_type or "image/jpeg",
        file_bytes=content,
    )
    return success_response(result, "Receipt processed successfully")


@router.get("")
async def list_receipts(
    user_id: str = Depends(get_user_id),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    month: Optional[str] = Query(None, description="e.g. 2026-04"),
    store: Optional[str] = Query(None),
):
    """List receipts with pagination and optional filters."""
    result = await receipt_service.list_receipts(user_id, page, page_size, month, store)
    return success_response(result)


@router.get("/{receipt_id}")
async def get_receipt(receipt_id: str):
    """Get full receipt details."""
    result = await receipt_service.get_receipt(receipt_id)
    return success_response(result)


@router.get("/{receipt_id}/image")
async def get_receipt_image(receipt_id: str):
    """Serve the receipt image file."""
    image_bytes, content_type = await receipt_service.get_receipt_image(receipt_id)
    return Response(content=image_bytes, media_type=content_type)


@router.patch("/{receipt_id}")
async def update_receipt(receipt_id: str, body: ReceiptReviewRequest):
    """Update receipt data (e.g. quantity or name) and sync inventory."""
    result = await receipt_service.review_receipt(receipt_id, body.model_dump())
    return success_response(result, "Receipt updated successfully")


@router.delete("/{receipt_id}")
async def delete_receipt(receipt_id: str):
    """Delete a receipt and reverse its inventory effects."""
    result = await receipt_service.delete_receipt(receipt_id)
    return success_response(result, "Receipt deleted")


@router.patch("/{receipt_id}/review")
async def review_receipt(receipt_id: str, body: ReceiptReviewRequest):
    """Legacy alias for review flow (legacy compatibility)."""
    result = await receipt_service.review_receipt(receipt_id, body.model_dump())
    return success_response(result, "Receipt reviewed and updated")
