"""Social channel provisioning and outbound posting via Zapier/Make."""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import BadRequestException, NotFoundException
from app.modules.integrations.auth.social_auth import (
    generate_api_key,
    generate_api_secret,
)
from app.modules.integrations.models import TenantSocialChannel, TenantSocialWebhookLog
from app.modules.integrations.token_crypto import encrypt_secret

logger = logging.getLogger(__name__)

SOCIAL_PLATFORMS = ("facebook", "instagram", "linkedin", "tiktok")


def _public_api_base() -> str:
    return (settings.PUBLIC_API_BASE_URL or settings.FRONTEND_URL).rstrip("/")


def webhook_url_for(channel_id: uuid.UUID, api_key: str) -> str:
    return f"{_public_api_base()}/api/v1/integrations/webhooks/social/{channel_id}?key={api_key}"


async def list_channels(db: AsyncSession, tenant_id: uuid.UUID) -> list[TenantSocialChannel]:
    rows = (
        await db.execute(
            select(TenantSocialChannel)
            .where(TenantSocialChannel.tenant_id == tenant_id)
            .order_by(TenantSocialChannel.channel_type)
        )
    ).scalars().all()
    return list(rows)


async def get_channel(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    channel_type: str,
) -> TenantSocialChannel | None:
    return (
        await db.execute(
            select(TenantSocialChannel).where(
                TenantSocialChannel.tenant_id == tenant_id,
                TenantSocialChannel.channel_type == channel_type,
            )
        )
    ).scalar_one_or_none()


async def provision_channel(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    channel_type: str,
) -> TenantSocialChannel:
    channel_type = channel_type.lower()
    if channel_type not in SOCIAL_PLATFORMS:
        raise BadRequestException(f"Unsupported platform: {channel_type}")

    existing = await get_channel(db, tenant_id, channel_type)
    if existing:
        return existing

    api_key = generate_api_key()
    api_secret = generate_api_secret()
    channel_id = uuid.uuid4()
    row = TenantSocialChannel(
        id=channel_id,
        tenant_id=tenant_id,
        channel_type=channel_type,
        api_key=api_key,
        api_secret_encrypted=encrypt_secret(api_secret),
        webhook_url=webhook_url_for(channel_id, api_key),
        zapier_integration_key=generate_api_key()[:32],
        make_integration_key=generate_api_key()[:32],
        status="pending",
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return row


def channel_response(row: TenantSocialChannel, *, include_secret: bool = False) -> dict[str, Any]:
    data: dict[str, Any] = {
        "id": str(row.id),
        "channel_type": row.channel_type,
        "webhook_url": row.webhook_url,
        "api_key": row.api_key,
        "zapier_integration_key": row.zapier_integration_key,
        "make_integration_key": row.make_integration_key,
        "status": row.status,
        "connected_at": row.connected_at.isoformat() if row.connected_at else None,
    }
    if include_secret:
        data["setup_note"] = "API secret is only shown once at creation — store it in Zapier/Make."
    return data


async def mark_channel_connected(db: AsyncSession, row: TenantSocialChannel) -> None:
    row.status = "connected"
    row.updated_at = datetime.now(timezone.utc)
    db.add(row)


async def post_to_social(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    *,
    platform: str,
    content: str,
    media_url: str | None = None,
) -> dict[str, Any]:
    row = await get_channel(db, tenant_id, platform.lower())
    if not row:
        raise BadRequestException(f"Connect {platform} via Zapier/Make first")

    outbound = {
        "event_type": "outbound_post",
        "platform": platform.lower(),
        "content": content,
        "media_url": media_url,
        "tenant_id": str(tenant_id),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    # Zapier/Make catch hooks are configured by the tenant using the webhook URL.
    # We POST back to the same webhook URL as an outgoing trigger payload.
    status = "queued"
    response_body: dict[str, Any] = {}
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(row.webhook_url, json=outbound)
        response_body = {"status_code": resp.status_code, "body": resp.text[:500]}
        status = "sent" if resp.status_code < 400 else "failed"
    except httpx.HTTPError as exc:
        logger.warning("Social post webhook failed tenant=%s platform=%s: %s", tenant_id, platform, exc)
        status = "failed"
        response_body = {"error": str(exc)}

    db.add(
        TenantSocialWebhookLog(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            channel_type=platform.lower(),
            incoming_payload={"direction": "outbound", **outbound, "response": response_body},
            status=status,
        )
    )
    await db.commit()
    return {"status": status, "platform": platform.lower(), "response": response_body}


async def get_channel_by_id(db: AsyncSession, channel_id: uuid.UUID) -> TenantSocialChannel:
    row = (
        await db.execute(select(TenantSocialChannel).where(TenantSocialChannel.id == channel_id))
    ).scalar_one_or_none()
    if not row:
        raise NotFoundException("Social channel")
    return row
