"""Tenant-owned Google OAuth credentials and sync."""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import BadRequestException, NotFoundException
from app.modules.integrations import service as platform_service
from app.modules.integrations.models import (
    TenantGoogleConnection,
    TenantGoogleCredentials,
    TenantGoogleSyncLog,
)
from app.modules.integrations.token_crypto import decrypt_secret, encrypt_secret
from app.services.google_business.client import (
    GOOGLE_SCOPES,
    GoogleBusinessClient,
    GoogleBusinessError,
    build_authorization_url,
    exchange_code_for_tokens,
    refresh_access_token,
    token_expires_at,
)

logger = logging.getLogger(__name__)


def _public_api_base() -> str:
    base = (settings.PUBLIC_API_BASE_URL or settings.FRONTEND_URL).rstrip("/")
    return base


def tenant_redirect_uri() -> str:
    return f"{_public_api_base()}/api/v1/integrations/google/oauth-callback"


async def get_credentials(db: AsyncSession, tenant_id: uuid.UUID) -> TenantGoogleCredentials | None:
    return (
        await db.execute(
            select(TenantGoogleCredentials).where(TenantGoogleCredentials.tenant_id == tenant_id)
        )
    ).scalar_one_or_none()


async def register_credentials(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    *,
    google_client_id: str,
    google_client_secret: str,
) -> dict[str, Any]:
    if not settings.INTEGRATIONS_TOKEN_ENCRYPTION_KEY:
        raise BadRequestException("Integration encryption is not configured on this server")

    client_id = google_client_id.strip()
    client_secret = google_client_secret.strip()
    if len(client_id) < 10 or len(client_secret) < 10:
        raise BadRequestException("Invalid Google Client ID or Secret")

    redirect = tenant_redirect_uri()
    row = await get_credentials(db, tenant_id)
    if row:
        row.google_client_id = client_id
        row.google_client_secret_encrypted = encrypt_secret(client_secret)
        row.redirect_uri = redirect
        row.status = "pending"
    else:
        row = TenantGoogleCredentials(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            google_client_id=client_id,
            google_client_secret_encrypted=encrypt_secret(client_secret),
            redirect_uri=redirect,
            scopes=" ".join(GOOGLE_SCOPES),
            status="pending",
        )
        db.add(row)
    await db.commit()
    await db.refresh(row)
    return credentials_status(row)


def credentials_status(row: TenantGoogleCredentials | None) -> dict[str, Any]:
    if not row:
        return {
            "registered": False,
            "status": None,
            "redirect_uri": tenant_redirect_uri(),
            "google_client_id": None,
            "connected_at": None,
            "expires_at": None,
        }
    return {
        "registered": True,
        "status": row.status,
        "redirect_uri": row.redirect_uri,
        "google_client_id": row.google_client_id,
        "connected_at": row.connected_at.isoformat() if row.connected_at else None,
        "expires_at": row.expires_at.isoformat() if row.expires_at else None,
    }


async def auth_url(db: AsyncSession, tenant_id: uuid.UUID, user_id: uuid.UUID) -> str:
    row = await get_credentials(db, tenant_id)
    if not row:
        raise BadRequestException("Register Google credentials first")
    state = platform_service.create_oauth_state(tenant_id=tenant_id, user_id=user_id)
    return build_authorization_url(
        state=state,
        client_id=row.google_client_id,
        redirect_uri=row.redirect_uri,
    )


async def _ensure_fresh_token(db: AsyncSession, creds: TenantGoogleCredentials) -> str:
    if creds.access_token_encrypted and creds.expires_at and creds.expires_at > datetime.now(timezone.utc):
        return decrypt_secret(creds.access_token_encrypted)

    if not creds.refresh_token_encrypted:
        creds.status = "expired"
        db.add(creds)
        await db.commit()
        raise BadRequestException("Google refresh token missing — reconnect OAuth")

    secret = decrypt_secret(creds.google_client_secret_encrypted)
    refreshed = await refresh_access_token(
        decrypt_secret(creds.refresh_token_encrypted),
        client_id=creds.google_client_id,
        client_secret=secret,
    )
    access = refreshed.get("access_token")
    if not access:
        creds.status = "expired"
        db.add(creds)
        await db.commit()
        raise BadRequestException("Google token refresh failed")

    creds.access_token_encrypted = encrypt_secret(access)
    if refreshed.get("refresh_token"):
        creds.refresh_token_encrypted = encrypt_secret(refreshed["refresh_token"])
    creds.expires_at = token_expires_at(refreshed.get("expires_in"))
    creds.status = "connected"
    db.add(creds)
    await db.commit()
    return access


async def complete_oauth_callback(
    db: AsyncSession,
    *,
    code: str,
    tenant_id: uuid.UUID,
) -> TenantGoogleCredentials:
    creds = await get_credentials(db, tenant_id)
    if not creds:
        raise BadRequestException("Google credentials not registered for this tenant")

    secret = decrypt_secret(creds.google_client_secret_encrypted)
    token_payload = await exchange_code_for_tokens(
        code,
        client_id=creds.google_client_id,
        client_secret=secret,
        redirect_uri=creds.redirect_uri,
    )
    access = token_payload.get("access_token")
    if not access:
        raise BadRequestException("Google authorization failed")

    creds.access_token_encrypted = encrypt_secret(access)
    refresh = token_payload.get("refresh_token")
    if refresh:
        creds.refresh_token_encrypted = encrypt_secret(refresh)
    creds.expires_at = token_expires_at(token_payload.get("expires_in"))
    creds.scopes = token_payload.get("scope") or " ".join(GOOGLE_SCOPES)
    creds.status = "connected"
    db.add(creds)
    await db.commit()

    client = GoogleBusinessClient(access)
    accounts = await client.list_accounts()
    if not accounts:
        raise BadRequestException("No Google Business accounts found")

    account = accounts[0]
    account_name = account.get("name") or ""
    locations = await client.list_locations(account_name)
    if not locations:
        raise BadRequestException("No business locations found")

    await platform_service._save_tokens(  # noqa: SLF001
        db,
        tenant_id,
        token_payload=token_payload,
        account_name=account_name,
        location=locations[0],
        all_locations=locations,
    )
    await db.refresh(creds)
    return creds


async def refresh_token(db: AsyncSession, tenant_id: uuid.UUID) -> dict[str, Any]:
    creds = await get_credentials(db, tenant_id)
    if not creds:
        raise NotFoundException("Google credentials")
    await _ensure_fresh_token(db, creds)
    return credentials_status(creds)


async def _client_for_tenant(db: AsyncSession, tenant_id: uuid.UUID) -> GoogleBusinessClient:
    creds = await get_credentials(db, tenant_id)
    if creds and creds.status == "connected":
        access = await _ensure_fresh_token(db, creds)
        return GoogleBusinessClient(access)

    conn = await platform_service.get_connection(db, tenant_id)
    if conn:
        return await platform_service._client_for_connection(db, conn)  # noqa: SLF001

    raise BadRequestException("Google Business is not connected")


async def _connection_for_tenant(db: AsyncSession, tenant_id: uuid.UUID) -> TenantGoogleConnection:
    conn = await platform_service.get_connection(db, tenant_id)
    if not conn or not conn.google_location_name:
        raise BadRequestException("Google Business location is not selected")
    return conn


async def _log_sync(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    data_type: str,
    payload: dict[str, Any],
    *,
    status: str = "success",
) -> None:
    db.add(
        TenantGoogleSyncLog(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            data_type=data_type,
            payload=payload,
            status=status,
        )
    )


async def sync_reviews(db: AsyncSession, tenant_id: uuid.UUID) -> dict[str, Any]:
    result = await platform_service.sync_google_reviews(db, tenant_id)
    await _log_sync(db, tenant_id, "reviews", result)
    await db.commit()
    return result


async def sync_messages(db: AsyncSession, tenant_id: uuid.UUID) -> dict[str, Any]:
    from app.modules.integrations.mappers.inbound_mapper import ingest_google_message

    conn = await _connection_for_tenant(db, tenant_id)
    client = await _client_for_tenant(db, tenant_id)
    # GBP messaging is limited; we log sync attempt and ingest any review replies as messages.
    reviews = await client.list_reviews(conn.google_location_name)
    ingested = 0
    for review in reviews:
        reply = (review.get("reviewReply") or {}).get("comment")
        if reply:
            reviewer = (review.get("reviewer") or {}).get("displayName") or "Google reviewer"
            await ingest_google_message(
                db,
                tenant_id=tenant_id,
                sender_name=reviewer,
                body=reply,
                external_id=review.get("name"),
            )
            ingested += 1
    payload = {"ingested": ingested, "review_count": len(reviews)}
    await _log_sync(db, tenant_id, "messages", payload)
    await db.commit()
    return payload


async def sync_posts(db: AsyncSession, tenant_id: uuid.UUID) -> dict[str, Any]:
    conn = await _connection_for_tenant(db, tenant_id)
    client = await _client_for_tenant(db, tenant_id)
    try:
        posts = await client.list_local_posts(conn.google_location_name)
    except GoogleBusinessError as exc:
        payload = {"error": str(exc), "total": 0}
        await _log_sync(db, tenant_id, "posts", payload, status="failed")
        await db.commit()
        raise BadRequestException("Could not fetch Google posts") from exc
    payload = {"total": len(posts), "posts": posts[:20]}
    await _log_sync(db, tenant_id, "posts", payload)
    await db.commit()
    return {"total": len(posts)}


async def sync_photos(db: AsyncSession, tenant_id: uuid.UUID) -> dict[str, Any]:
    conn = await _connection_for_tenant(db, tenant_id)
    client = await _client_for_tenant(db, tenant_id)
    try:
        media = await client.list_media(conn.google_location_name)
    except GoogleBusinessError as exc:
        payload = {"error": str(exc), "total": 0}
        await _log_sync(db, tenant_id, "photos", payload, status="failed")
        await db.commit()
        raise BadRequestException("Could not fetch Google photos") from exc
    payload = {"total": len(media)}
    await _log_sync(db, tenant_id, "photos", payload)
    await db.commit()
    return {"total": len(media)}


async def sync_analytics(db: AsyncSession, tenant_id: uuid.UUID) -> dict[str, Any]:
    conn = await _connection_for_tenant(db, tenant_id)
    client = await _client_for_tenant(db, tenant_id)
    insights = await client.fetch_location_insights(conn.google_location_name)
    payload = {"insights": insights}
    await _log_sync(db, tenant_id, "analytics", payload)
    await db.commit()
    return {"ok": True, "metrics": insights.get("metrics") or []}
