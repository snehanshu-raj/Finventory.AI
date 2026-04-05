"""Receipt service – upload, extraction, and correction orchestration."""

import logging
from datetime import datetime
from typing import Optional

from app.repositories.receipt_repository import receipt_repo
from app.repositories.price_repository import price_repo
from app.services.extraction_service import extraction_service
from app.services.inventory_service import inventory_service
from app.utils.exceptions import NotFoundException, ValidationException
from app.utils.storage import storage

logger = logging.getLogger(__name__)

ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/jpg", "image/png", "image/webp"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


def _detect_image_type(file_bytes: bytes) -> str:
    """Detect actual image format from magic bytes."""
    if len(file_bytes) < 4:
        return "image/jpeg"  # default
    
    # Check magic bytes (file signatures)
    if file_bytes[:3] == b'\xff\xd8\xff':  # JPEG
        return "image/jpeg"
    elif file_bytes[:8] == b'\x89PNG\r\n\x1a\n':  # PNG
        return "image/png"
    elif file_bytes[:4] == b'RIFF' and file_bytes[8:12] == b'WEBP':  # WebP
        return "image/webp"
    elif file_bytes[:6] == b'GIF87a' or file_bytes[:6] == b'GIF89a':  # GIF
        return "image/gif"
    
    return "image/jpeg"  # default fallback


class ReceiptService:
    """Orchestrates receipt upload ➜ extraction ➜ storage ➜ downstream effects."""

    async def upload_receipt(
        self,
        user_id: str,
        filename: str,
        content_type: str,
        file_bytes: bytes,
    ) -> dict:
        """Full upload pipeline: save ➜ extract ➜ store ➜ inventory ➜ prices."""
        # Detect actual image format from magic bytes
        actual_content_type = _detect_image_type(file_bytes)
        if actual_content_type != content_type:
            logger.info(
                "Content-type mismatch: declared=%s, actual=%s, using actual",
                content_type, actual_content_type
            )
            content_type = actual_content_type
        
        # Validate
        if content_type not in ALLOWED_CONTENT_TYPES:
            raise ValidationException(
                f"Invalid file type '{content_type}'. Allowed: {', '.join(ALLOWED_CONTENT_TYPES)}."
            )
        if len(file_bytes) > MAX_FILE_SIZE:
            raise ValidationException(
                f"File too large ({len(file_bytes)} bytes). Max: {MAX_FILE_SIZE}."
            )

        # Save file
        storage_path = await storage.save(filename, file_bytes)

        try:
            # Extract via LLM/OCR
            extracted = await extraction_service.extract_receipt(storage_path, content_type)
        except Exception as e:
            logger.error("Extraction failed for %s: %s", storage_path, e)
            from app.utils.exceptions import ValidationException
            raise ValidationException(f"LLM extraction failed: {str(e)}")

        # Normalize merchant name
        merchant_name = extracted.merchant.name
        normalized_name = merchant_name.strip().lower().replace("'", "").replace("  ", " ")

        # Build receipt document
        now = datetime.utcnow()
        
        # Validate extracted date – use today if extraction is too old or in future
        extracted_date = extracted.transaction.purchased_at
        if extracted_date:
            # Check if date is unreasonable (more than 5 years old or in the future)
            days_old = (now - extracted_date).days
            if days_old > 1825 or days_old < 0:  # 5 years = ~1825 days
                logger.warning(
                    "Extracted date %s is unreasonable (days_old=%d), using upload date %s",
                    extracted_date, days_old, now
                )
                purchased_at = now
            else:
                purchased_at = extracted_date
        else:
            purchased_at = now
        
        month_bucket = purchased_at.strftime("%Y-%m")
        items_data = [item.model_dump() for item in extracted.items]

        grocery_count = sum(1 for i in extracted.items if i.is_grocery)
        non_grocery_count = len(extracted.items) - grocery_count
        needs_review = any(i.confidence < 0.7 for i in extracted.items)

        receipt_doc = {
            "userId": user_id,
            "source": {
                "filename": filename,
                "contentType": content_type,
                "storagePath": storage_path,
                "uploadedAt": now,
                "ocrProvider": "llm",
                "ocrStatus": "completed",
                "ocrConfidence": (
                    sum(i.confidence for i in extracted.items) / len(extracted.items)
                    if extracted.items else 0
                ),
                "rawText": None,
            },
            "merchant": {
                "name": merchant_name,
                "normalizedName": normalized_name,
                "storeId": None,
                "address": extracted.merchant.address,
                "phone": extracted.merchant.phone,
            },
            "transaction": {
                "receiptNumber": extracted.transaction.receipt_number,
                "purchasedAt": purchased_at,
                "currency": extracted.transaction.currency,
                "subtotal": extracted.transaction.subtotal,
                "tax": extracted.transaction.tax,
                "tip": extracted.transaction.tip,
                "total": extracted.transaction.total,
                "paymentMethod": extracted.transaction.payment_method,
            },
            "items": [
                {
                    "rawText": item.raw_text,
                    "canonicalItemId": item.canonical_name.lower().replace(" ", "_"),
                    "canonicalName": item.canonical_name,
                    "category": item.category,
                    "brand": item.brand,
                    "quantity": item.quantity,
                    "unit": item.unit,
                    "normalizedQuantity": item.normalized_quantity,
                    "normalizedUnit": item.normalized_unit,
                    "unitPrice": item.unit_price,
                    "linePrice": item.line_price,
                    "confidence": item.confidence,
                    "isGrocery": item.is_grocery,
                }
                for item in extracted.items
            ],
            "totals": {
                "itemCount": len(extracted.items),
                "groceryItemsCount": grocery_count,
                "nonGroceryItemsCount": non_grocery_count,
            },
            "derived": {
                "monthBucket": month_bucket,
                "priceObservationCreated": False,
                "inventoryApplied": False,
            },
            "review": {
                "needsHumanReview": needs_review,
                "reviewed": False,
                "reviewedAt": None,
            },
        }

        # Insert receipt
        receipt_id = await receipt_repo.insert(receipt_doc)
        receipt_doc["_id"] = receipt_id

        # Create price observations for grocery items
        observations = []
        for item in receipt_doc["items"]:
            if item.get("isGrocery"):
                observations.append({
                    "userId": user_id,
                    "receiptId": receipt_id,
                    "canonicalItemId": item["canonicalItemId"],
                    "canonicalName": item["canonicalName"],
                    "canonicalCategory": item.get("category"),
                    "storeName": normalized_name,
                    "storeId": None,
                    "purchasedAt": receipt_doc["transaction"]["purchasedAt"],
                    "quantity": item["quantity"],
                    "unit": item["unit"],
                    "normalizedQuantity": item.get("normalizedQuantity"),
                    "normalizedUnit": item.get("normalizedUnit"),
                    "linePrice": item["linePrice"],
                    "unitPrice": item.get("unitPrice"),
                    "promoFlag": False,
                    "brand": item.get("brand"),
                    "confidence": item.get("confidence", 0),
                })
        if observations:
            await price_repo.insert_observations(observations)
            await receipt_repo.update(receipt_id, {"derived.priceObservationCreated": True})

        # Apply inventory
        await inventory_service.apply_receipt_purchases(
            user_id,
            receipt_id,
            [item.model_dump() for item in extracted.items],
            store_name=normalized_name,
        )
        await receipt_repo.update(receipt_id, {"derived.inventoryApplied": True})

        logger.info("Receipt %s processed for user %s", receipt_id, user_id)
        return self._to_response(receipt_doc)

    # ── Queries ────────────────────────────────────────────────────────

    async def get_receipt(self, receipt_id: str) -> dict:
        """Get a receipt by id."""
        doc = await receipt_repo.find_by_id(receipt_id)
        if not doc:
            raise NotFoundException(f"Receipt {receipt_id} not found")
        return self._to_response(doc)

    async def get_receipt_image(self, receipt_id: str) -> tuple[bytes, str]:
        """Get receipt image from storage."""
        doc = await receipt_repo.find_by_id(receipt_id)
        if not doc:
            raise NotFoundException(f"Receipt {receipt_id} not found")

        path = doc.get("source", {}).get("storagePath")
        content_type = doc.get("source", {}).get("contentType", "image/jpeg")

        if not path:
            raise NotFoundException(f"No image path for receipt {receipt_id}")

        image_bytes = await storage.read(path)
        return image_bytes, content_type

    async def list_receipts(
        self,
        user_id: str,
        page: int = 1,
        page_size: int = 20,
        month: Optional[str] = None,
        store: Optional[str] = None,
    ) -> dict:
        """List receipts with pagination."""
        docs, total = await receipt_repo.find_by_user(
            user_id, page, page_size, month, store
        )
        total_pages = (total + page_size - 1) // page_size if total else 0
        return {
            "items": [self._to_list_item(d) for d in docs],
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total": total,
                "total_pages": total_pages,
            },
        }

    # ── Review / correction ────────────────────────────────────────────

    async def review_receipt(self, receipt_id: str, corrections: dict) -> dict:
        """Apply corrections to a receipt and replay downstream effects."""
        doc = await receipt_repo.find_by_id(receipt_id)
        if not doc:
            raise NotFoundException(f"Receipt {receipt_id} not found")

        user_id = doc["userId"]

        # Reverse old effects
        await inventory_service.reverse_receipt_effects(user_id, receipt_id, doc.get("items", []))
        await price_repo.delete_by_receipt(receipt_id)

        # Apply corrections
        update: dict = {
            "review.reviewed": True,
            "review.reviewedAt": datetime.utcnow(),
        }

        if corrections.get("merchant_name"):
            update["merchant.name"] = corrections["merchant_name"]
            update["merchant.normalizedName"] = corrections["merchant_name"].strip().lower()

        if corrections.get("items") is not None:
            update["items"] = [
                {
                    "rawText": i.raw_text,
                    "canonicalItemId": i.canonical_name.lower().replace(" ", "_"),
                    "canonicalName": i.canonical_name,
                    "category": i.category,
                    "brand": i.brand,
                    "quantity": i.quantity,
                    "unit": i.unit,
                    "normalizedQuantity": i.normalized_quantity,
                    "normalizedUnit": i.normalized_unit,
                    "unitPrice": i.unit_price,
                    "linePrice": i.line_price,
                    "confidence": i.confidence,
                    "isGrocery": i.is_grocery,
                }
                for i in corrections["items"]
            ]

        updated = await receipt_repo.update(receipt_id, update)

        # Replay effects with corrected data
        final = await receipt_repo.find_by_id(receipt_id)
        store_name = final.get("merchant", {}).get("normalizedName", "")
        items = final.get("items", [])

        # Re-create price observations
        observations = []
        for item in items:
            if item.get("isGrocery"):
                observations.append({
                    "userId": user_id,
                    "receiptId": receipt_id,
                    "canonicalItemId": item.get("canonicalItemId", ""),
                    "canonicalName": item.get("canonicalName", ""),
                    "canonicalCategory": item.get("category"),
                    "storeName": store_name,
                    "storeId": None,
                    "purchasedAt": final.get("transaction", {}).get("purchasedAt"),
                    "quantity": item.get("quantity", 1),
                    "unit": item.get("unit", "count"),
                    "normalizedQuantity": item.get("normalizedQuantity"),
                    "normalizedUnit": item.get("normalizedUnit"),
                    "linePrice": item.get("linePrice", 0),
                    "unitPrice": item.get("unitPrice"),
                    "promoFlag": False,
                    "brand": item.get("brand"),
                    "confidence": item.get("confidence", 0),
                })
        if observations:
            await price_repo.insert_observations(observations)

        # Re-apply inventory
        item_dicts = [
            {
                "canonical_name": i.get("canonicalName", ""),
                "category": i.get("category"),
                "quantity": i.get("quantity", 0),
                "unit": i.get("unit", "count"),
                "normalized_quantity": i.get("normalizedQuantity"),
                "normalized_unit": i.get("normalizedUnit"),
                "line_price": i.get("linePrice", 0),
                "confidence": i.get("confidence", 0),
                "is_grocery": i.get("isGrocery", True),
            }
            for i in items
        ]
        await inventory_service.apply_receipt_purchases(
            user_id, receipt_id, item_dicts, store_name=store_name
        )

        return self._to_response(final)

    async def delete_receipt(self, receipt_id: str) -> dict:
        """Fully delete a receipt and reverse its downstream effects."""
        doc = await receipt_repo.find_by_id(receipt_id)
        if not doc:
            raise NotFoundException(f"Receipt {receipt_id} not found")

        user_id = doc["userId"]
        items = doc.get("items", [])
        storage_path = doc.get("source", {}).get("storagePath")

        await inventory_service.reverse_receipt_effects(user_id, receipt_id, items)
        await price_repo.delete_by_receipt(receipt_id)
        await receipt_repo.delete(receipt_id)

        if storage_path:
            await storage.delete(storage_path)

        logger.info("Receipt %s deleted", receipt_id)
        return {"id": receipt_id, "deleted": True}

    # ── Helpers ────────────────────────────────────────────────────────

    @staticmethod
    def _to_response(doc: dict) -> dict:
        merchant = doc.get("merchant", {})
        txn = doc.get("transaction", {})
        return {
            "id": str(doc.get("_id", "")),
            "user_id": doc.get("userId", ""),
            "merchant": {
                "name": merchant.get("name", ""),
                "normalized_name": merchant.get("normalizedName", ""),
                "store_id": merchant.get("storeId"),
                "address": merchant.get("address"),
                "phone": merchant.get("phone"),
            },
            "transaction": {
                "receipt_number": txn.get("receiptNumber"),
                "purchased_at": txn.get("purchasedAt"),
                "currency": txn.get("currency", "USD"),
                "subtotal": txn.get("subtotal", 0),
                "tax": txn.get("tax", 0),
                "tip": txn.get("tip", 0),
                "total": txn.get("total", 0),
                "payment_method": txn.get("paymentMethod"),
            },
            "items": [
                {
                    "raw_text": item.get("rawText", ""),
                    "canonical_item_id": item.get("canonicalItemId"),
                    "canonical_name": item.get("canonicalName"),
                    "category": item.get("category"),
                    "brand": item.get("brand"),
                    "quantity": item.get("quantity", 0),
                    "unit": item.get("unit", ""),
                    "normalized_quantity": item.get("normalizedQuantity"),
                    "normalized_unit": item.get("normalizedUnit"),
                    "unit_price": item.get("unitPrice"),
                    "line_price": item.get("linePrice", 0),
                    "confidence": item.get("confidence", 0),
                    "is_grocery": item.get("isGrocery", True),
                }
                for item in doc.get("items", [])
            ],
            "totals": doc.get("totals", {}),
            "review": doc.get("review", {}),
            "image_url": f"/api/v1/receipts/{doc.get('_id')}/image",
            "created_at": doc.get("source", {}).get("uploadedAt"),
        }

    @staticmethod
    def _to_list_item(doc: dict) -> dict:
        return {
            "id": str(doc.get("_id", "")),
            "merchant_name": doc.get("merchant", {}).get("name", ""),
            "total": doc.get("transaction", {}).get("total", 0),
            "item_count": doc.get("totals", {}).get("itemCount", 0),
            "purchased_at": doc.get("transaction", {}).get("purchasedAt"),
            "image_url": f"/api/v1/receipts/{doc.get('_id')}/image",
        }


receipt_service = ReceiptService()
