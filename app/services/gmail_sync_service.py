"""Gmail sync service – fetch, parse, and store expenses from Gmail."""

import logging
from datetime import datetime, timedelta, timezone

import httpx

from app.repositories.gmail_repository import (
    email_expense_repo,
    linked_account_repo,
    sync_run_repo,
)
from app.services.gmail_auth_service import gmail_auth_service
from app.services.gmail_expense_parser import gmail_expense_parser
from app.utils.exceptions import ValidationException

logger = logging.getLogger(__name__)

GMAIL_API_BASE = "https://gmail.googleapis.com/gmail/v1/users/me"

# Keywords for filtering expense-related emails
EXPENSE_KEYWORDS = (
    "receipt OR invoice OR payment OR order OR charged OR "
    "transaction OR statement OR subscription OR delivery OR "
    "purchase OR confirmation OR shipped"
)

EXPENSE_SENDERS = [
    "zellepay.com", "paypal.com", "venmo.com",
    "uber.com", "lyft.com",
    "doordash.com", "ubereats.com", "grubhub.com", "instacart.com",
    "amazon.com", "amazon.in",
    "netflix.com", "spotify.com", "apple.com",
]


class GmailSyncService:
    """Orchestrates Gmail sync: fetch messages → parse → store."""

    def build_query(self, days_back: int = 0) -> str:
        """Build Gmail search query. days_back=0 means today only."""
        target_date = datetime.now(timezone.utc) - timedelta(days=days_back)
        date_str = target_date.strftime("%Y/%m/%d")
        sender_filter = " OR ".join(f"from:{s}" for s in EXPENSE_SENDERS)
        return f"after:{date_str} ({EXPENSE_KEYWORDS} OR {sender_filter})"

    async def sync_emails(self, user_id: str, days_back: int = 0) -> dict:
        """Full sync pipeline: fetch → parse → store → log.
        
        days_back=0 means today only, days_back=7 means last 7 days, etc.
        """
        access_token = await gmail_auth_service.get_valid_token(user_id)
        query = self.build_query(days_back)

        # Log sync run
        run_id = await sync_run_repo.insert({
            "userId": user_id,
            "startedAt": datetime.utcnow(),
            "status": "running",
            "queryUsed": query,
            "messagesFound": 0,
            "messagesParsed": 0,
            "messagesStored": 0,
            "errors": [],
        })

        errors: list[str] = []
        messages_found = 0
        messages_parsed = 0
        messages_stored = 0
        new_expenses: list[dict] = []
        skipped_emails: list[dict] = []

        try:
            # Fetch message IDs
            message_ids = await self._list_messages(access_token, query)
            messages_found = len(message_ids)

            for msg_meta in message_ids:
                msg_id = msg_meta["id"]
                try:
                    # Check if already stored
                    if await email_expense_repo.exists_by_gmail_id(user_id, msg_id):
                        continue

                    # Fetch full message
                    full_msg = await self._get_message(access_token, msg_id)

                    # Extract headers for logging
                    headers = full_msg.get("payload", {}).get("headers", [])
                    msg_subject = next((h["value"] for h in headers if h["name"].lower() == "subject"), "(no subject)")
                    msg_sender = next((h["value"] for h in headers if h["name"].lower() == "from"), "(unknown)")
                    msg_snippet = full_msg.get("snippet", "")[:120]

                    logger.info(
                        "Processing email: from=%s subject=%s snippet=%s",
                        msg_sender[:60], msg_subject[:80], msg_snippet[:60],
                    )

                    # Parse
                    parsed = await gmail_expense_parser.parse_message_async(full_msg)
                    if not parsed:
                        logger.info(
                            "SKIPPED (no expense found): from=%s subject=%s",
                            msg_sender[:60], msg_subject[:80],
                        )
                        skipped_emails.append({
                            "gmail_message_id": msg_id,
                            "sender": msg_sender,
                            "subject": msg_subject,
                            "snippet": msg_snippet,
                            "reason": "No expense pattern or dollar amount found",
                        })
                        continue

                    messages_parsed += 1

                    # Build expense document
                    expense_doc = {
                        "userId": user_id,
                        "gmailMessageId": msg_id,
                        "gmailThreadId": full_msg.get("threadId"),
                        "gmailLabelIds": full_msg.get("labelIds", []),
                        "source": "gmail",
                        "sender": parsed.get("sender", ""),
                        "subject": parsed.get("subject", ""),
                        "snippet": full_msg.get("snippet", ""),
                        "receivedAt": parsed.get("receivedAt"),
                        "messageDate": parsed.get("receivedAt"),
                        "expenseType": parsed.get("expenseType", "other"),
                        "merchant": parsed.get("merchant", ""),
                        "normalizedMerchant": parsed.get("normalizedMerchant", ""),
                        "amount": parsed.get("amount", 0),
                        "currency": parsed.get("currency", "USD"),
                        "tax": parsed.get("tax"),
                        "transactionAt": parsed.get("transactionAt") or datetime.utcnow(),
                        "category": parsed.get("category", "other"),
                        "paymentMethod": parsed.get("paymentMethod"),
                        "confidence": parsed.get("confidence", 0),
                        "rawText": parsed.get("rawText", ""),
                        "rawHtml": None,
                        "attachmentsMeta": [],
                        "parsingStatus": parsed.get("parsingStatus", "parsed"),
                        "review": parsed.get("review", {
                            "needsHumanReview": parsed.get("confidence", 0) < 0.7,
                            "reviewed": False,
                            "reviewedAt": None,
                        }),
                        "createdAt": datetime.utcnow(),
                        "updatedAt": datetime.utcnow(),
                    }

                    expense_id = await email_expense_repo.insert(expense_doc)
                    expense_doc["_id"] = expense_id
                    messages_stored += 1
                    new_expenses.append(self._to_response(expense_doc))

                except Exception as e:
                    err_msg = f"Failed to process message {msg_id}: {str(e)}"
                    logger.warning(err_msg)
                    errors.append(err_msg)

        except Exception as e:
            err_msg = f"Sync failed: {str(e)}"
            logger.exception(err_msg)
            errors.append(err_msg)

        # Update sync run
        await sync_run_repo.update(run_id, {
            "completedAt": datetime.utcnow(),
            "status": "completed" if not errors else "completed_with_errors",
            "messagesFound": messages_found,
            "messagesParsed": messages_parsed,
            "messagesStored": messages_stored,
            "errors": errors,
        })

        # Update last synced timestamp
        await linked_account_repo.update(user_id, {"lastSyncedAt": datetime.utcnow()})

        summary = {
            "messages_found": messages_found,
            "messages_parsed": messages_parsed,
            "messages_stored": messages_stored,
            "messages_skipped": len(skipped_emails),
            "errors": errors,
            "expenses": new_expenses,
            "skipped_emails": skipped_emails,
        }

        logger.info(
            "Gmail sync for user %s: found=%d parsed=%d stored=%d errors=%d",
            user_id, messages_found, messages_parsed, messages_stored, len(errors),
        )
        return summary

    async def sync_current_day(self, user_id: str) -> dict:
        """Convenience wrapper: sync today only."""
        return await self.sync_emails(user_id, days_back=0)

    async def fetch_and_preview(self, user_id: str, days_back: int = 0) -> dict:
        """Fetch emails, parse them, show what was found, AND store to DB."""
        return await self.sync_emails(user_id, days_back=days_back)

    async def get_sync_runs(self, user_id: str, limit: int = 10) -> list[dict]:
        """Return recent sync run history."""
        runs = await sync_run_repo.find_by_user(user_id, limit)
        return [
            {
                "id": r.get("_id", ""),
                "started_at": r.get("startedAt"),
                "completed_at": r.get("completedAt"),
                "status": r.get("status", ""),
                "query_used": r.get("queryUsed", ""),
                "messages_found": r.get("messagesFound", 0),
                "messages_parsed": r.get("messagesParsed", 0),
                "messages_stored": r.get("messagesStored", 0),
                "errors": r.get("errors", []),
            }
            for r in runs
        ]

    async def delete_all_email_expenses(self, user_id: str) -> dict:
        """Delete all email expenses for a user (testing reset)."""
        count = await email_expense_repo.delete_all_by_user(user_id)
        logger.info("Deleted %d email expenses for user %s", count, user_id)
        return {"expenses_deleted": count}

    # ── Gmail API helpers ──────────────────────────────────────────────

    async def _list_messages(self, access_token: str, query: str) -> list[dict]:
        """List Gmail message IDs matching the query."""
        messages = []
        page_token = None

        async with httpx.AsyncClient() as client:
            while True:
                params: dict = {"q": query, "maxResults": 50}
                if page_token:
                    params["pageToken"] = page_token

                resp = await client.get(
                    f"{GMAIL_API_BASE}/messages",
                    headers={"Authorization": f"Bearer {access_token}"},
                    params=params,
                    timeout=30,
                )

                if resp.status_code != 200:
                    logger.error("Gmail list messages failed: %s", resp.text)
                    break

                data = resp.json()
                messages.extend(data.get("messages", []))
                page_token = data.get("nextPageToken")
                if not page_token:
                    break

        return messages

    async def _get_message(self, access_token: str, message_id: str) -> dict:
        """Fetch full Gmail message by ID."""
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{GMAIL_API_BASE}/messages/{message_id}",
                headers={"Authorization": f"Bearer {access_token}"},
                params={"format": "full"},
                timeout=30,
            )

        if resp.status_code != 200:
            raise Exception(f"Gmail get message failed: {resp.status_code} {resp.text}")

        return resp.json()

    @staticmethod
    def _to_response(doc: dict) -> dict:
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
            "created_at": doc.get("createdAt"),
        }


gmail_sync_service = GmailSyncService()
