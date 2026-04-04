# Gmail Integration Setup Guide

Connect your Gmail to automatically extract expenses from emails (Zelle, PayPal, Amazon, Uber, subscriptions, etc.)

---

## Prerequisites

- Python 3.11+ with `venv` activated
- MongoDB running locally
- The Expense Tracker server code

---

## Step 1: Create a Google Cloud Project & Enable Gmail API

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. **Create a new project** (or select an existing one)
3. Go to **APIs & Services** → **Library** → search **Gmail API** → click **Enable**

---

## Step 2: Configure OAuth Consent Screen

1. Go to **APIs & Services** → [OAuth consent screen](https://console.cloud.google.com/apis/credentials/consent)
2. Choose **External** → **Create**
3. Fill in:
   - **App name**: `Expense Tracker`
   - **User support email**: your email
   - **Developer contact**: your email
4. Click **Save and Continue**
5. On **Scopes**, click **Add or Remove Scopes** → search `gmail.readonly` → check it → **Update** → **Save and Continue**
6. On **Test users**, click **Add Users** → add your Gmail address → **Save and Continue**
7. Click **Back to Dashboard**

> While in "Testing" mode, only test users you added can use it. This is fine for personal use.

---

## Step 3: Create OAuth Credentials

1. Go to **APIs & Services** → [Credentials](https://console.cloud.google.com/apis/credentials)
2. Click **+ Create Credentials** → **OAuth client ID**
3. Choose **Web application**
4. Set **Name**: `Expense Tracker`
5. Under **Authorized redirect URIs**, add **both**:
   ```
   http://localhost:8000/api/v1/integrations/gmail/callback
   http://localhost:9999/callback
   ```
6. Click **Create** → copy the **Client ID** and **Client Secret**

---

## Step 4: Add Credentials to `.env`

Open your `.env` file and add:

```env
GOOGLE_CLIENT_ID=your-client-id-here.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-your-secret-here
```

---

## Step 5: Get Your Refresh Token (One-Time)

Run the included setup script:

```bash
cd /home/srj/expense-tracker
source venv/bin/activate
python scripts/get_refresh_token.py
```

**What happens:**
1. Your browser opens Google's sign-in page
2. Sign in and allow access (if you see a warning, click **Advanced** → **Go to Expense Tracker**)
3. The script prints your refresh token

Copy the output and add it to your `.env`:

```env
GOOGLE_REFRESH_TOKEN=1//06xxxxxxxxxxxxxxxx
```

> This token doesn't expire. You only need to do this once.

---

## Step 6: Start the Server & Sync

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

That's it! Gmail auto-connects on first use. No manual setup API calls needed.

### Sync your emails

```bash
# Sync today's emails
curl -X POST "http://localhost:8000/api/v1/integrations/gmail/sync"

# Sync last 7 days
curl -X POST "http://localhost:8000/api/v1/integrations/gmail/sync?days_back=7"

# Sync last 30 days
curl -X POST "http://localhost:8000/api/v1/integrations/gmail/sync?days_back=30"
```

---

## API Quick Reference

No `user_id` needed on any call — it's set once in `.env` as `DEFAULT_USER_ID`.

```bash
# Check Gmail connection status
curl "http://localhost:8000/api/v1/integrations/gmail/status"

# Sync emails
curl -X POST "http://localhost:8000/api/v1/integrations/gmail/sync?days_back=7"

# Fetch, parse, and preview
curl -X POST "http://localhost:8000/api/v1/integrations/gmail/fetch-and-preview?days_back=7"

# View sync history
curl "http://localhost:8000/api/v1/integrations/gmail/sync-runs"

# List email expenses
curl "http://localhost:8000/api/v1/email-expenses"

# Unified feed (receipts + emails)
curl "http://localhost:8000/api/v1/expenses"

# Spending summary
curl "http://localhost:8000/api/v1/expenses/summary"

# Filter by source
curl "http://localhost:8000/api/v1/expenses?source=gmail"
curl "http://localhost:8000/api/v1/expenses?source=receipt"

# Correct a parsed expense
curl -X PATCH "http://localhost:8000/api/v1/email-expenses/EXPENSE_ID/review" \
  -H "Content-Type: application/json" \
  -d '{"merchant": "Correct Name", "amount": 25.99, "category": "food"}'

# Reset all email expenses (testing only)
curl -X DELETE "http://localhost:8000/api/v1/integrations/gmail/email-expenses/reset"

# Nuclear reset (wipes ALL data)
curl -X DELETE "http://localhost:8000/api/v1/admin/reset"
```

---

## Automatic Polling

Once configured, the backend polls Gmail every **6 hours** (set `GMAIL_SYNC_INTERVAL_HOURS` in `.env` to change). It automatically:
- Searches for expense-related emails
- Deduplicates by Gmail message ID
- Parses with regex (known senders) or LLM fallback
- Stores results in the database

---

## What Emails Get Detected

| Source | Detected As |
|--------|-------------|
| Zelle | `zelle` transfer |
| PayPal | `order_receipt` |
| Amazon | `order_receipt` (shopping) |
| Uber / Lyft | `ride_share` (transport) |
| DoorDash / UberEats / Grubhub | `food_delivery` |
| Netflix / Spotify / Apple / Adobe | `subscription` |
| Credit card alerts | `card_alert` |
| Any email with $ amounts | `other` (LLM fallback) |

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `redirect_uri_mismatch` | Make sure both redirect URIs from Step 3 are added in Google Cloud Console |
| `access_denied` | Add your Gmail as a test user in the OAuth consent screen (Step 2) |
| `OAUTH_REFRESH_FAILED` | Re-run `python scripts/get_refresh_token.py` and update `.env` |
| `0 messages found` | No expense emails in that time range — try `days_back=30` |
| Low confidence / `needs_review` | Correct via the `PATCH .../review` endpoint |
| `429 Too Many Requests` | Gemini API rate limit — wait a minute and retry |

---

## `.env` Summary

```env
# Required for Gmail integration
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-your-secret
GOOGLE_REFRESH_TOKEN=1//06xxxxxxxx

# Optional
GMAIL_SYNC_INTERVAL_HOURS=6          # default: 6
DEFAULT_USER_ID=your-mongo-user-id   # skip user_id in API calls
```