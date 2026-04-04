"""Extraction service – OCR/LLM receipt extraction pipeline."""

import logging

from app.schemas.receipt import ExtractedReceipt
from app.services.llm_provider import get_llm_provider
from app.utils.exceptions import ExtractionException

logger = logging.getLogger(__name__)


class ReceiptExtractionService:
    """Extract structured receipt data from images using the configured LLM provider."""

    async def extract_receipt(self, file_path: str, content_type: str) -> ExtractedReceipt:
        """Read an image file and extract structured receipt data.

        Args:
            file_path: Path to the saved receipt image.
            content_type: MIME type of the image (e.g. image/jpeg).

        Returns:
            ExtractedReceipt with merchant, transaction, and line items.
        """
        try:
            with open(file_path, "rb") as f:
                image_bytes = f.read()

            provider = get_llm_provider()
            raw = await provider.vision_extract(image_bytes, content_type)
            logger.info("Extraction completed via %s", type(provider).__name__)

            # Validate and parse into schema
            return self._parse_extraction(raw)

        except ExtractionException:
            raise
        except Exception as e:
            logger.exception("Receipt extraction failed: %s", e)
            raise ExtractionException(f"Receipt extraction failed: {e}")

    def _parse_extraction(self, raw: dict) -> ExtractedReceipt:
        """Parse raw LLM output into an ExtractedReceipt schema."""
        try:
            merchant = raw.get("merchant", {})
            transaction = raw.get("transaction", {})
            items = raw.get("items", [])

            return ExtractedReceipt(
                merchant={
                    "name": merchant.get("name", ""),
                    "address": merchant.get("address"),
                    "phone": merchant.get("phone"),
                },
                transaction={
                    "receipt_number": transaction.get("receiptNumber"),
                    "purchased_at": transaction.get("purchasedAt"),
                    "currency": transaction.get("currency", "USD"),
                    "subtotal": transaction.get("subtotal", 0),
                    "tax": transaction.get("tax", 0),
                    "tip": transaction.get("tip", 0),
                    "total": transaction.get("total", 0),
                    "payment_method": transaction.get("paymentMethod"),
                },
                items=[
                    {
                        "raw_text": item.get("rawText", ""),
                        "canonical_name": item.get("canonicalName", ""),
                        "category": item.get("category"),
                        "brand": item.get("brand"),
                        "quantity": item.get("quantity", 1),
                        "unit": item.get("unit", "count"),
                        "normalized_quantity": item.get("normalizedQuantity"),
                        "normalized_unit": item.get("normalizedUnit"),
                        "line_price": item.get("linePrice", 0),
                        "unit_price": item.get("unitPrice"),
                        "confidence": item.get("confidence", 0),
                        "is_grocery": item.get("isGrocery", True),
                    }
                    for item in items
                ],
            )
        except Exception as e:
            raise ExtractionException(f"Failed to parse extraction result: {e}")


extraction_service = ReceiptExtractionService()
