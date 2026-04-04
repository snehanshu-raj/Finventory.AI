# Build Prompt: AI Finance + Grocery Manager Backend

Build a production-style backend in **Python 3.11** using **FastAPI** and **MongoDB** for an AI-powered personal finance and grocery manager.

The system should let a user upload a grocery receipt image, extract structured JSON from it, store the receipt in MongoDB, maintain a central inventory of current stock, decrement stock daily based on onboarding consumption assumptions, trigger low-stock reminders, compute price insights across stores, and expose APIs for pantry, expenses, predictions, and shopping recommendations. FastAPI is a standard fit for file-upload APIs and service-style Python backends, while MongoDB is well-suited for flexible receipt documents, event data, and time-based inventory views. [web:246][web:239][web:229]

## Product Goal

Create a backend for a consumer app with this workflow:

1. User completes onboarding with household size, diet habits, staple consumption, units, and notification preferences.
2. User uploads receipt image(s).
3. Backend extracts receipt JSON using an OCR + LLM pipeline.
4. Backend stores raw receipt, normalized line items, and derived observations in MongoDB.
5. Backend updates inventory counts based on purchased items.
6. A scheduled daily job decrements stock using estimated daily consumption.
7. If an item falls below threshold, backend creates a low-stock alert and notification.
8. Backend computes estimated days left, cheapest store insights, expense summaries, and pantry-based meal suggestions.

## Tech Requirements

- Python 3.11
- FastAPI
- Pydantic v2
- Motor or PyMongo for MongoDB
- APScheduler or a simple cron-compatible job runner for daily decrement jobs
- Uvicorn
- python-dotenv
- httpx for external OCR/LLM calls
- Optional: Celery/RQ only if truly needed; otherwise keep architecture simple
- Docker-ready
- Clean modular folder structure
- Type hints everywhere
- Async where useful, but keep code readable

## Deliverables

Generate a complete backend codebase with:

- `app/main.py`
- `app/config.py`
- `app/db.py`
- `app/models/`
- `app/schemas/`
- `app/routes/`
- `app/services/`
- `app/repositories/`
- `app/jobs/`
- `app/utils/`
- `requirements.txt`
- `.env.example`
- `Dockerfile`
- `README.md`

The backend must run locally with Docker and connect to MongoDB.

---

## Core Domain Model

Use these MongoDB collections.

### 1. `users`
Store app user profile and onboarding data.

Fields:
- `_id`
- `email`
- `name`
- `createdAt`
- `updatedAt`
- `householdProfile`
  - `householdSize`
  - `adults`
  - `children`
- `dietProfile`
  - `staples`: array of staple configs
  - each staple config contains:
    - `canonicalItemId`
    - `canonicalName`
    - `dailyConsumptionEstimate`
    - `unit`
    - `thresholdQuantity`
- `preferences`
  - `currency`
  - `locale`
  - `notificationEnabled`
  - `notificationChannels` (for now support in-app and mock email)

### 2. `receipts`
One document per uploaded receipt.

Fields:
- `_id`
- `userId`
- `source`
  - `filename`
  - `contentType`
  - `storagePath`
  - `uploadedAt`
  - `ocrProvider`
  - `ocrStatus`
  - `ocrConfidence`
  - `rawText`
- `merchant`
  - `name`
  - `normalizedName`
  - `storeId`
  - `address`
  - `phone`
- `transaction`
  - `receiptNumber`
  - `purchasedAt`
  - `currency`
  - `subtotal`
  - `tax`
  - `tip`
  - `total`
  - `paymentMethod`
- `items`: array of line items
  - `rawText`
  - `canonicalItemId`
  - `canonicalName`
  - `category`
  - `brand`
  - `quantity`
  - `unit`
  - `normalizedQuantity`
  - `normalizedUnit`
  - `unitPrice`
  - `linePrice`
  - `confidence`
  - `isGrocery`
- `totals`
  - `itemCount`
  - `groceryItemsCount`
  - `nonGroceryItemsCount`
- `derived`
  - `monthBucket`
  - `priceObservationCreated`
  - `inventoryApplied`
- `review`
  - `needsHumanReview`
  - `reviewed`
  - `reviewedAt`

### 3. `inventory_state`
One document per user-item representing current pantry state.

Fields:
- `_id`
- `userId`
- `canonicalItemId`
- `canonicalName`
- `category`
- `currentQuantity`
- `unit`
- `thresholdQuantity`
- `dailyConsumptionEstimate`
- `estimatedDaysLeft`
- `status` (`ok`, `low`, `critical`, `out_of_stock`)
- `lastUpdatedAt`
- `lastReceiptAt`
- `reminderEnabled`
- `lastReminderSentAt`
- `metadata`
  - `sourceConfidence`
  - `lastPurchaseStore`
  - `lastPurchasePrice`

### 4. `inventory_events`
Append-only event log for stock changes.

Fields:
- `_id`
- `userId`
- `canonicalItemId`
- `canonicalName`
- `eventType` (`purchase`, `daily_decrement`, `manual_adjustment`, `receipt_deleted`, `consumption_correction`, `waste_discarded`)
- `deltaQuantity`
- `unit`
- `createdAt`
- `source`
  - `type`
  - `referenceId`
- `meta`

### 5. `price_observations`
Flattened normalized line-item observations for analytics.

Fields:
- `_id`
- `userId`
- `receiptId`
- `canonicalItemId`
- `canonicalName`
- `canonicalCategory`
- `storeName`
- `storeId`
- `purchasedAt`
- `quantity`
- `unit`
- `normalizedQuantity`
- `normalizedUnit`
- `linePrice`
- `unitPrice`
- `promoFlag`
- `brand`
- `confidence`

### 6. `notifications`
Store reminders/alerts.

Fields:
- `_id`
- `userId`
- `type` (`low_stock`, `prediction_alert`, `weekly_summary`)
- `title`
- `message`
- `status` (`pending`, `sent`, `dismissed`, `failed`)
- `channel`
- `context`
- `createdAt`
- `sentAt`

### 7. `price_insights`
Precomputed store-level summaries per item.

Fields:
- `_id`
- `userId`
- `canonicalItemId`
- `canonicalName`
- `window`
- `generatedAt`
- `stores`
  - `storeName`
  - `avgUnitPrice`
  - `samples`
  - `lastSeen`
- `bestStore`
- `confidence`
- `insight`

---

## Functional Requirements

## A. Onboarding APIs

Implement APIs for onboarding and preference management.

### `POST /api/v1/users/onboarding`
Create or update onboarding.

Input example:
```json
{
  "name": "John",
  "email": "john@example.com",
  "householdProfile": {
    "householdSize": 2,
    "adults": 2,
    "children": 0
  },
  "dietProfile": {
    "staples": [
      {
        "canonicalItemId": "atta",
        "canonicalName": "atta",
        "dailyConsumptionEstimate": 0.25,
        "unit": "kg",
        "thresholdQuantity": 1.0
      },
      {
        "canonicalItemId": "rice",
        "canonicalName": "rice",
        "dailyConsumptionEstimate": 0.18,
        "unit": "kg",
        "thresholdQuantity": 1.0
      },
      {
        "canonicalItemId": "milk",
        "canonicalName": "milk",
        "dailyConsumptionEstimate": 0.5,
        "unit": "liter",
        "thresholdQuantity": 1.0
      }
    ]
  },
  "preferences": {
    "currency": "USD",
    "locale": "en-US",
    "notificationEnabled": true,
    "notificationChannels": ["in_app"]
  }
}
```

Behavior:
- Upsert user document.
- For any staple not already in `inventory_state`, create an inventory state doc with zero quantity and the configured threshold and daily consumption values.

### `GET /api/v1/users/{user_id}`
Return profile and onboarding config.

### `PATCH /api/v1/users/{user_id}/staples`
Update staple threshold or daily consumption settings.

---

## B. Receipt Upload and OCR APIs

### `POST /api/v1/receipts/upload`
Multipart file upload for one receipt image.

Behavior:
- Accept jpg/jpeg/png.
- Validate file size and content type.
- Save to local `uploads/` or configurable object storage path.
- Run OCR extraction pipeline.
- Convert extracted content into normalized structured JSON.
- Save receipt doc into MongoDB.
- Create `price_observations` entries for grocery items.
- Apply receipt purchases to `inventory_state`.
- Create corresponding `inventory_events` of type `purchase`.
- Return structured receipt response.

### OCR extraction service requirements
Create a service abstraction, e.g. `ReceiptExtractionService`, with one public function:

```python
async def extract_receipt(file_path: str) -> ExtractedReceipt:
    ...
```

For now, this service may call a vision-capable LLM or OCR provider, but the code must be designed so the provider can be swapped.

Expected extracted JSON schema from OCR stage:
```json
{
  "merchant": {
    "name": "Ralphs",
    "address": "123 Main St",
    "phone": null
  },
  "transaction": {
    "receiptNumber": "A12345",
    "purchasedAt": "2026-04-02T18:10:00Z",
    "currency": "USD",
    "subtotal": 38.40,
    "tax": 3.78,
    "tip": 0,
    "total": 42.18,
    "paymentMethod": "card"
  },
  "items": [
    {
      "rawText": "EGGS LG 12CT",
      "canonicalName": "eggs",
      "category": "dairy_and_eggs",
      "brand": null,
      "quantity": 12,
      "unit": "count",
      "normalizedQuantity": 12,
      "normalizedUnit": "count",
      "linePrice": 4.29,
      "unitPrice": 0.3575,
      "confidence": 0.94,
      "isGrocery": true
    }
  ]
}
```

### Rules for extraction pipeline
- Preserve raw OCR text.
- Normalize merchant/store names to a canonical `normalizedName`.
- Normalize items to canonical pantry names where possible.
- Support partial fallback if exact quantity/unit cannot be inferred.
- Mark low-confidence extraction for review.

### `GET /api/v1/receipts`
List receipts for a user with pagination and optional month/store filters.

### `GET /api/v1/receipts/{receipt_id}`
Return full receipt details.

### `PATCH /api/v1/receipts/{receipt_id}/review`
Allow manual correction of extracted fields or line items.

Behavior:
- Update receipt.
- Rebuild downstream `price_observations` for that receipt.
- Recompute inventory effects if line items changed.

---

## C. Inventory APIs

### `GET /api/v1/inventory`
Return all current inventory items for the user.

Support filters:
- `status=low|critical|ok`
- `category`
- `sortBy=estimatedDaysLeft|currentQuantity|name`

### `GET /api/v1/inventory/low-stock`
Return only low, critical, and out-of-stock items.

### `GET /api/v1/inventory/{canonical_item_id}`
Return one item’s inventory state plus recent history.

Response should include:
- current quantity
- threshold
- estimated days left
- daily consumption estimate
- recent events
- last reminder sent

### `PATCH /api/v1/inventory/{canonical_item_id}`
Manual adjustment endpoint.

Input example:
```json
{
  "currentQuantity": 2.5,
  "unit": "kg",
  "reason": "manual correction"
}
```

Behavior:
- Update `inventory_state`.
- Insert `inventory_events` with `eventType=manual_adjustment`.
- Recompute status and estimated days left.

---

## D. Prediction and Analytics APIs

### `GET /api/v1/predictions`
Return predicted run-out timeline for all inventory items.

Each item should include:
- `canonicalItemId`
- `canonicalName`
- `currentQuantity`
- `dailyConsumptionEstimate`
- `estimatedDaysLeft`
- `predictedRunOutDate`
- `status`

Prediction formula for now:

`estimatedDaysLeft = currentQuantity / dailyConsumptionEstimate`

Guardrails:
- If `dailyConsumptionEstimate <= 0`, return null for estimatedDaysLeft.
- Never return negative quantity; clamp at zero.

### `GET /api/v1/analytics/expenses/summary`
Return spending summary by:
- current month
- previous month
- by store
- by category
- top spend items

### `GET /api/v1/analytics/prices/best-store`
Query params:
- `item=eggs`
- `window=30d`

Return best store insight from precomputed or on-demand aggregation.

Required logic:
- Compare only normalized unit prices.
- Use recent observations in specified window.
- Require minimum sample threshold before claiming a store is best.
- Include confidence score.

### `GET /api/v1/analytics/prices/compare`
Return multi-store comparison for a given item or category.

### `GET /api/v1/analytics/dashboard`
Combined dashboard response with:
- monthly spend
- low stock count
- items likely to run out in next 7 days
- top stores by spend
- top opportunities to save money based on known price observations

---

## E. Meal Suggestion / LLM APIs

### `POST /api/v1/meals/suggest`
Input example:
```json
{
  "userId": "...",
  "constraints": {
    "maxPrepMinutes": 20,
    "vegetarian": false,
    "budgetMode": true
  }
}
```

Behavior:
- Read current pantry from `inventory_state`.
- Select items with meaningful remaining quantity.
- Ask LLM for meals that can be made from current pantry.
- Return structured meals, missing ingredients, and a short shopping list.

Response should include:
- meal title
- short description
- pantry ingredients used
- missing ingredients
- prep time
- why suggested

Important:
- LLM should only suggest recipes and explain reasoning.
- Inventory math and stock decisions must stay deterministic in backend logic.

### `POST /api/v1/shopping/suggest`
Generate smart shopping suggestions based on:
- low stock items
- upcoming run-out predictions
- store price insights
- optional budget limit

Return:
- must buy now
- buy soon
- cheapest known store per item when enough data exists

---

## F. Notification APIs

### `GET /api/v1/notifications`
List notifications.

### `POST /api/v1/notifications/test`
Create a mock test notification.

### `PATCH /api/v1/notifications/{notification_id}`
Mark as dismissed or read.

---

## Background Jobs

Implement background jobs in a clean `jobs/` module.

### 1. Daily stock decrement job
Runs once per day.

Logic:
- Fetch all `inventory_state` docs.
- For each item with `dailyConsumptionEstimate > 0`, subtract that value from `currentQuantity`.
- Clamp to zero.
- Create `inventory_events` entry with `eventType=daily_decrement`.
- Recompute:
  - `estimatedDaysLeft`
  - `predictedRunOutDate`
  - `status`
- If quantity crosses below threshold and reminders are enabled, create a low-stock notification.

### 2. Price insight aggregation job
Runs daily or on demand.

Logic:
- Aggregate `price_observations` by user + canonicalItemId + store across recent window.
- Compute average unit price, sample count, last seen.
- Pick `bestStore` if enough samples exist.
- Write summary to `price_insights`.

### 3. Weekly summary job
Optional but scaffold it.
Generate weekly summaries of:
- spend
- low stock items
- upcoming run-outs
- best savings opportunities

---

## Business Logic Rules

### Inventory status rules
- `ok`: currentQuantity > thresholdQuantity
- `low`: currentQuantity <= thresholdQuantity
- `critical`: currentQuantity <= thresholdQuantity * 0.5
- `out_of_stock`: currentQuantity <= 0

### Reminder rules
- Send alert when item crosses from above threshold to below threshold.
- Do not spam daily.
- Store `lastReminderSentAt`.
- Optional cooldown: 3 days.

### Price insight rules
- Never compare raw line-item strings directly.
- Always compare canonical normalized items.
- Compare by unit price, not pack price.
- Require a minimum sample count before making store recommendations.
- Include `confidence` in responses.

### Receipt correction rules
- If a receipt is edited after upload, reverse and replay downstream inventory and price effects for that receipt.

---

## API Response Requirements

All APIs should return consistent JSON envelopes like:

```json
{
  "success": true,
  "data": {...},
  "message": "..."
}
```

On errors:

```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "..."
  }
}
```

Use proper HTTP status codes.

---

## Validation and Quality

Implement:
- request/response schemas with Pydantic
- service/repository separation
- indexes for hot queries
- logging
- env-based config
- clear exception handling
- lightweight unit-test-ready architecture

Suggested MongoDB indexes:
- `receipts`: `{ userId: 1, 'transaction.purchasedAt': -1 }`
- `inventory_state`: `{ userId: 1, canonicalItemId: 1 }` unique
- `inventory_state`: `{ userId: 1, status: 1 }`
- `inventory_events`: `{ userId: 1, canonicalItemId: 1, createdAt: -1 }`
- `price_observations`: `{ userId: 1, canonicalItemId: 1, purchasedAt: -1 }`
- `price_insights`: `{ userId: 1, canonicalItemId: 1, window: 1 }`

---

## Code Style Requirements

- Keep functions small and readable.
- No giant monolithic route files.
- Use repository classes for database access.
- Use service classes for business logic.
- Keep OCR/LLM provider behind interfaces.
- Make it easy to swap local storage with S3 later.
- Include docstrings for public functions.
- Include example cURL requests in README.

---

## Non-Goals for v1

Do not implement these unless trivial:
- multi-user auth system beyond simple userId-based flow or mocked auth
- complex ML forecasting beyond deterministic daily consumption estimates
- full production notification providers like Twilio or Firebase
- barcode scanning
- retailer API integrations

Keep v1 focused and working.

---

## Nice-to-Have If Time Permits

- batch receipt upload
- image preprocessing before OCR
- duplicate receipt detection
- merchant normalization dictionary
- item canonicalization helper map
- budget-based shopping plan endpoint
- weekly summary notification endpoint

---

## Expected Outcome

At the end, the backend should support this demo flow:

1. Create user onboarding with staple consumption assumptions.
2. Upload receipt image.
3. Extract and store structured receipt JSON in MongoDB.
4. Auto-update pantry quantities.
5. View current inventory and low-stock items.
6. Run prediction API and show estimated run-out dates.
7. Generate store-price insights from observations.
8. Suggest meals from current pantry.
9. Trigger low-stock reminder when threshold is crossed.

Build the code now.
