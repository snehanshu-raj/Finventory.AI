# 💰 Finventory - Smart Expense & Inventory Management

> **Intelligent expense tracking that works for you—automatically parsing emails, tracking prices, and predicting your financial future.**

[![Built with React](https://img.shields.io/badge/Frontend-React%2019-61DAFB?style=flat&logo=react)](https://react.dev)
[![Built with FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688?style=flat&logo=fastapi)](https://fastapi.tiangolo.com)
[![Built with MongoDB](https://img.shields.io/badge/Database-MongoDB-13AA52?style=flat&logo=mongodb)](https://www.mongodb.com)
[![Gmail API](https://img.shields.io/badge/Integration-Gmail%20API-EA4335?style=flat&logo=gmail)](https://developers.google.com/gmail/api)
[![LLM Powered](https://img.shields.io/badge/AI-Gemini%20Flash-4285F4?style=flat&logo=google)](https://ai.google.dev)

---

## 🚀 Features

### 📧 Intelligent Email Expense Extraction
- **Hybrid AI Engine**: Combines deterministic regex patterns + Gemini Flash LLM
- **Auto-categorization**: Airlines, restaurants, utilities, subscriptions—all recognized
- **High accuracy**: 85%+ confidence for known merchants, human review queue for low-confidence items
- **HTML-aware parsing**: Extracts amounts from complex formatted emails

### 💳 Unified Expense Dashboard
- **Multi-source tracking**: Manual receipts + Gmail expenses in one place
- **Real-time summaries**: Daily totals, monthly spend, category breakdown
- **Advanced filtering**: By date range, merchant, category, source
- **Cross-device sync**: Seamless experience on laptop and phone via ngrok tunneling

### 📊 Smart Analytics & Insights
- **Spending trends**: Track expenses by category and merchant over time
- **Price history**: Monitor inflation and product prices month-to-month
- **Household budget tracking**: Multi-person meal planning and expense sharing
- **Weekly summaries**: Automated email digests of your spending

### 🏠 Household Features
- **Shared inventory**: Track household staples and quantities
- **Daily decrement tracking**: Automatically monitor consumption patterns
- **Meal planning**: Coordinate household meals and dietary preferences
- **Price aggregation**: Compare prices across merchants for smarter shopping

### 🔐 Secure & Privacy-First
- **Single-user mode**: Your data, your database
- **OAuth authenticated**: Gmail integration requires explicit permission
- **Minimal data storage**: Only essential fields, automatic cleanup
- **No third-party tracking**: Self-hosted architecture

---

## 🛠️ Technology Stack

### Frontend (Glassmorphic Dark Theme)
```
React 19 + TypeScript
├─ Vite 5.4.0 (Lightning-fast builds)
├─ Tailwind CSS 3.4.0 (Modern styling)
├─ Zustand (Lightweight state management)
└─ Axios (Smart API client with ngrok support)
```

### Backend (Async-first Architecture)
```
Python 3.12 + FastAPI
├─ Uvicorn ASGI server
├─ Motor (Async MongoDB driver)
├─ APScheduler (Background jobs)
└─ Google Gemini Flash LLM
```

### Database & Integrations
```
MongoDB (Local or cloud)
├─ Collections: users, receipts, email_expenses, prices, meals, notifications
├─ Async queries via Motor
└─ Aggregation pipelines for analytics

Gmail API
├─ OAuth 2.0 authentication
├─ 7-day email lookback (customizable)
└─ Hybrid parsing: regex + LLM

Google Gemini Flash 2.5
├─ Expense extraction & categorization
├─ Rate limiting with fallback to regex
└─ Confidence scoring for human review
```

---

## 📈 How It Works

### Expense Tracking Pipeline
```
Gmail Email
    ↓
[OAuth Fetch] → 7-day lookback query
    ↓
[HTML Parser] → Convert to plaintext, unescape entities
    ↓
[Deterministic Extract] → Regex patterns for known merchants
    ↓
[Confidence Check] → 85%+ → Store | <85% → Gemini LLM
    ↓
[LLM Fallback] → Advanced parsing with context
    ↓
[MongoDB Store] → Deduplicated, categorized, queryable
    ↓
[Analytics] → Updated dashboard in real-time
```

### Key Improvements (Latest Version)
- **HTML Email Support**: Handles airlines, hotels, utilities sending HTML-formatted receipts
- **Multi-format Dates**: Parses "March 31, 2026", "3/30/2026", "04/17/26" consistently
- **Merchant Recognition**: 25+ patterns for airlines, hotels, food delivery, subscriptions, banks
- **Entity Deduplication**: Prevents duplicate expenses from re-syncs
- **Cross-Device Sync**: No localStorage caching—database is the single source of truth

---

## 🎯 Getting Started

### Prerequisites
- Python 3.12+
- Node.js 18+
- MongoDB (local or Atlas)
- Google OAuth credentials (optional for Gmail sync)

### Backend Setup
```bash
cd finventory

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your MongoDB URL, Gmail credentials, LLM API key

# Run backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Setup
```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev

# Production build
npm run build
```

### Access the Application
- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs (Swagger UI)

### Cross-Device Testing with ngrok
```bash
# Terminal 1: Backend
cd finventory && uvicorn app.main:app --reload --port 8000

# Terminal 2: Frontend
cd frontend && npm run dev

# Terminal 3: ngrok tunnel
ngrok http 5173

# Visit: https://your-ngrok-url.ngrok.io on phone
```

---

## 📦 Project Structure

```
finventory/
├── app/                          # FastAPI backend
│   ├── routes/                   # API endpoints
│   │   ├── expenses.py           # Unified expense endpoints
│   │   ├── receipts.py           # Receipt management
│   │   ├── integrations.py       # Gmail API integration
│   │   ├── analytics.py          # Spending insights
│   │   └── users.py              # User profiles & onboarding
│   ├── services/                 # Business logic
│   │   ├── gmail_sync_service.py # Email fetching & parsing
│   │   ├── gmail_expense_parser.py # Hybrid extraction engine
│   │   ├── unified_expense_service.py # Receipt + email merge
│   │   └── analytics_service.py  # Aggregations & summaries
│   ├── repositories/             # Data access layer
│   │   ├── gmail_repository.py   # Email expenses CRUD
│   │   ├── receipt_repository.py # Receipt queries
│   │   └── price_repository.py   # Price history ops
│   ├── models/                   # MongoDB schemas
│   ├── schemas/                  # Pydantic request/response
│   ├── jobs/                     # Scheduled tasks
│   │   ├── daily_decrement.py    # Inventory tracking
│   │   ├── gmail_poll.py         # Auto-sync emails
│   │   ├── weekly_summary.py     # Email digests
│   │   └── price_aggregation.py  # Price tracking
│   └── utils/                    # Helpers, exceptions, storage
│
├── frontend/                     # React + TypeScript
│   ├── src/
│   │   ├── pages/               # Route components
│   │   │   ├── Dashboard.tsx    # Main expense view
│   │   │   ├── Expenses.tsx     # Detailed list & filters
│   │   │   ├── Settings.tsx     # Gmail sync controls
│   │   │   └── Onboarding.tsx   # User setup flow
│   │   ├── components/          # Reusable UI components
│   │   ├── store/               # Zustand state (in-memory)
│   │   ├── api/                 # Axios HTTP clients
│   │   └── App.tsx              # Main app router
│   └── vite.config.ts           # ngrok domain allowlist
│
├── requirements.txt             # Python dependencies
├── docker-compose.yml           # Local MongoDB + backend
├── Dockerfile                   # Container configuration
├── .env                         # Environment config
├── TECH_STACK.md                # Technology details
└── README.md                    # You are here
```

---

## 🔌 API Endpoints

### Expenses
```
GET  /api/v1/expenses              # List expenses
GET  /api/v1/expenses/summary       # Monthly totals & breakdown
GET  /api/v1/expenses/{id}          # Single expense detail
POST /api/v1/expenses               # Create manual expense
```

### Gmail Integration
```
POST /api/v1/integrations/gmail/auth        # Start OAuth flow
GET  /api/v1/integrations/gmail/callback    # OAuth redirect
POST /api/v1/integrations/gmail/fetch-and-preview  # Sync emails (7-day lookback)
GET  /api/v1/integrations/gmail/sync-history     # Past syncs
DELETE /api/v1/integrations/gmail/expenses       # Reset email expenses
```

### Analytics
```
GET  /api/v1/analytics/summary              # Spending overview
GET  /api/v1/analytics/trends/{item}        # Price trends
GET  /api/v1/analytics/by-category          # Categorical spend
```

### Users & Onboarding
```
POST /api/v1/users/onboarding               # Initial setup
GET  /api/v1/users/onboarding/data          # Check onboarding status
GET  /api/v1/users/profile                  # User profile
```

---

## 💡 Key Implementation Highlights

### Hybrid AI Extraction Engine
```python
# 1. Fast deterministic regex (confidence 0.85)
-  Airlines: Spirit, United, Delta, Southwest regex patterns
- Hotels: Airbnb, Booking.com, VRBO matching
- Utilities: Landlord, property manager, power company patterns
- Banks: Bank of America, Chase, Wells Fargo detection

# 2. LLM fallback for complex cases
- Gemini Flash processes low-confidence emails (<85%)
- Returns structured JSON with merchant, amount, category
- Human review queue for <70% confidence items
- Rate limit handling: Fallback to regex if API limit hit
```

### Cross-Device Sync Architecture
```
Frontend (React)
    ↓ [Axios client detects environment]
    ├─ localhost        → http://localhost:8000
    └─ ngrok domain     → API at relative /api/v1
        ↓
    Backend (FastAPI)
        ↓ [Single user_id from .env]
        ↓
    MongoDB (Single database)
        ↓ [API-first design]
    ✓ Onboarding state syncs instantly across devices
    ✓ No localStorage caching (DB is source of truth)
    ✓ Phone + Laptop work seamlessly
```

### HTML Email Parsing
```python
# Processing Flow:
1. Check if email body is HTML (regex: <, <!DOCTYPE, &nbsp;, etc.)
2. Convert HTML → plaintext (BeautifulSoup)
3. Unescape entities (&nbsp; → space, &amp; → &, etc.)
4. Normalize whitespace (multiple spaces → single space)
5. Apply regex patterns to extract amounts
6. Result: $3.99 extracted from "<p>Total: $3.99</p>"
```

### Performance Optimizations
- **Motor async driver**: Non-blocking MongoDB queries
- **Hot module reloading**: Vite frontend development speed
- **Email deduplication**: Gmail message ID prevents duplicates
- **Aggregation pipelines**: Fast category/merchant analytics
- **Message filtering**: 7-day lookback reduces API calls (~50 emails/week)

---

## 🎨 UI/UX Design

### Glassmorphic Dark Theme
- **Modern aesthetic**: Frosted glass effect with transparency
- **Dark mode**: Easy on the eyes during long sessions
- **Responsive**: Mobile, tablet, and desktop optimized
- **Fast interactions**: Optimistic UI updates, smooth transitions

### Key Pages
- **Dashboard**: Quick expense summary, recent transactions, spending by category
- **Expenses**: Advanced filtering, merchant search, date range picker, source indicator
- **Settings**: Gmail sync controls (7-day lookback), notification preferences
- **Onboarding**: Guided setup for first-time users (one-time flow per device)

---

## 🚀 Deployment

### Docker Compose (Development)
```bash
docker-compose up -d
# MongoDB on port 27017
# Backend on port 8000
# Frontend on port 5173
```

### Production Ready
- Environment-based configuration (.env)
- Rate limiting middleware for APIs
- CORS configured for secure origins
- MongoDB indexes for query performance
- Error handling with structured logging

---

## 📊 Database Schema Example

### email_expenses Collection
```json
{
  "_id": "ObjectId",
  "userId": "69d053d1bc3220a8660218b3",
  "gmailMessageId": "abc123xyz",
  "merchant": "Spirit Airlines",
  "normalizedMerchant": "spirit airlines",
  "amount": 258.75,
  "currency": "USD",
  "category": "transport",
  "transactionAt": "2026-04-05T00:00:00Z",
  "expenseType": "ride_share",
  "confidence": 0.85,
  "parsingStatus": "parsed",
  "createdAt": "2026-04-05T12:30:00Z"
}
```

---

## 🔄 Update History

### Latest (April 5, 2026) - "Smart Parsing Update"
- ✅ Fixed HTML email parsing (airlines, hotels, utilities)
- ✅ Added merchant pattern recognition for 25+ vendors
- ✅ Improved amount extraction accuracy (HTML entities handling)
- ✅ Enhanced confidence scoring system (0.85 for known merchants)
- ✅ Cross-device sync validation & database-first architecture

### Previous Milestones
- ✅ Gmail 7-day lookback parameter fix (April 4)
- ✅ Date normalization with python-dateutil (April 3)
- ✅ Database-driven onboarding (no localStorage) (April 2)
- ✅ ngrok cross-device support (March 31)
- ✅ Glassmorphic UI redesign with dark theme (March 30)

---

## 🎓 Learning & Architecture Decisions

### Why These Choices?

| Component | Choice | Reason |
|-----------|--------|--------|
| **Frontend** | React 19 | Modern hooks, fast re-renders, large ecosystem |
| **Backend** | FastAPI | Async-first, automatic API docs, type safety |
| **Database** | MongoDB | Flexible schema for expense variations, Motor async driver |
| **LLM** | Gemini Flash | Fast inference, cost-effective, reliable extraction |
| **State** | Zustand | Lightweight, no boilerplate, easy to debug |
| **Styling** | Tailwind CSS | Utility-first, responsive, modern design |

### Architectural Patterns
- **Service Layer**: Business logic separated from routes
- **Repository Pattern**: Data access abstraction
- **Dependency Injection**: Clean, testable code
- **Async Throughout**: No blocking operations
- **Single User Mode**: Simplified auth, perfect for households

---

## 🐛 Known Limitations & Future Work

### Current Constraints
- Single-user mode (ideal for households, not multi-tenant SaaS)
- Local MongoDB (no cloud backup auto-configured)
- Rate limiting on Gemini API (fallback to regex works fine)
- Mobile web only (no native iOS/Android apps)

### Roadmap
- [ ] Export to CSV/PDF reports with charts
- [ ] Receipt image OCR (AWS Textract integration)
- [ ] Recurring expense prediction (ML models)
- [ ] Bank account direct integration (Plaid)
- [ ] Mobile native apps (React Native)
- [ ] White-label customization for SaaS
- [ ] Advanced tax reporting and categories
- [ ] Multi-user household teams with roles
- [ ] Budget alerts and spending limits
- [ ] Investment tracking and portfolio integration

---

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

## 👨‍💻 Author

**Built by SRJ** - Full-stack developer passionate about financial automation and AI-powered applications.

---

## 🙌 Acknowledgments

- **Gmail API** team for excellent documentation
- **Google Gemini Flash** for reliable LLM extraction
- **FastAPI** framework for making backend development joyful
- **React** and **Tailwind CSS** communities for amazing tools
- **MongoDB** for flexible document storage

---

## 📞 Support & Feedback

Have questions or feedback? Open an issue on GitHub or reach out directly.

Need help? Check out the [TECH_STACK.md](TECH_STACK.md) for detailed technology information.

**Happy budgeting! 💰**

---

<div align="center">

### ⭐ Star this repo if you find it helpful!

Built with ❤️ for financial freedom

</div>
