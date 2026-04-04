# AI Finance & Grocery Manager Backend

AI-powered personal finance and grocery manager backend built with **FastAPI** + **MongoDB**.

## Features

- Receipt image upload with OCR extraction (Gemini Flash / Claude / Mock)
- Automatic inventory tracking and daily stock decrement
- Price analytics and best-store insights
- LLM-powered meal suggestions from pantry
- Smart shopping recommendations
- Low-stock notifications with cooldown
- Expense summaries and dashboard

## Quick Start

### With Docker Compose (recommended)

```bash
cp .env.example .env
# Edit .env with your API keys if using Gemini/Claude
docker compose up --build
```

### Without Docker

```bash
# Start MongoDB locally
# Install dependencies
pip install -r requirements.txt

cp .env.example .env
# Edit .env as needed

uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

API docs: http://localhost:8000/docs

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MONGODB_URL` | `mongodb://localhost:27017` | MongoDB connection string |
| `MONGODB_DB_NAME` | `expense_tracker` | Database name |
| `LLM_PROVIDER` | `mock` | `gemini`, `claude`, or `mock` |
| `GEMINI_API_KEY` | (none) | Required if LLM_PROVIDER=gemini |
| `CLAUDE_API_KEY` | (none) | Required if LLM_PROVIDER=claude |
| `UPLOAD_DIR` | `./uploads` | Receipt image storage path |
| `REMINDER_COOLDOWN_DAYS` | `3` | Days between repeat reminders |
| `MIN_PRICE_SAMPLES` | `3` | Min samples for store recommendation |

## API Endpoints

### A. Users / Onboarding

```bash
# Create or update onboarding
curl -X POST http://localhost:8000/api/v1/users/onboarding \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John",
    "email": "john@example.com",
    "household_profile": {"household_size": 2, "adults": 2, "children": 0},
    "diet_profile": {
      "staples": [
        {"canonical_item_id": "milk", "canonical_name": "milk", "daily_consumption_estimate": 0.5, "unit": "liter", "threshold_quantity": 1.0},
        {"canonical_item_id": "rice", "canonical_name": "rice", "daily_consumption_estimate": 0.18, "unit": "kg", "threshold_quantity": 1.0},
        {"canonical_item_id": "atta", "canonical_name": "atta", "daily_consumption_estimate": 0.25, "unit": "kg", "threshold_quantity": 1.0}
      ]
    },
    "preferences": {"currency": "USD", "locale": "en-US", "notification_enabled": true, "notification_channels": ["in_app"]}
  }'

# Get user profile
curl http://localhost:8000/api/v1/users/{user_id}

# Update staples
curl -X PATCH http://localhost:8000/api/v1/users/{user_id}/staples \
  -H "Content-Type: application/json" \
  -d '{"staples": [{"canonical_item_id": "milk", "canonical_name": "milk", "daily_consumption_estimate": 0.6, "unit": "liter", "threshold_quantity": 1.5}]}'
```

### B. Receipts

```bash
# Upload receipt image
curl -X POST http://localhost:8000/api/v1/receipts/upload \
  -F "user_id={user_id}" \
  -F "file=@receipt.jpg"

# List receipts
curl "http://localhost:8000/api/v1/receipts?user_id={user_id}&page=1&page_size=10"

# Get receipt details
curl http://localhost:8000/api/v1/receipts/{receipt_id}

# Review/correct receipt
curl -X PATCH http://localhost:8000/api/v1/receipts/{receipt_id}/review \
  -H "Content-Type: application/json" \
  -d '{"merchant_name": "Corrected Store Name"}'
```

### C. Inventory

```bash
# List all inventory
curl "http://localhost:8000/api/v1/inventory?user_id={user_id}"

# Filter by status
curl "http://localhost:8000/api/v1/inventory?user_id={user_id}&status=low"

# Get low-stock items
curl "http://localhost:8000/api/v1/inventory/low-stock?user_id={user_id}"

# Get item detail with history
curl "http://localhost:8000/api/v1/inventory/milk?user_id={user_id}"

# Manual adjustment
curl -X PATCH "http://localhost:8000/api/v1/inventory/milk?user_id={user_id}" \
  -H "Content-Type: application/json" \
  -d '{"current_quantity": 2.5, "unit": "liter", "reason": "manual correction"}'
```

### D. Analytics & Predictions

```bash
# Predictions (run-out timeline)
curl "http://localhost:8000/api/v1/analytics/predictions?user_id={user_id}"

# Expense summary
curl "http://localhost:8000/api/v1/analytics/expenses/summary?user_id={user_id}"

# Best store for an item
curl "http://localhost:8000/api/v1/analytics/prices/best-store?user_id={user_id}&item=eggs&window=30d"

# Price comparison
curl "http://localhost:8000/api/v1/analytics/prices/compare?user_id={user_id}&item=milk"

# Dashboard
curl "http://localhost:8000/api/v1/analytics/dashboard?user_id={user_id}"
```

### E. Meals & Shopping

```bash
# Meal suggestions
curl -X POST http://localhost:8000/api/v1/meals/suggest \
  -H "Content-Type: application/json" \
  -d '{"user_id": "{user_id}", "constraints": {"max_prep_minutes": 20, "vegetarian": false, "budget_mode": true}}'

# Shopping suggestions
curl -X POST http://localhost:8000/api/v1/shopping/suggest \
  -H "Content-Type: application/json" \
  -d '{"user_id": "{user_id}", "budget_limit": 50.0}'
```

### F. Notifications

```bash
# List notifications
curl "http://localhost:8000/api/v1/notifications?user_id={user_id}"

# Create test notification
curl -X POST http://localhost:8000/api/v1/notifications/test \
  -H "Content-Type: application/json" \
  -d '{"user_id": "{user_id}", "title": "Test", "message": "Hello!"}'

# Dismiss notification
curl -X PATCH http://localhost:8000/api/v1/notifications/{notification_id} \
  -H "Content-Type: application/json" \
  -d '{"status": "dismissed"}'
```

## Project Structure

```
app/
├── main.py              # FastAPI app with lifespan
├── config.py            # Pydantic settings from .env
├── db.py                # Motor async MongoDB client
├── models/              # Domain models (Pydantic)
├── schemas/             # Request/response schemas
├── routes/              # FastAPI route handlers
├── services/            # Business logic layer
│   └── llm_provider.py  # Gemini/Claude/Mock providers
├── repositories/        # MongoDB data access layer
├── jobs/                # Background jobs (APScheduler)
└── utils/               # Helpers (response, exceptions, storage)
```

## Background Jobs

| Job | Schedule | Description |
|-----|----------|-------------|
| Daily Decrement | 2:00 AM daily | Decrements stock by daily consumption |
| Price Aggregation | 3:00 AM daily | Aggregates price observations into insights |
| Weekly Summary | Monday 8:00 AM | Generates weekly summary notifications |

## LLM Provider Configuration

Set `LLM_PROVIDER` in `.env`:

- **`mock`** – Returns sample data (no API key required, good for local dev)
- **`gemini`** – Uses Gemini Flash API (requires `GEMINI_API_KEY`)
- **`claude`** – Uses Claude API (requires `CLAUDE_API_KEY`)
