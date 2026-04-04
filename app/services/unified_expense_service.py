"""Unified expense service – merge receipts + email expenses."""

import logging
from datetime import datetime

from typing import Optional

from app.repositories.gmail_repository import email_expense_repo
from app.repositories.receipt_repository import receipt_repo
from app.repositories.price_repository import price_repo

logger = logging.getLogger(__name__)


class UnifiedExpenseService:
    """Merge receipt-based and email-based expenses into one feed."""

    async def list_expenses(
        self,
        user_id: str,
        source: str = "all",
        category: Optional[str] = None,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        merchant: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> dict:
        """Return merged expense feed sorted by date."""
        unified: list[dict] = []

        # Fetch receipt expenses
        if source in ("all", "receipt"):
            receipt_docs, _ = await receipt_repo.find_by_user(
                user_id, page=1, page_size=200,
            )
            for doc in receipt_docs:
                exp = self._receipt_to_unified(doc)
                if self._passes_filters(exp, category, from_date, to_date, merchant):
                    unified.append(exp)

        # Fetch email expenses
        if source in ("all", "gmail"):
            email_docs, _ = await email_expense_repo.find_by_user(
                user_id, page=1, page_size=200,
                category=category, from_date=from_date, to_date=to_date, merchant=merchant,
            )
            for doc in email_docs:
                unified.append(self._email_to_unified(doc))

        # Sort by date descending
        unified.sort(
            key=lambda x: self._safe_date(x.get("transaction_at")),
            reverse=True,
        )

        # Paginate
        total = len(unified)
        paginated = unified[offset : offset + limit]

        return {
            "items": paginated,
            "pagination": {
                "total": total,
                "limit": limit,
                "offset": offset,
            },
        }

    async def get_expense(self, expense_id: str) -> dict:
        """Get a single expense by prefixed ID (gmail_<id> or receipt_<id>)."""
        if expense_id.startswith("gmail_"):
            raw_id = expense_id[6:]
            doc = await email_expense_repo.find_by_id(raw_id)
            if doc:
                return self._email_to_unified(doc)
        elif expense_id.startswith("receipt_"):
            raw_id = expense_id[8:]
            doc = await receipt_repo.find_by_id(raw_id)
            if doc:
                return self._receipt_to_unified(doc)
        else:
            # Try both
            doc = await email_expense_repo.find_by_id(expense_id)
            if doc:
                return self._email_to_unified(doc)
            doc = await receipt_repo.find_by_id(expense_id)
            if doc:
                return self._receipt_to_unified(doc)

        from app.utils.exceptions import NotFoundException
        raise NotFoundException(f"Expense {expense_id} not found")

    async def get_summary(self, user_id: str) -> dict:
        """Combined spend summary across receipts and emails."""
        now = datetime.utcnow()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        # Receipt totals
        receipt_month_total = await price_repo.total_spend_since(user_id, month_start)
        receipt_today_total = await price_repo.total_spend_since(user_id, today_start)

        # Email expense totals
        email_month_total = await email_expense_repo.total_spend_since(user_id, month_start)
        email_today_total = await email_expense_repo.total_spend_since(user_id, today_start)

        # By category (email)
        email_by_cat = await email_expense_repo.aggregate_by_category(user_id, month_start)
        categories = [
            {
                "category": c["_id"] or "other",
                "total_spend": round(c["totalSpend"], 2),
                "count": c.get("count", 0),
                "source": "gmail",
            }
            for c in email_by_cat
        ]

        # Receipt by category (from price observations)
        receipt_by_cat = await price_repo.aggregate_expenses_by_category(user_id, month_start)
        for c in receipt_by_cat:
            categories.append({
                "category": c["_id"] or "uncategorized",
                "total_spend": round(c.get("totalSpend", 0), 2),
                "count": c.get("itemCount", 0),
                "source": "receipt",
            })

        # Recent expenses
        recent_emails, _ = await email_expense_repo.find_by_user(user_id, page=1, page_size=5)
        recent_receipts, _ = await receipt_repo.find_by_user(user_id, page=1, page_size=5)

        recent = []
        for doc in recent_emails:
            recent.append(self._email_to_unified(doc))
        for doc in recent_receipts:
            recent.append(self._receipt_to_unified(doc))
        recent.sort(key=lambda x: self._safe_date(x.get("transaction_at")), reverse=True)

        # Recent merchants
        merchants = list({e.get("merchant", "") for e in recent if e.get("merchant")})[:10]

        return {
            "total_today": round(receipt_today_total + email_today_total, 2),
            "total_this_month": round(receipt_month_total + email_month_total, 2),
            "by_source": {
                "receipt": round(receipt_month_total, 2),
                "gmail": round(email_month_total, 2),
            },
            "by_category": categories,
            "recent_merchants": merchants,
            "recent_expenses": recent[:10],
        }

    # ── Helpers ─────────────────────────────────────────────────────────

    @staticmethod
    def _safe_date(val) -> datetime:
        """Normalise a date value (datetime, str, or None) to datetime for sorting."""
        if isinstance(val, datetime):
            return val
        if isinstance(val, str):
            try:
                return datetime.fromisoformat(val.replace("Z", "+00:00"))
            except (ValueError, TypeError):
                return datetime.min
        return datetime.min

    # ── Adapters ───────────────────────────────────────────────────────

    @staticmethod
    def _receipt_to_unified(doc: dict) -> dict:
        txn = doc.get("transaction", {})
        merchant = doc.get("merchant", {})
        return {
            "id": f"receipt_{doc.get('_id', '')}",
            "source": "receipt",
            "source_id": str(doc.get("_id", "")),
            "merchant": merchant.get("name", ""),
            "normalized_merchant": merchant.get("normalizedName", ""),
            "amount": txn.get("total", 0),
            "currency": txn.get("currency", "USD"),
            "transaction_at": txn.get("purchasedAt"),
            "category": "grocery",
            "payment_method": txn.get("paymentMethod"),
            "expense_type": "receipt",
            "confidence": doc.get("source", {}).get("ocrConfidence", 0),
            "meta": {
                "subject": None,
                "store_name": merchant.get("name"),
                "receipt_id": str(doc.get("_id", "")),
                "item_count": doc.get("totals", {}).get("itemCount", 0),
            },
        }

    @staticmethod
    def _email_to_unified(doc: dict) -> dict:
        return {
            "id": f"gmail_{doc.get('_id', '')}",
            "source": "gmail",
            "source_id": doc.get("gmailMessageId", ""),
            "merchant": doc.get("merchant", ""),
            "normalized_merchant": doc.get("normalizedMerchant", ""),
            "amount": doc.get("amount", 0),
            "currency": doc.get("currency", "USD"),
            "transaction_at": doc.get("transactionAt"),
            "category": doc.get("category", "other"),
            "payment_method": doc.get("paymentMethod"),
            "expense_type": doc.get("expenseType", "other"),
            "confidence": doc.get("confidence", 0),
            "meta": {
                "subject": doc.get("subject"),
                "store_name": None,
                "receipt_id": None,
                "gmail_message_id": doc.get("gmailMessageId"),
            },
        }

    @staticmethod
    def _passes_filters(
        expense: dict,
        category: Optional[str],
        from_date: Optional[datetime],
        to_date: Optional[datetime],
        merchant: Optional[str],
    ) -> bool:
        if category and expense.get("category") != category:
            return False
        txn_at = expense.get("transaction_at")
        if from_date and txn_at and txn_at < from_date:
            return False
        if to_date and txn_at and txn_at > to_date:
            return False
        if merchant and merchant.lower() not in (expense.get("normalized_merchant") or ""):
            return False
        return True


unified_expense_service = UnifiedExpenseService()
