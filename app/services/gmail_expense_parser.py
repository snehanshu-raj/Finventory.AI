"""Gmail expense parser – hybrid deterministic + LLM extraction."""

import json
import logging
import re
from datetime import datetime
from typing import Optional

from app.services.llm_provider import get_llm_provider

logger = logging.getLogger(__name__)

# ── Deterministic patterns for known senders ───────────────────────────

SENDER_PATTERNS = {
    # Zelle
    r"zellepay|zelle": {
        "expense_type": "zelle",
        "category": "transfer",
        "patterns": {
            "amount": [r"\$\s*([\d,]+\.?\d{0,2})", r"([\d,]+\.?\d{0,2})\s*(?:USD|dollars)"],
            "merchant": [r"(?:to|from|sent to|received from)\s+([A-Za-z\s]+?)(?:\s+on|\s+\$|\.|$)"],
        },
    },
    # PayPal
    r"paypal": {
        "expense_type": "order_receipt",
        "category": "shopping",
        "patterns": {
            "amount": [r"\$\s*([\d,]+\.?\d{0,2})", r"Total\s*\$?([\d,]+\.?\d{0,2})"],
            "merchant": [r"payment\s+to\s+(.+?)(?:\s+for|\s*\$|\.)", r"You\s+(?:sent|paid)\s+(.+?)(?:\s*\$|\.)"],
        },
    },
    # Uber / Lyft
    r"uber|lyft": {
        "expense_type": "ride_share",
        "category": "transport",
        "patterns": {
            "amount": [r"\$\s*([\d,]+\.?\d{0,2})", r"total[:\s]*\$?([\d,]+\.?\d{0,2})"],
            "merchant": [r"(uber|lyft)"],
        },
    },
    # DoorDash / UberEats / Grubhub / Instacart
    r"doordash|ubereats|grubhub|instacart|postmates": {
        "expense_type": "food_delivery",
        "category": "food",
        "patterns": {
            "amount": [r"\$\s*([\d,]+\.?\d{0,2})", r"total[:\s]*\$?([\d,]+\.?\d{0,2})"],
            "merchant": [r"(doordash|uber\s*eats|grubhub|instacart|postmates)"],
        },
    },
    # Amazon
    r"amazon": {
        "expense_type": "order_receipt",
        "category": "shopping",
        "patterns": {
            "amount": [r"\$\s*([\d,]+\.?\d{0,2})", r"(?:total|grand total|order total)[:\s]*\$?([\d,]+\.?\d{0,2})"],
            "merchant": [r"(amazon)"],
        },
    },
    # Subscription / recurring
    r"netflix|spotify|apple\.com|google\s*play|hulu|disney|youtube\s*premium|adobe": {
        "expense_type": "subscription",
        "category": "subscriptions",
        "patterns": {
            "amount": [r"\$\s*([\d,]+\.?\d{0,2})"],
            "merchant": [r"(netflix|spotify|apple|google play|hulu|disney|youtube premium|adobe)"],
        },
    },
    # Airlines (Spirit, United, Delta, Southwest, American, JetBlue, etc.)
    r"spirit|united|delta|southwest|american\s*airlines|jetblue|frontier|allegiant|air\s*canada": {
        "expense_type": "ride_share",
        "category": "transport",
        "patterns": {
            "amount": [r"\$\s*([\d,]+\.?\d{0,2})", r"(?:total|amount|price)[:\s]*\$?([\d,]+\.?\d{0,2})"],
            "merchant": [r"(spirit|united|delta|southwest|american|jet\s*blue|frontier|allegiant)"],
        },
    },
    # Hotel / Rental (Airbnb, booking.com, hotels.com, Vrbo, etc.)
    r"airbnb|booking\.com|hotels\.com|vrbo|hilton|marriott|hyatt|ihg|wyndham|expedia": {
        "expense_type": "invoice",
        "category": "travel",
        "patterns": {
            "amount": [r"\$\s*([\d,]+\.?\d{0,2})", r"(?:total|amount due|reservation total)[:\s]*\$?([\d,]+\.?\d{0,2})"],
            "merchant": [r"(airbnb|booking|hotels|vrbo|hilton|marriott|hyatt|wyndham)"],
        },
    },
    # Rental cars (Hertz, Avis, Budget, Enterprise, etc.)
    r"hertz|avis|budget|enterprise|alamo|national|europcar": {
        "expense_type": "invoice",
        "category": "transport",
        "patterns": {
            "amount": [r"\$\s*([\d,]+\.?\d{0,2})", r"(?:total|amount due)[:\s]*\$?([\d,]+\.?\d{0,2})"],
            "merchant": [r"(hertz|avis|budget|enterprise|alamo|national|europcar)"],
        },
    },
    # Utilities / Rent (landlord, property manager, utility company)
    r"rent|landlord|property|manager|apartment|utility|electric|gas\s+company|water|comcast|verizon|at&t": {
        "expense_type": "invoice",
        "category": "utilities",
        "patterns": {
            "amount": [r"(?:due|payment|amount|total)[:\s]*\$?([\d,]+\.?\d{0,2})", r"\$\s*([\d,]+\.?\d{0,2})"],
            "merchant": [r"property|landlord|rent|utility|apartment"],
        },
    },
    # Banks and Financial (Bank of America, Chase, Wells Fargo, etc.)
    r"bank\s*of\s*america|chase|wells\s*fargo|citi|capital\s*one|navy\s*federal|payroll": {
        "expense_type": "invoice",
        "category": "other",
        "patterns": {
            "amount": [r"(?:amount|debit|withdrawal)[:\s]*\$?([\d,]+\.?\d{0,2})", r"\$\s*([\d,]+\.?\d{0,2})"],
            "merchant": [r"(bank|chase|wells|citi|capital)"],
        },
    },
    # Credit card alerts
    r"(?:card|transaction|purchase|charge)\s*(?:alert|notification|confirmation)": {
        "expense_type": "card_alert",
        "category": "other",
        "patterns": {
            "amount": [r"\$\s*([\d,]+\.?\d{0,2})", r"(?:amount|charged|transaction)[:\s]*\$?([\d,]+\.?\d{0,2})"],
            "merchant": [r"(?:at|merchant|from)\s+([A-Za-z0-9\s&'.]+?)(?:\s+on|\s+for|\s*\$|\.|$)"],
        },
    },
}

# Date patterns
DATE_PATTERNS = [
    r"(\d{1,2}/\d{1,2}/\d{2,4})",
    r"(\d{4}-\d{2}-\d{2})",
    r"((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\w*\s+\d{1,2},?\s+\d{4})",
]


EMAIL_EXPENSE_LLM_PROMPT = """Extract expense information from this email. Return a JSON object with these fields:
- expenseType: one of "zelle", "card_alert", "order_receipt", "invoice", "subscription", "ride_share", "food_delivery", "other"
- merchant: the merchant/vendor/payee name
- normalizedMerchant: lowercase simple version of merchant name
- amount: the dollar amount as a number (no $ sign)
- currency: usually "USD"
- tax: tax amount if visible, otherwise null
- transactionAt: ISO 8601 datetime if you can determine it, otherwise null
- category: one of "shopping", "food", "transport", "subscriptions", "transfer", "utilities", "entertainment", "health", "other"
- paymentMethod: "credit_card", "debit_card", "bank_transfer", "paypal", etc. or null
- confidence: your confidence 0.0-1.0 in this extraction

IMPORTANT:
- Only extract if you see a clear expense/payment/charge/transaction being paid/charged. DO NOT assume an expense if you only see a transaction alert.
- Do NOT invent amounts that aren't in the text
- If this doesn't look like an expense email, return {{"isExpense": false}}

Email:
From: {sender}
Subject: {subject}
Body:
{body}

Return ONLY valid JSON, no markdown fences."""


class GmailExpenseParser:
    """Hybrid deterministic + LLM email expense parser."""

    def parse_message(self, message: dict) -> Optional[dict]:
        """Parse a Gmail message payload into a structured expense.

        Returns None if the email doesn't appear to be expense-related.
        """
        sender = self._get_header(message, "From") or ""
        subject = self._get_header(message, "Subject") or ""
        body_text = self._get_body_text(message)
        received_at = self._get_header(message, "Date")

        combined_text = f"{sender}\n{subject}\n{body_text}"

        # Step 1: Try deterministic patterns
        result = self._deterministic_extract(sender, subject, body_text, combined_text)

        if result and result.get("confidence", 0) >= 0.7:
            result["sender"] = sender
            result["subject"] = subject
            result["rawText"] = body_text[:5000]
            result["receivedAt"] = received_at
            result["parsingStatus"] = "parsed"
            result["review"] = {"needsHumanReview": False, "reviewed": False, "reviewedAt": None}
            return result

        # Step 2: return deterministic with lower confidence (will be enhanced by LLM in async path)
        if result:
            result["sender"] = sender
            result["subject"] = subject
            result["rawText"] = body_text[:5000]
            result["receivedAt"] = received_at
            result["parsingStatus"] = "needs_review"
            result["review"] = {"needsHumanReview": True, "reviewed": False, "reviewedAt": None}
            return result

        return None

    async def parse_message_async(self, message: dict) -> Optional[dict]:
        """Parse with deterministic first, LLM fallback for low confidence."""
        result = self.parse_message(message)

        if result and result.get("confidence", 0) >= 0.7:
            return result

        # LLM fallback
        sender = self._get_header(message, "From") or ""
        subject = self._get_header(message, "Subject") or ""
        body_text = self._get_body_text(message)

        llm_result = await self._llm_extract(sender, subject, body_text)
        if llm_result:
            llm_result["sender"] = sender
            llm_result["subject"] = subject
            llm_result["rawText"] = body_text[:5000]
            llm_result["receivedAt"] = self._get_header(message, "Date")
            return llm_result

        # Return deterministic result even if low confidence
        return result

    def _deterministic_extract(self, sender: str, subject: str, body: str, combined: str) -> Optional[dict]:
        """Try regex-based extraction for known senders."""
        combined_lower = combined.lower()
        sender_lower = sender.lower()
        subject_lower = subject.lower()

        for sender_pattern, config in SENDER_PATTERNS.items():
            if re.search(sender_pattern, sender_lower) or re.search(sender_pattern, subject_lower):
                amount = self._extract_amount(config["patterns"]["amount"], combined)
                merchant = self._extract_pattern(config["patterns"]["merchant"], combined)

                if amount is not None:
                    return {
                        "expenseType": config["expense_type"],
                        "merchant": merchant or sender.split("<")[0].strip(),
                        "normalizedMerchant": (merchant or "").strip().lower().replace("'", "").replace("  ", " "),
                        "amount": amount,
                        "currency": "USD",
                        "tax": None,
                        "transactionAt": self._extract_date(combined),
                        "category": config["category"],
                        "paymentMethod": None,
                        "confidence": 0.85,
                        "parsingStatus": "parsed",
                    }

        # Generic amount detection (card alerts, etc.)
        amount = self._extract_amount([r"\$\s*([\d,]+\.?\d{0,2})"], combined)
        if amount and amount > 0:
            return {
                "expenseType": "other",
                "merchant": sender.split("<")[0].strip() or "Unknown",
                "normalizedMerchant": sender.split("<")[0].strip().lower(),
                "amount": amount,
                "currency": "USD",
                "tax": None,
                "transactionAt": self._extract_date(combined),
                "category": "other",
                "paymentMethod": None,
                "confidence": 0.4,
                "parsingStatus": "needs_review",
            }

        return None

    async def _llm_extract(self, sender: str, subject: str, body: str) -> Optional[dict]:
        """Use LLM to extract expense data."""
        try:
            provider = get_llm_provider()
            prompt = EMAIL_EXPENSE_LLM_PROMPT.format(
                sender=sender,
                subject=subject,
                body=body[:3000],
            )
            raw = await provider.generate_text(prompt)

            cleaned = raw.strip()
            if cleaned.startswith("```"):
                lines = cleaned.split("\n")
                lines = lines[1:]
                if lines and lines[-1].strip() == "```":
                    lines = lines[:-1]
                cleaned = "\n".join(lines)

            parsed = json.loads(cleaned)

            if parsed.get("isExpense") is False:
                return None

            confidence = parsed.get("confidence", 0.5)
            return {
                "expenseType": parsed.get("expenseType", "other"),
                "merchant": parsed.get("merchant", "Unknown"),
                "normalizedMerchant": parsed.get("normalizedMerchant", "").lower(),
                "amount": float(parsed.get("amount", 0)),
                "currency": parsed.get("currency", "USD"),
                "tax": parsed.get("tax"),
                "transactionAt": parsed.get("transactionAt"),
                "category": parsed.get("category", "other"),
                "paymentMethod": parsed.get("paymentMethod"),
                "confidence": confidence,
                "parsingStatus": "parsed" if confidence >= 0.7 else "needs_review",
                "review": {
                    "needsHumanReview": confidence < 0.7,
                    "reviewed": False,
                    "reviewedAt": None,
                },
            }
        except Exception as e:
            logger.warning("LLM expense extraction failed: %s", e)
            return None

    # ── Helpers ────────────────────────────────────────────────────────

    @staticmethod
    def _get_header(message: dict, name: str) -> Optional[str]:
        headers = message.get("payload", {}).get("headers", [])
        for h in headers:
            if h.get("name", "").lower() == name.lower():
                return h.get("value")
        return None

    @staticmethod
    def _html_to_text(html: str) -> str:
        """Convert HTML to plain text, handling common entities."""
        try:
            from bs4 import BeautifulSoup
            text = BeautifulSoup(html, "html.parser").get_text(separator=" ", strip=True)
        except ImportError:
            # Strip HTML tags with regex
            text = re.sub(r"<[^>]+>", " ", html)
        
        # Unescape HTML entities
        import html as html_module
        text = html_module.unescape(text)
        
        # Normalize whitespace
        text = re.sub(r"\s+", " ", text).strip()
        return text

    @staticmethod
    def _get_body_text(message: dict) -> str:
        """Extract plain text from Gmail message payload."""
        import base64

        def _decode(data: str) -> str:
            try:
                return base64.urlsafe_b64decode(data + "==").decode("utf-8", errors="replace")
            except Exception:
                return ""

        def _is_html(text: str) -> bool:
            """Check if text is HTML."""
            return bool(re.search(r'<!DOCTYPE|<html|<body|<div|<p|<span|&(?:[a-zA-Z]+|#\d+);', text, re.IGNORECASE))

        payload = message.get("payload", {})

        # Simple body
        body_data = payload.get("body", {}).get("data", "")
        if body_data:
            decoded = _decode(body_data)
            # Check if it's HTML and convert to plain text
            if _is_html(decoded):
                return GmailExpenseParser._html_to_text(decoded)
            return decoded

        # Multipart
        parts = payload.get("parts", [])
        for part in parts:
            mime = part.get("mimeType", "")
            if mime == "text/plain":
                data = part.get("body", {}).get("data", "")
                if data:
                    return _decode(data)

        # HTML fallback
        for part in parts:
            mime = part.get("mimeType", "")
            if mime == "text/html":
                data = part.get("body", {}).get("data", "")
                if data:
                    html = _decode(data)
                    return GmailExpenseParser._html_to_text(html)

        return message.get("snippet", "")

    @staticmethod
    def _extract_amount(patterns: list[str], text: str) -> Optional[float]:
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    return float(match.group(1).replace(",", ""))
                except (ValueError, IndexError):
                    continue
        return None

    @staticmethod
    def _extract_pattern(patterns: list[str], text: str) -> Optional[str]:
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return None

    @staticmethod
    def _extract_date(text: str) -> Optional[str]:
        for pattern in DATE_PATTERNS:
            match = re.search(pattern, text)
            if match:
                return match.group(1)
        return None


gmail_expense_parser = GmailExpenseParser()
