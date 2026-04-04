# Add-On Build Prompt: Gmail-Powered Universal Expense Ingestion

Extend the existing **AI Finance + Grocery Manager** backend with a new capability: **universal expense ingestion from Gmail emails**. The backend should fetch only the current day's expense-related emails on demand or via scheduled polling, parse structured expense data from those emails, store them in MongoDB, and expose unified APIs that return expenses from both uploaded receipts and parsed emails in one consolidated feed. Gmail API supports query-based message filtering through `users.messages.list`, including date and sender filters, which makes a current-day polling strategy feasible for a simpler v1. 

## Scope

This prompt is for **v2 backend enhancement only**.
Do **not** redesign the existing receipt/inventory flow.
Just add Gmail email ingestion and unified expense APIs.

Keep the implementation simple:
- Use **polling** instead of Gmail push notifications.
- Only fetch emails for the **current day** during each sync to reduce complexity.
- Avoid overengineering deduplication; use Gmail `messageId` as the unique identifier.
- Parse only expense-related emails.
- Merge email-derived expenses with receipt-derived expenses in one unified API.

---

## Product Goal

The app should now support two expense ingestion channels:

1. **Receipt uploads** for physical purchases.
2. **Gmail ingestion** for digital expenses such as:
   - Zelle payment confirmations
   - online credit card transaction alerts
   - order confirmations
   - invoices and receipts
   - subscription billing emails
   - ride-share and food delivery receipts

The dashboard should show a single unified expense list regardless of whether the expense came from a receipt image or a Gmail email. Gmail parsing and automated expense extraction are already used in expense tooling to reduce manual entry of digital transactions. [web:289][web:291][web:294]

---

## Tech Requirements

Use the same backend stack:
- Python 3.11
- FastAPI
- MongoDB
- Pydantic v2
- Motor or PyMongo
- httpx if needed
- Google Gmail API client for Python
- OAuth 2.0 for Gmail connection
- APScheduler or similar for polling job

Keep architecture modular and consistent with the existing backend.

---

## New MongoDB Collections

### 1. `linked_accounts`
Store Gmail connection metadata.

Fields:
- `_id`
- `userId`
- `provider` = `gmail`
- `email`
- `scopes`
- `accessToken` or secure token reference
- `refreshToken` or secure token reference
- `tokenExpiry`
- `lastSyncedAt`
- `syncEnabled`
- `createdAt`
- `updatedAt`

Notes:
- If secure token storage is not fully implemented, clearly isolate token-handling logic in one service so it can be replaced later.
- Refresh tokens must be supported.

### 2. `email_expenses`
Store parsed expense records from Gmail messages.

Fields:
- `_id`
- `userId`
- `gmailMessageId`
- `gmailThreadId`
- `gmailLabelIds`
- `source` = `gmail`
- `sender`
- `subject`
- `snippet`
- `receivedAt`
- `messageDate`
- `expenseType` (`zelle`, `card_alert`, `order_receipt`, `invoice`, `subscription`, `ride_share`, `food_delivery`, `other`)
- `merchant`
- `normalizedMerchant`
- `amount`
- `currency`
- `tax`
- `transactionAt`
- `category`
- `paymentMethod`
- `confidence`
- `rawText`
- `rawHtml`
- `attachmentsMeta`
- `parsingStatus` (`parsed`, `needs_review`, `ignored`, `failed`)
- `review`
  - `needsHumanReview`
  - `reviewed`
  - `reviewedAt`
- `createdAt`
- `updatedAt`

### 3. Optional `email_sync_runs`
Track sync job runs.

Fields:
- `_id`
- `userId`
- `startedAt`
- `completedAt`
- `status`
- `queryUsed`
- `messagesFound`
- `messagesParsed`
- `messagesStored`
- `errors`

---

## Functional Requirements

## A. Gmail Account Linking APIs

### `POST /api/v1/integrations/gmail/connect`
Create Gmail integration metadata after OAuth token exchange.

Expected behavior:
- Accept auth code or token payload depending on implementation style.
- Exchange it using Google OAuth.
- Store Gmail linked account metadata in `linked_accounts`.
- Enable sync.

### `GET /api/v1/integrations/gmail/status`
Return whether Gmail is connected and when it was last synced.

### `POST /api/v1/integrations/gmail/disconnect`
Disable sync and optionally remove tokens.

---

## B. Gmail Sync APIs

### `POST /api/v1/integrations/gmail/sync`
Trigger manual sync for the current day.

Behavior:
- Read linked Gmail account for the user.
- Build a Gmail search query limited to current-day likely-expense messages.
- Fetch matching messages using Gmail API `users.messages.list` and then `users.messages.get` for full content. Gmail’s message listing supports the same query format as the Gmail search box and can filter by date/sender/keywords. [web:298][web:304][web:302]
- Parse each message into a structured expense object.
- Store parsed expenses into `email_expenses`.
- Skip insertion if `gmailMessageId` already exists.
- Return sync summary.

### Suggested Gmail query logic for v1
Use current-day-only search to simplify deduplication.

Examples:
- `after:YYYY/MM/DD (receipt OR invoice OR payment OR order OR charged OR sent OR transaction)`
- `after:YYYY/MM/DD from:zellepay.com`
- `after:YYYY/MM/DD category:purchases`
- `after:YYYY/MM/DD (from:uber OR from:doordash OR from:amazon OR from:paypal)`

Gmail search operators like `after:`, `before:`, sender filters, and subject matching are officially supported and can be combined to narrow the sync set. [web:298][web:302][web:306]

Implementation note:
- Make the query builder configurable.
- Store the exact query used in sync logs.

### `GET /api/v1/integrations/gmail/sync-runs`
Return recent sync runs.

---

## C. Email Expense Parsing

Implement a service named something like `GmailExpenseParserService`.

### Public interface
```python
async def parse_gmail_message(message_payload: dict) -> ParsedEmailExpense:
    ...
```

### Parsing strategy
Use a **hybrid deterministic + LLM parser**.

#### Step 1: Deterministic heuristics
Extract from:
- sender email
- subject line
- Gmail snippet
- plain text body
- HTML body converted to text

Use deterministic patterns first for known sources like:
- Zelle
- PayPal
- Uber
- DoorDash
- Amazon
- card transaction alerts
- subscription renewals

Heuristics should look for:
- merchant/vendor
- amount
- currency
- date/time
- transaction type
- payment method

#### Step 2: LLM fallback
If deterministic parsing confidence is low, call an LLM to extract structured fields.

LLM should output this schema:
```json
{
  "expenseType": "zelle",
  "merchant": "Uber",
  "normalizedMerchant": "uber",
  "amount": 18.43,
  "currency": "USD",
  "tax": null,
  "transactionAt": "2026-04-03T11:21:00Z",
  "category": "transport",
  "paymentMethod": "credit_card",
  "confidence": 0.88
}
```

Important:
- The parser must keep `rawText` and original message metadata.
- Mark low-confidence results with `needsHumanReview=true`.
- Do not let the LLM invent an amount if no reliable amount exists.
- Prefer deterministic extraction when possible.

Gmail parsing workflows for receipts and expense automation often use structured extraction of vendor, date, amount, and category, but a hybrid approach is safer than relying entirely on a free-form LLM parser. [web:289][web:294]

---

## D. New Unified Expense APIs

### `GET /api/v1/expenses`
Return one merged feed of all expense records from:
- uploaded receipt-derived transactions
- parsed Gmail-derived expenses

Query params:
- `userId`
- `source=receipt|gmail|all`
- `category`
- `fromDate`
- `toDate`
- `merchant`
- `limit`
- `offset`

Unified response format per item:
```json
{
  "id": "...",
  "source": "gmail",
  "sourceId": "gmail_message_123",
  "merchant": "Uber",
  "normalizedMerchant": "uber",
  "amount": 18.43,
  "currency": "USD",
  "transactionAt": "2026-04-03T11:21:00Z",
  "category": "transport",
  "paymentMethod": "credit_card",
  "expenseType": "ride_share",
  "confidence": 0.88,
  "meta": {
    "subject": "Your Uber receipt",
    "storeName": null,
    "receiptId": null
  }
}
```

### `GET /api/v1/expenses/summary`
Return combined expense summary across receipts and Gmail.

Include:
- total spend today
- total spend this month
- spend by source (`receipt`, `gmail`)
- spend by category
- recent merchants
- recent expenses

### `GET /api/v1/expenses/{expense_id}`
Return full detail for one unified expense.

Implementation note:
- Prefix IDs by source if needed, e.g. `gmail_<id>` and `receipt_<id>`.

---

## E. Email Expense Review APIs

### `GET /api/v1/email-expenses`
List Gmail-derived expenses only.

### `GET /api/v1/email-expenses/{email_expense_id}`
Return one email expense and raw message metadata.

### `PATCH /api/v1/email-expenses/{email_expense_id}/review`
Allow manual correction of merchant, amount, category, date, or expenseType.

Behavior:
- Update parsed object.
- Set reviewed flags.
- Preserve original raw fields.

---

## Background Job

### Poll Gmail current-day emails every N hours
Implement a scheduled polling job that runs every 6 hours by default.

Logic:
1. Find all users with Gmail sync enabled.
2. For each user, build current-day query.
3. Fetch matching messages from Gmail.
4. Skip already stored `gmailMessageId`s.
5. Parse and store new expenses.
6. Record job results in `email_sync_runs`.

Keep this job idempotent.
Gmail `messageId` should be treated as a unique key in MongoDB to avoid duplicate inserts. [web:304][web:296]

---

## Suggested Unified Expense Model

Internally define a normalized expense shape used by the dashboard regardless of source.

```json
{
  "source": "gmail",
  "sourceId": "...",
  "merchant": "...",
  "normalizedMerchant": "...",
  "amount": 25.99,
  "currency": "USD",
  "transactionAt": "...",
  "category": "shopping",
  "paymentMethod": "card",
  "expenseType": "order_receipt",
  "confidence": 0.91
}
```

Use adapters:
- `receipt -> unified expense`
- `email_expense -> unified expense`

This keeps dashboard code simple and avoids duplicating response formatting logic.

---

## Business Rules

- Only process current-day emails in v1.
- Use Gmail `messageId` as unique identifier.
- If a message cannot be confidently parsed, store it with `needsHumanReview=true` instead of dropping it.
- Do not block the entire sync if one email fails to parse.
- Support both manual sync and scheduled sync.
- Do not parse the full historical inbox in v1.
- Do not implement Gmail push notifications in v1.

---

## Suggested Gmail Scopes

Use the minimum required scope for reading message content needed for parsing. Gmail API is the appropriate API for mailbox access in web applications. [web:296]

Prefer a read-only scope if sufficient for your implementation.

---

## Validation and Quality

Implement:
- Pydantic request/response schemas
- repository/service separation
- retry-safe sync logic
- proper logging
- clear error handling for OAuth and Gmail API failures
- clear fallback when Gmail account is disconnected or token is expired

Suggested indexes:
- `linked_accounts`: `{ userId: 1, provider: 1 }` unique
- `email_expenses`: `{ userId: 1, gmailMessageId: 1 }` unique
- `email_expenses`: `{ userId: 1, transactionAt: -1 }`
- `email_expenses`: `{ userId: 1, category: 1, transactionAt: -1 }`
- `email_sync_runs`: `{ userId: 1, startedAt: -1 }`

---

## API Response Envelope

Use the same API format as the existing backend:

```json
{
  "success": true,
  "data": {...},
  "message": "..."
}
```

Error format:

```json
{
  "success": false,
  "error": {
    "code": "...",
    "message": "..."
  }
}
```

---

## README Expectations

Update the README with:
- Gmail OAuth setup steps
- required Google Cloud project settings
- environment variables
- how to run manual Gmail sync
- sample cURL for connect/sync/list expenses

---

## Expected Outcome

At the end, the backend should support this flow:

1. User connects Gmail.
2. Manual or scheduled sync fetches current-day expense-related emails.
3. Backend parses structured expense records from those emails.
4. Email expenses are stored in MongoDB.
5. Unified expense API returns both receipt and Gmail expenses in one dashboard feed.
6. Summary API shows total spend across both sources.

Build this enhancement now, cleanly integrated into the existing FastAPI + MongoDB backend.
