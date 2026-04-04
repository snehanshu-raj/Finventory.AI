"""FastAPI application entry point."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.db import connect_db, close_db
from app.jobs.scheduler import start_scheduler, shutdown_scheduler
from app.utils.exceptions import AppException

# Route imports
from app.routes.users import router as users_router
from app.routes.receipts import router as receipts_router
from app.routes.inventory import router as inventory_router
from app.routes.analytics import router as analytics_router
from app.routes.meals import router as meals_router
from app.routes.notifications import router as notifications_router
from app.routes.integrations import router as integrations_router
from app.routes.email_expenses import router as email_expenses_router
from app.routes.expenses import router as expenses_router
from app.routes.admin import router as admin_router

logging.basicConfig(
    level=settings.log_level.upper(),
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application startup and shutdown."""
    logger.info("Starting up Expense Tracker API...")
    await connect_db()
    start_scheduler()
    yield
    shutdown_scheduler()
    await close_db()
    logger.info("Expense Tracker API shut down.")


app = FastAPI(
    title="AI Finance & Grocery Manager",
    description="AI-powered personal finance and grocery manager backend",
    version="1.0.0",
    lifespan=lifespan,
)


# ── Enable CORS ────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For hackathon, allow everything. Restrict in prod.
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Global Exception Handlers ──────────────────────────────────────────

@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    """Handle custom application exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "code": exc.error_code,
                "message": exc.message,
            },
        },
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    """Catch-all for unhandled exceptions."""
    logger.exception("Unhandled exception: %s", exc)
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "An unexpected error occurred.",
            },
        },
    )


# ── Register Routers ───────────────────────────────────────────────────

app.include_router(users_router, prefix="/api/v1/users", tags=["Users"])
app.include_router(receipts_router, prefix="/api/v1/receipts", tags=["Receipts"])
app.include_router(inventory_router, prefix="/api/v1/inventory", tags=["Inventory"])
app.include_router(analytics_router, prefix="/api/v1/analytics", tags=["Analytics"])
app.include_router(meals_router, prefix="/api/v1", tags=["Meals & Shopping"])
app.include_router(notifications_router, prefix="/api/v1/notifications", tags=["Notifications"])
app.include_router(integrations_router, prefix="/api/v1/integrations", tags=["Gmail Integration"])
app.include_router(email_expenses_router, prefix="/api/v1/email-expenses", tags=["Email Expenses"])
app.include_router(expenses_router, prefix="/api/v1/expenses", tags=["Unified Expenses"])
app.include_router(admin_router, prefix="/api/v1/admin", tags=["Admin (Testing)"])


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint."""
    return {"success": True, "data": {"status": "healthy"}, "message": "OK"}
