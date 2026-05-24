"""Process inbound social webhooks from Zapier/Make/N8N."""
from __future__ import annotations

import logging
import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.integrations.auth.social_auth import resolve_channel, verify_signature
from app.modules.integrations.mappers.inbound_mapper import ingest_social_webhook
from app.modules.integrations.models import TenantSocialWebhookLog
from app.modules.integrations.social import service as social_service
from app.modules.integrations.validators.social_payload import SocialWebhookPayload

logger = logging.getLogger(__name__)


async def handle_social_webhook(
    db: AsyncSession,
    *,
    channel_id: str,
    api_key: str,
    body: bytes,
    signature: str | None,
    payload_dict: dict[str, Any],
) -> dict[str, Any]:
    channel = await resolve_channel(db, channel_id=channel_id, api_key=api_key)

    if signature and not verify_signature(channel, body, signature):
        log = TenantSocialWebhookLog(
            id=uuid.uuid4(),
            tenant_id=channel.tenant_id,
            channel_type=channel.channel_type,
            incoming_payload={"error": "invalid_signature", "raw": payload_dict},
            status="rejected",
        )
        db.add(log)
        await db.commit()
        return {"ok": False, "error": "invalid_signature"}

    payload = SocialWebhookPayload.model_validate(payload_dict)
    if payload.platform != channel.channel_type:
        payload.platform = channel.channel_type  # type: ignore[assignment]

    log = TenantSocialWebhookLog(
        id=uuid.uuid4(),
        tenant_id=channel.tenant_id,
        channel_type=channel.channel_type,
        incoming_payload=payload_dict,
        status="processing",
    )
    db.add(log)
    await db.flush()

    try:
        result = await ingest_social_webhook(db, channel.tenant_id, payload)
        log.status = "processed"
        db.add(log)
        await social_service.mark_channel_connected(db, channel)
        await db.commit()
        return {"ok": True, **result}
    except Exception as exc:  # noqa: BLE001
        logger.exception("Social webhook processing failed channel=%s", channel_id)
        log.status = "failed"
        log.incoming_payload = {**payload_dict, "error": str(exc)}
        db.add(log)
        await db.commit()
        return {"ok": False, "error": "processing_failed"}
