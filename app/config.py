"""Application configuration loaded from environment variables."""

from typing import Literal

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings backed by .env file."""

    # MongoDB
    mongodb_url: str = "mongodb://localhost:27017"
    mongodb_db_name: str = "expense_tracker"

    # LLM Provider
    llm_provider: Literal["gemini", "claude", "mock"] = "mock"
    gemini_api_key: str = ""
    claude_api_key: str = ""

    # File Storage
    upload_dir: str = "./uploads"

    # Business Rules
    reminder_cooldown_days: int = 3
    min_price_samples: int = 3

    # Google OAuth / Gmail
    google_client_id: str = ""
    google_client_secret: str = ""
    google_redirect_uri: str = "http://localhost:8000/api/v1/integrations/gmail/callback"
    google_refresh_token: str = ""
    gmail_sync_interval_hours: int = 6

    # Single-user mode
    default_user_id: str = ""

    # App
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    log_level: str = "info"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
