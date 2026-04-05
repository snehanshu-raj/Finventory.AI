# Tech Stack - Finventory

## Frontend
- **Framework**: React 19 with TypeScript
- **Build Tool**: Vite 5.4.0
- **Styling**: Tailwind CSS 3.4.0
- **State Management**: Zustand (in-memory, no persistence)
- **UI Design Pattern**: Glassmorphism with dark theme
- **HTTP Client**: Axios (environment-aware for localhost/ngrok)
- **Node.js**: Version 18+ (compatible)

## Backend
- **Language**: Python 3.12
- **Framework**: FastAPI
- **ASGI Server**: Uvicorn (with `--reload` for development)
- **Async Support**: Python asyncio

## Database
- **Primary DB**: MongoDB
- **Driver**: Motor (async driver for Python)
- **Connection**: Local MongoDB instance (mongodb://localhost:27017)
- **Database Name**: expense_tracker

## APIs & Integrations
- **Gmail API**: Email fetch and expense extraction
  - OAuth 2.0 authentication
  - Refresh token-based access
- **Google OAuth**: User authentication and Gmail account linking
- **LLM Provider**: Google Gemini Flash (2.5-flash model)
  - Hybrid extraction: deterministic regex + LLM fallback
  - Rate limit: 429 handling (cooldown retry strategy)

## Date & Time
- **Date Parsing**: python-dateutil 2.8.2
  - Handles multiple date formats (ISO, US, text)
  - Converts to datetime for MongoDB storage

## Development & Testing
- **Tunneling**: ngrok (cross-device testing via phone)
- **Containerization**: Docker & docker-compose.yml
- **API Documentation**: FastAPI auto-generated (interactive docs)
- **Environment Config**: .env file with Pydantic Settings

## Architecture Patterns
- **Single-User Mode**: DEFAULT_USER_ID from .env (hardcoded throughout)
- **API-First Design**: Database as source of truth
- **Async/Await**: All database operations non-blocking
- **Repository Pattern**: Separation of data access from business logic
- **Service Layer**: Business logic encapsulation
- **Dependency Injection**: FastAPI's depends() for user context

## Key Features
- **Expense Tracking**: Manual receipts + Gmail-based automatic extraction
- **Daily Scheduler**: Background jobs for email sync, price tracking, summaries
- **Gmail Sync**: 7-day lookback for expense emails (2026-04-04 baseline)
- **Meal Planning**: Household meal coordination
- **Price Tracking**: Historical price observations for inflation analysis
- **Notification System**: In-app alerts for expenses
- **Admin Routes**: User management and system diagnostics

## Performance Optimizations
- Motor async driver for non-blocking MongoDB queries
- Vite's fast hot module reloading
- ngrok for efficient cross-device testing (no server reconfiguration needed)
- Message deduplication in Gmail sync to prevent duplicate expenses

