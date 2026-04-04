"""Gmail OAuth service – token exchange, refresh, and management."""

import logging
from datetime import datetime, timedelta
from typing import Optional

import httpx

from app.config import settings
from app.repositories.gmail_repository import linked_account_repo
from app.utils.exceptions import AppException, ValidationException

logger = logging.getLogger(__name__)

GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"
GOOGLE_REVOKE_URL = "https://oauth2.googleapis.com/revoke"


class GmailAuthService:
    """Handle Google OAuth token refresh and auto-provisioning."""

    async def _auto_provision(self, user_id: str) -> Optional[dict]:
        """Auto-create linked account from .env GOOGLE_REFRESH_TOKEN if available."""
        refresh_token = settings.google_refresh_token
        if not refresh_token:
            return None

        logger.info("Auto-provisioning Gmail linked account for user %s from .env", user_id)

        # Use refresh token to get a fresh access token
        async with httpx.AsyncClient() as client:
            resp = await client.post(GOOGLE_TOKEN_URL, data={
                "client_id": settings.google_client_id,
                "client_secret": settings.google_client_secret,
                "refresh_token": refresh_token,
                "grant_type": "refresh_token",
            })

        if resp.status_code != 200:
            logger.error("Auto-provision token refresh failed: %s", resp.text)
            return None

        token_data = resp.json()
        access_token = token_data["access_token"]
        expires_in = token_data.get("expires_in", 3600)
        token_expiry = datetime.utcnow() + timedelta(seconds=expires_in)

        # Fetch user email
        async with httpx.AsyncClient() as client:
            info_resp = await client.get(
                GOOGLE_USERINFO_URL,
                headers={"Authorization": f"Bearer {access_token}"},
            )
        email = info_resp.json().get("email", "") if info_resp.status_code == 200 else ""

        # Store linked account
        account = await linked_account_repo.upsert(user_id, {
            "userId": user_id,
            "provider": "gmail",
            "email": email,
            "scopes": ["https://www.googleapis.com/auth/gmail.readonly"],
            "accessToken": access_token,
            "refreshToken": refresh_token,
            "tokenExpiry": token_expiry,
            "syncEnabled": True,
            "createdAt": datetime.utcnow(),
        })

        logger.info("Gmail auto-provisioned for user %s (%s)", user_id, email)
        return account

    async def get_status(self, user_id: str) -> dict:
        """Return Gmail connection status."""
        account = await linked_account_repo.find_by_user(user_id)
        if not account:
            # Try auto-provision
            account = await self._auto_provision(user_id)
        if not account:
            return {"connected": False, "email": None, "sync_enabled": False, "last_synced_at": None}
        return {
            "connected": True,
            "email": account.get("email", ""),
            "sync_enabled": account.get("syncEnabled", False),
            "last_synced_at": account.get("lastSyncedAt"),
        }

    async def disconnect(self, user_id: str) -> dict:
        """Revoke tokens and remove linked account."""
        account = await linked_account_repo.find_by_user(user_id)
        if account and account.get("accessToken"):
            try:
                async with httpx.AsyncClient() as client:
                    await client.post(GOOGLE_REVOKE_URL, params={"token": account["accessToken"]})
            except Exception as e:
                logger.warning("Token revocation failed: %s", e)

        await linked_account_repo.delete(user_id)
        logger.info("Gmail disconnected for user %s", user_id)
        return {"connected": False, "email": None, "sync_enabled": False}

    async def get_valid_token(self, user_id: str) -> str:
        """Return a valid access token, refreshing if expired. Auto-provisions from .env if needed."""
        account = await linked_account_repo.find_by_user(user_id)

        # Auto-provision if no linked account exists
        if not account:
            account = await self._auto_provision(user_id)
            if not account:
                raise ValidationException(
                    "Gmail not configured. Set GOOGLE_REFRESH_TOKEN in .env "
                    "(run: python scripts/get_refresh_token.py)"
                )

        token_expiry = account.get("tokenExpiry")
        if token_expiry and token_expiry > datetime.utcnow() + timedelta(minutes=2):
            return account["accessToken"]

        # Refresh
        refresh_token = account.get("refreshToken") or settings.google_refresh_token
        if not refresh_token:
            raise ValidationException("No refresh token available. Set GOOGLE_REFRESH_TOKEN in .env")

        async with httpx.AsyncClient() as client:
            resp = await client.post(GOOGLE_TOKEN_URL, data={
                "client_id": settings.google_client_id,
                "client_secret": settings.google_client_secret,
                "refresh_token": refresh_token,
                "grant_type": "refresh_token",
            })

        if resp.status_code != 200:
            logger.error("Token refresh failed: %s", resp.text)
            raise AppException(
                status_code=401,
                error_code="OAUTH_REFRESH_FAILED",
                message="Failed to refresh Gmail token. Check GOOGLE_REFRESH_TOKEN in .env",
            )

        token_data = resp.json()
        new_token = token_data["access_token"]
        expires_in = token_data.get("expires_in", 3600)

        await linked_account_repo.update(user_id, {
            "accessToken": new_token,
            "tokenExpiry": datetime.utcnow() + timedelta(seconds=expires_in),
        })

        logger.info("Gmail token refreshed for user %s", user_id)
        return new_token


gmail_auth_service = GmailAuthService()
