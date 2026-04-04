# API Docs – Complete Reference

> **Base URL**: `http://localhost:8000`
> **Interactive Docs**: `http://localhost:8000/docs`
> **LLM Provider**: Set in `.env` → `LLM_PROVIDER=mock|gemini|claude`

---

## Dependency Flow (Read This First)

The APIs are designed to be used in a specific order. Here's what unlocks what:

```
1. Onboard User  ──────►  user_id created
       │
2. Upload Receipt  ────►  receipt stored + inventory populated + price observations created
       │
       ├──► Inventory APIs now return data
       ├──► Analytics/Predictions now have data to analyze
       ├──► Price comparison needs 2+ receipts from different stores
       └──► Meal suggestions use current inventory
```

| API Group           | Minimum Prerequisite                                      |
|---------------------|-----------------------------------------------------------|
| Users               | None — this is the starting point                         |
| Receipt Upload      | A user must exist (need `user_id`)                        |
| Receipt List/Detail | At least 1 receipt uploaded                               |
| Inventory List      | At least 1 receipt uploaded (auto-populates inventory)    |
| Inventory Adjust    | Item must exist in inventory                              |
| Predictions         | Inventory items with `dailyConsumptionEstimate > 0`       |
| Expense Summary     | At least 1 receipt with price observations                |
| Best Store          | 2+ receipts from different stores for the same item       |
| Price Compare       | Same as Best Store                                        |
| Dashboard           | Works with any data; richer with more receipts            |
| Meal Suggestions    | Inventory items with `currentQuantity > 0` + LLM provider |
| Shopping Suggest    | Inventory items exist                                     |
| Notifications       | None — can create test notifications anytime              |

---

## A. Users / Onboarding

### `POST /api/v1/users/onboarding`

**When to use**: First API to call. Creates a new user or updates an existing one. Also initializes inventory for each staple defined.

**Prerequisite**: None.

**Request Body**:
```json
{
  "name": "John",
  "email": "john@example.com",
  "household_profile": {
    "household_size": 2,
    "adults": 2,
    "children": 0
  },
  "diet_profile": {
    "staples": [
      {
        "canonical_item_id": "milk",
        "canonical_name": "milk",
        "daily_consumption_estimate": 0.5,
        "unit": "liter",
        "threshold_quantity": 1.0
      },
      {
        "canonical_item_id": "rice",
        "canonical_name": "rice",
        "daily_consumption_estimate": 0.18,
        "unit": "kg",
        "threshold_quantity": 1.0
      },
      {
        "canonical_item_id": "eggs",
        "canonical_name": "eggs",
        "daily_consumption_estimate": 2.0,
        "unit": "count",
        "threshold_quantity": 6.0
      }
    ]
  },
  "preferences": {
    "currency": "USD",
    "locale": "en-US",
    "notification_enabled": true,
    "notification_channels": ["in_app"]
  }
}
```

**Required fields**: `name`, `email`, `household_profile` (with `household_size ≥ 1`)

**What happens behind the scenes**:
- Creates/upserts user doc in `users` collection
- For each staple → creates an `inventory_state` doc with `currentQuantity: 0`, `status: "out_of_stock"`, and the configured `dailyConsumptionEstimate` and `thresholdQuantity`
- Returns the full user profile with generated `user_id`

**Response** (in `data`):
```json
{
  "id": "660e...",
  "email": "john@example.com",
  "name": "John",
  "created_at": "2026-04-03T20:30:00Z",
  "updated_at": "2026-04-03T20:30:00Z",
  "household_profile": { ... },
  "diet_profile": { "staples": [ ... ] },
  "preferences": { ... }
}
```

---

### `GET /api/v1/users/{user_id}`

**When to use**: Fetch the user profile after onboarding.

**Prerequisite**: User must exist (call onboarding first).

```bash
curl http://localhost:8000/api/v1/users/660e1234abcd5678ef901234
```

**Returns**: Same shape as onboarding response.

---

### `PATCH /api/v1/users/{user_id}/staples`

**When to use**: Update how much of a staple you consume daily or change thresholds.

**Prerequisite**: User must exist.

```json
{
  "staples": [
    {
      "canonical_item_id": "milk",
      "canonical_name": "milk",
      "daily_consumption_estimate": 0.8,
      "unit": "liter",
      "threshold_quantity": 2.0
    }
  ]
}
```

**What happens**: Updates the user's diet profile AND updates the matching `inventory_state` docs with new `dailyConsumptionEstimate` and `thresholdQuantity` values.

---

## B. Receipts

### `POST /api/v1/receipts/upload`

**When to use**: Upload a receipt image. This is the CORE action that populates inventory, creates price observations, and stores the receipt.

**Prerequisite**: User must exist. Valid image file (JPEG/PNG, max 10 MB).

**Request**: `multipart/form-data`

```bash
curl -X POST http://localhost:8000/api/v1/receipts/upload \
  -F "user_id=660e1234abcd5678ef901234" \
  -F "file=@receipt.jpg"
```

**What happens (full pipeline)**:
1. Saves image to `uploads/` directory
2. Sends image to LLM (Gemini/Claude/Mock) for OCR extraction
3. Parses structured data: merchant, items, totals
4. Inserts receipt document into `receipts` collection
5. Creates `price_observations` for each grocery item
6. Creates/updates `inventory_state` for each grocery item (adds quantity)
7. Logs `inventory_events` (type: `purchase`) for each item

**LLM Providers**:
- `mock`: Returns 3 sample items (milk $4.29, whole wheat bread $3.49, eggs $5.99) — no API key needed
- `gemini`: Real OCR via Gemini 2.5 Flash — needs `GEMINI_API_KEY`
- `claude`: Real OCR via Claude — needs `CLAUDE_API_KEY`

**Response** (in `data`):
```json
{
  "id": "660e...",
  "user_id": "660e...",
  "merchant": {
    "name": "Trader Joe's",
    "normalized_name": "trader joes",
    "address": "123 Main St",
    "phone": null
  },
  "transaction": {
    "receipt_number": "12345",
    "purchased_at": "2026-04-03T12:00:00Z",
    "currency": "USD",
    "subtotal": 12.77,
    "tax": 0.99,
    "total": 13.76,
    "payment_method": "credit_card"
  },
  "items": [
    {
      "raw_text": "ORGANIC MILK 1GAL",
      "canonical_item_id": "milk",
      "canonical_name": "milk",
      "category": "dairy",
      "quantity": 1.0,
      "unit": "gallon",
      "normalized_quantity": 3.785,
      "normalized_unit": "liter",
      "line_price": 4.29,
      "confidence": 0.95,
      "is_grocery": true
    }
  ],
  "totals": { "itemCount": 3, "groceryItemsCount": 3, "nonGroceryItemsCount": 0 },
  "review": { "needsHumanReview": false, "reviewed": false }
}
```

**Common errors**:
- `429 Too Many Requests` — Gemini free tier rate limit. Wait 60s or use `mock`.
- `EXTRACTION_ERROR` — LLM failed to parse. Try a clearer image.
- `VALIDATION_ERROR` — Wrong file type or file too large.

---

### `GET /api/v1/receipts`

**When to use**: List all receipts for a user with pagination & filters.

**Prerequisite**: At least 1 uploaded receipt.

```bash
# Basic listing
curl "http://localhost:8000/api/v1/receipts?user_id=USER_ID"

# With filters
curl "http://localhost:8000/api/v1/receipts?user_id=USER_ID&month=2026-04&store=walmart&page=1&page_size=10"
```

**Query params**: `user_id` (required), `page`, `page_size`, `month` (YYYY-MM), `store`

**Response** (in `data`):
```json
{
  "items": [
    {
      "id": "660e...",
      "merchant_name": "Trader Joe's",
      "total": 13.76,
      "item_count": 3,
      "purchased_at": "2026-04-03T12:00:00Z"
    }
  ],
  "pagination": { "page": 1, "page_size": 20, "total": 1, "total_pages": 1 }
}
```

---

### `GET /api/v1/receipts/{receipt_id}`

**Prerequisite**: Receipt must exist.

```bash
curl http://localhost:8000/api/v1/receipts/660e1234abcd5678ef901234
```

**Returns**: Full receipt with all items (same shape as upload response).

---

### `PATCH /api/v1/receipts/{receipt_id}/review`

**When to use**: Correct OCR mistakes. This **reverses** the old inventory/price effects and **replays** with corrected data.

**Prerequisite**: Receipt must exist.

```json
{
  "merchant_name": "Corrected Store Name",
  "items": [
    {
      "raw_text": "ORG MILK",
      "canonical_name": "milk",
      "category": "dairy",
      "quantity": 2.0,
      "unit": "gallon",
      "line_price": 8.58,
      "confidence": 1.0,
      "is_grocery": true
    }
  ]
}
```

**All fields are optional** — only send what you want to correct.

---

## C. Inventory

### `GET /api/v1/inventory`

**When to use**: View current pantry state.

**Prerequisite**: Inventory items exist (created via onboarding staples or receipt upload).

```bash
# All items
curl "http://localhost:8000/api/v1/inventory?user_id=USER_ID"

# Filtered
curl "http://localhost:8000/api/v1/inventory?user_id=USER_ID&status=low&category=dairy&sort_by=estimatedDaysLeft"
```

**Query params**: `user_id` (required), `status` (ok|low|critical|out_of_stock), `category`, `sort_by` (estimatedDaysLeft|currentQuantity|name)

**Response** (in `data`): Array of:
```json
{
  "canonical_item_id": "milk",
  "canonical_name": "milk",
  "category": "dairy",
  "current_quantity": 3.785,
  "unit": "liter",
  "threshold_quantity": 1.0,
  "daily_consumption_estimate": 0.5,
  "estimated_days_left": 7.6,
  "status": "ok",
  "last_updated_at": "2026-04-03T20:30:00Z",
  "last_receipt_at": "2026-04-03T20:30:00Z",
  "reminder_enabled": true,
  "last_reminder_sent_at": null
}
```

**Status values explained**:
| Status | Meaning |
|--------|---------|
| `ok` | Quantity above threshold |
| `low` | Quantity ≤ threshold |
| `critical` | Quantity ≤ 50% of threshold |
| `out_of_stock` | Quantity ≤ 0 |

---

### `GET /api/v1/inventory/low-stock`

**When to use**: Quick view of items needing attention.

**Prerequisite**: Same as inventory list.

```bash
curl "http://localhost:8000/api/v1/inventory/low-stock?user_id=USER_ID"
```

**Returns**: Only items with status `low`, `critical`, or `out_of_stock`.

---

### `GET /api/v1/inventory/{canonical_item_id}`

**When to use**: View one item's state plus its event history (purchases, decrements, adjustments).

**Prerequisite**: Item must exist in inventory.

```bash
curl "http://localhost:8000/api/v1/inventory/milk?user_id=USER_ID"
```

**Response** (in `data`):
```json
{
  "item": { "canonical_item_id": "milk", "current_quantity": 3.785, "status": "ok", "..." : "..." },
  "recent_events": [
    {
      "id": "660e...",
      "event_type": "purchase",
      "delta_quantity": 3.785,
      "unit": "liter",
      "created_at": "2026-04-03T20:30:00Z",
      "source": { "type": "receipt", "referenceId": "660e..." }
    }
  ]
}
```

**Event types**: `purchase`, `manual_adjustment`, `daily_decrement`, `onboarding_init`

---

### `PATCH /api/v1/inventory/{canonical_item_id}`

**When to use**: Manually correct inventory count (e.g., you ate something, or count was wrong).

**Prerequisite**: Item must exist in inventory.

```bash
curl -X PATCH "http://localhost:8000/api/v1/inventory/milk?user_id=USER_ID" \
  -H "Content-Type: application/json" \
  -d '{"current_quantity": 2.0, "unit": "liter", "reason": "spilled some"}'
```

**Required fields**: `current_quantity` (≥ 0), `unit`

---

### `DELETE /api/v1/inventory/reset`

**When to use**: Wipe ALL inventory data for a user (for testing/starting over).

**Prerequisite**: User must exist.

```bash
curl -X DELETE "http://localhost:8000/api/v1/inventory/reset?user_id=USER_ID"
```

**Response** (in `data`):
```json
{ "states_deleted": 5, "events_deleted": 23 }
```

> ⚠️ This is destructive — deletes all `inventory_state` and `inventory_events` for the user. Does NOT delete receipts or price observations.

---

## D. Analytics & Predictions

### `GET /api/v1/analytics/predictions`

**When to use**: See predicted run-out dates for all inventory items.

**Prerequisite**: Inventory items must exist with `dailyConsumptionEstimate > 0` (set via onboarding staples).

**Items without a daily rate will have `estimated_days_left: null`** — they were likely discovered via receipt (not onboarded as staples).

```bash
curl "http://localhost:8000/api/v1/analytics/predictions?user_id=USER_ID"
```

**Response** (in `data`): Array of:
```json
{
  "canonical_item_id": "milk",
  "canonical_name": "milk",
  "current_quantity": 3.785,
  "daily_consumption_estimate": 0.5,
  "estimated_days_left": 7.6,
  "predicted_run_out_date": "2026-04-11T00:00:00Z",
  "status": "ok"
}
```

---

### `GET /api/v1/analytics/expenses/summary`

**When to use**: See spending breakdowns for the current month.

**Prerequisite**: At least 1 receipt uploaded (price observations must exist).

```bash
curl "http://localhost:8000/api/v1/analytics/expenses/summary?user_id=USER_ID"
```

**Response** (in `data`):
```json
{
  "current_month_total": 45.23,
  "previous_month_total": 120.50,
  "by_store": [
    { "store_name": "trader joes", "total_spend": 30.00, "receipt_count": 2 }
  ],
  "by_category": [
    { "category": "dairy", "total_spend": 12.50, "item_count": 3 }
  ],
  "top_spend_items": [
    { "canonical_name": "milk", "total_spend": 8.58, "purchase_count": 2 }
  ]
}
```

---

### `GET /api/v1/analytics/prices/best-store`

**When to use**: Find which store sells a specific item the cheapest.

**Prerequisite**: Needs price observations from **2+ different stores** for the same item. Needs at least `MIN_PRICE_SAMPLES` (default: 3) records for a confident recommendation.

```bash
curl "http://localhost:8000/api/v1/analytics/prices/best-store?user_id=USER_ID&item=milk&window=30d"
```

**Query params**: `user_id`, `item` (canonical_item_id), `window` (default: `30d`)

**Response** (in `data`):
```json
{
  "canonical_item_id": "milk",
  "best_store": "costco",
  "stores": [
    { "store_name": "costco", "avg_unit_price": 3.50, "samples": 5, "last_seen": "..." },
    { "store_name": "trader joes", "avg_unit_price": 4.29, "samples": 3, "last_seen": "..." }
  ],
  "confidence": 0.63,
  "insight": "Best store for milk is costco"
}
```

**If not enough data**: `best_store` will be `null` and `insight` will say "Not enough data".

---

### `GET /api/v1/analytics/prices/compare`

**When to use**: Same as best-store but focused on multi-store comparison.

```bash
curl "http://localhost:8000/api/v1/analytics/prices/compare?user_id=USER_ID&item=eggs&window=30d"
```

---

### `GET /api/v1/analytics/dashboard`

**When to use**: One-call dashboard combining spend, low stock, and run-out alerts.

**Prerequisite**: Works with any amount of data; more data = richer dashboard.

```bash
curl "http://localhost:8000/api/v1/analytics/dashboard?user_id=USER_ID"
```

**Response** (in `data`):
```json
{
  "monthly_spend": 45.23,
  "low_stock_count": 2,
  "items_running_out_7days": [
    { "canonical_name": "eggs", "estimated_days_left": 3.0, "status": "low" }
  ],
  "top_stores": [
    { "store_name": "trader joes", "total_spend": 30.00, "receipt_count": 2 }
  ],
  "savings_opportunities": []
}
```

---

## E. Meals & Shopping

### `POST /api/v1/meals/suggest`

**When to use**: Get meal ideas based on what's currently in your pantry.

**Prerequisite**: Inventory items with `currentQuantity > 0`. If pantry is empty → returns `{"meals": []}`. Uses the configured LLM provider for generation.

```bash
curl -X POST http://localhost:8000/api/v1/meals/suggest \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "USER_ID",
    "constraints": {
      "max_prep_minutes": 30,
      "vegetarian": false,
      "budget_mode": true
    }
  }'
```

**All constraint fields are optional**.

**Response** (in `data`):
```json
{
  "meals": [
    {
      "title": "Simple Egg Fried Rice",
      "description": "Quick fried rice using pantry staples",
      "pantry_ingredients_used": ["rice", "eggs", "oil"],
      "missing_ingredients": ["green onions"],
      "prep_time_minutes": 15,
      "why_suggested": "Uses 3 pantry items, budget-friendly, under 30 mins"
    }
  ]
}
```

**With `mock` provider**: Returns 2 sample meals (Pantry Pasta, Rice Bowl).

---

### `POST /api/v1/shopping/suggest`

**When to use**: Get smart shopping list based on what's running low + price insights.

**Prerequisite**: Inventory items must exist. Items are categorized by urgency.

```bash
curl -X POST http://localhost:8000/api/v1/shopping/suggest \
  -H "Content-Type: application/json" \
  -d '{"user_id": "USER_ID", "budget_limit": 50.0}'
```

**Response** (in `data`):
```json
{
  "must_buy_now": [
    {
      "canonical_item_id": "milk",
      "canonical_name": "milk",
      "current_quantity": 0,
      "threshold_quantity": 1.0,
      "estimated_days_left": 0,
      "cheapest_store": "costco",
      "estimated_price": 3.50
    }
  ],
  "buy_soon": [
    {
      "canonical_item_id": "eggs",
      "canonical_name": "eggs",
      "current_quantity": 3,
      "estimated_days_left": 1.5,
      "cheapest_store": null,
      "estimated_price": null
    }
  ]
}
```

**Categorization**:
- `must_buy_now` → status is `out_of_stock` or `critical`
- `buy_soon` → status is `low`

---

## F. Notifications

### `GET /api/v1/notifications`

**When to use**: List all notifications for a user (system-generated low-stock alerts + manual test ones).

**Prerequisite**: None (returns empty list if no notifications).

```bash
curl "http://localhost:8000/api/v1/notifications?user_id=USER_ID&page=1&page_size=20"
```

**Response** (in `data`):
```json
{
  "items": [
    {
      "id": "660e...",
      "user_id": "USER_ID",
      "type": "low_stock",
      "title": "Low stock: milk",
      "message": "milk is low. Current quantity: 0.5 liter.",
      "status": "sent",
      "channel": "in_app",
      "context": { "canonicalItemId": "milk", "currentQuantity": 0.5 },
      "created_at": "2026-04-03T02:00:00Z",
      "sent_at": "2026-04-03T02:00:01Z"
    }
  ],
  "pagination": { "page": 1, "page_size": 20, "total": 1, "total_pages": 1 }
}
```

**Notification types**: `low_stock` (auto-generated by daily decrement job), `weekly_summary` (weekly job), `low_stock` (manual test)

---

### `POST /api/v1/notifications/test`

**When to use**: Test the notification system without waiting for background jobs.

**Prerequisite**: None.

```bash
curl -X POST http://localhost:8000/api/v1/notifications/test \
  -H "Content-Type: application/json" \
  -d '{"user_id": "USER_ID", "title": "Test Alert", "message": "This is a test!"}'
```

---

### `PATCH /api/v1/notifications/{notification_id}`

**When to use**: Dismiss or mark a notification as read.

```bash
curl -X PATCH http://localhost:8000/api/v1/notifications/660e1234abcd5678ef901234 \
  -H "Content-Type: application/json" \
  -d '{"status": "dismissed"}'
```

---

## G. Health

### `GET /health`

**Prerequisite**: None. Always works.

```bash
curl http://localhost:8000/health
```

```json
{ "success": true, "data": { "status": "healthy" }, "message": "OK" }
```

---

## Background Jobs (Automatic)

These run on a schedule via APScheduler. You don't call them directly.

| Job | Schedule | What It Does | What It Needs |
|-----|----------|-------------|---------------|
| **Daily Decrement** | 2:00 AM daily | Subtracts `dailyConsumptionEstimate` from each item's `currentQuantity`. Creates `daily_decrement` events. Sends `low_stock` notifications when items cross threshold. | Inventory items with `dailyConsumptionEstimate > 0` |
| **Price Aggregation** | 3:00 AM daily | Aggregates `price_observations` into `price_insights` (per-item store summaries). Powers the best-store and compare APIs. | Price observations from uploaded receipts |
| **Weekly Summary** | Monday 8:00 AM | Creates `weekly_summary` notification listing low-stock items. | Inventory items exist |

---

## Testing Workflow (Recommended Order)

```
1. POST /api/v1/users/onboarding        → get user_id
2. POST /api/v1/receipts/upload          → upload receipt (use mock LLM first)
3. GET  /api/v1/inventory                → see populated pantry
4. GET  /api/v1/analytics/predictions    → see run-out timeline
5. POST /api/v1/meals/suggest            → get meal ideas
6. POST /api/v1/shopping/suggest         → get shopping list
7. GET  /api/v1/analytics/dashboard      → see combined dashboard
8. DELETE /api/v1/inventory/reset        → wipe and start over
```

---

## All Response Envelopes

Every response follows this format:

**Success**:
```json
{ "success": true, "data": { ... }, "message": "OK" }
```

**Error**:
```json
{ "success": false, "error": { "code": "NOT_FOUND", "message": "Receipt xyz not found" } }
```

**Error codes**: `NOT_FOUND`, `VALIDATION_ERROR`, `EXTRACTION_ERROR`, `INTERNAL_ERROR`
