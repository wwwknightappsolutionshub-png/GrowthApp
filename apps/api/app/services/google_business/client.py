"""HTTP client for Google Business Profile (My Business) API v4."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any
from urllib.parse import urlencode

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
MYBUSINESS_API_BASE = "https://mybusiness.googleapis.com/v4"
GOOGLE_SCOPES = ("https://www.googleapis.com/auth/business.manage",)


class GoogleBusinessError(Exception):
    """Raised when Google API returns an error."""


def build_authorization_url(*, state: str) -> str:
    params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": " ".join(GOOGLE_SCOPES),
        "access_type": "offline",
        "prompt": "consent",
        "state": state,
    }
    return f"{GOOGLE_AUTH_URL}?{urlencode(params)}"


async def exchange_code_for_tokens(code: str) -> dict[str, Any]:
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(
            GOOGLE_TOKEN_URL,
            data={
                "code": code,
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "redirect_uri": settings.GOOGLE_REDIRECT_URI,
                "grant_type": "authorization_code",
            },
        )
    if resp.status_code >= 400:
        logger.error("Google token exchange failed: %s", resp.text[:500])
        raise GoogleBusinessError("Google token exchange failed")
    return resp.json()


async def refresh_access_token(refresh_token: str) -> dict[str, Any]:
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(
            GOOGLE_TOKEN_URL,
            data={
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "refresh_token": refresh_token,
                "grant_type": "refresh_token",
            },
        )
    if resp.status_code >= 400:
        raise GoogleBusinessError("Google token refresh failed")
    return resp.json()


def token_expires_at(expires_in: int | None) -> datetime | None:
    if not expires_in:
        return None
    return datetime.now(timezone.utc) + timedelta(seconds=int(expires_in))


class GoogleBusinessClient:
    def __init__(self, access_token: str) -> None:
        self.access_token = access_token

    async def _get(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        url = f"{MYBUSINESS_API_BASE}/{path.lstrip('/')}"
        async with httpx.AsyncClient(timeout=45.0) as client:
            resp = await client.get(
                url,
                params=params,
                headers={"Authorization": f"Bearer {self.access_token}"},
            )
        if resp.status_code >= 400:
            logger.warning("Google API GET %s -> %s %s", path, resp.status_code, resp.text[:300])
            raise GoogleBusinessError(f"Google API error {resp.status_code}")
        return resp.json()

    async def _put(self, path: str, body: dict[str, Any]) -> dict[str, Any]:
        url = f"{MYBUSINESS_API_BASE}/{path.lstrip('/')}"
        async with httpx.AsyncClient(timeout=45.0) as client:
            resp = await client.put(
                url,
                json=body,
                headers={"Authorization": f"Bearer {self.access_token}"},
            )
        if resp.status_code >= 400:
            raise GoogleBusinessError(f"Google API error {resp.status_code}")
        return resp.json() if resp.content else {}

    async def list_accounts(self) -> list[dict[str, Any]]:
        data = await self._get("accounts")
        return list(data.get("accounts") or [])

    async def list_locations(self, account_name: str) -> list[dict[str, Any]]:
        account_id = account_name.split("/")[-1]
        data = await self._get(f"accounts/{account_id}/locations", params={"pageSize": 100})
        return list(data.get("locations") or [])

    async def list_reviews(self, location_name: str) -> list[dict[str, Any]]:
        # location_name: accounts/{aid}/locations/{lid}
        data = await self._get(f"{location_name}/reviews", params={"pageSize": 50})
        return list(data.get("reviews") or [])

    async def reply_to_review(self, review_name: str, comment: str) -> dict[str, Any]:
        # review_name: accounts/.../locations/.../reviews/...
        return await self._put(f"{review_name}/reply", {"comment": comment})
