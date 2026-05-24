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


def _oauth_config(
    *,
    client_id: str | None = None,
    client_secret: str | None = None,
    redirect_uri: str | None = None,
) -> tuple[str, str, str]:
    cid = client_id or settings.GOOGLE_CLIENT_ID
    secret = client_secret or settings.GOOGLE_CLIENT_SECRET
    redirect = redirect_uri or settings.GOOGLE_REDIRECT_URI
    if not cid or not secret or not redirect:
        raise GoogleBusinessError("Google OAuth is not configured")
    return cid, secret, redirect


def build_authorization_url(
    *,
    state: str,
    client_id: str | None = None,
    redirect_uri: str | None = None,
    scopes: tuple[str, ...] | None = None,
) -> str:
    cid, _, redirect = _oauth_config(client_id=client_id, redirect_uri=redirect_uri)
    params = {
        "client_id": cid,
        "redirect_uri": redirect,
        "response_type": "code",
        "scope": " ".join(scopes or GOOGLE_SCOPES),
        "access_type": "offline",
        "prompt": "consent",
        "state": state,
    }
    return f"{GOOGLE_AUTH_URL}?{urlencode(params)}"


async def exchange_code_for_tokens(
    code: str,
    *,
    client_id: str | None = None,
    client_secret: str | None = None,
    redirect_uri: str | None = None,
) -> dict[str, Any]:
    cid, secret, redirect = _oauth_config(
        client_id=client_id, client_secret=client_secret, redirect_uri=redirect_uri
    )
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(
            GOOGLE_TOKEN_URL,
            data={
                "code": code,
                "client_id": cid,
                "client_secret": secret,
                "redirect_uri": redirect,
                "grant_type": "authorization_code",
            },
        )
    if resp.status_code >= 400:
        logger.error("Google token exchange failed: %s", resp.text[:500])
        raise GoogleBusinessError("Google token exchange failed")
    return resp.json()


async def refresh_access_token(
    refresh_token: str,
    *,
    client_id: str | None = None,
    client_secret: str | None = None,
) -> dict[str, Any]:
    cid, secret, _ = _oauth_config(client_id=client_id, client_secret=client_secret)
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(
            GOOGLE_TOKEN_URL,
            data={
                "client_id": cid,
                "client_secret": secret,
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

    async def list_local_posts(self, location_name: str) -> list[dict[str, Any]]:
        data = await self._get(f"{location_name}/localPosts", params={"pageSize": 50})
        return list(data.get("localPosts") or [])

    async def list_media(self, location_name: str) -> list[dict[str, Any]]:
        account_id, _, location_id = location_name.partition("/locations/")
        account_part = account_id.replace("accounts/", "")
        loc_id = location_id.split("/")[0] if location_id else location_name.split("/")[-1]
        data = await self._get(
            f"accounts/{account_part}/locations/{loc_id}/media",
            params={"pageSize": 50},
        )
        return list(data.get("mediaItems") or [])

    async def fetch_location_insights(self, location_name: str) -> dict[str, Any]:
        """Best-effort analytics snapshot for a location."""
        try:
            return await self._get(f"{location_name}:reportInsights", params={"dailyMetrics": "ALL"})
        except GoogleBusinessError:
            return {"location": location_name, "metrics": []}
