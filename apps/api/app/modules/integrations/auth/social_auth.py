"""Verify social webhook API keys."""
from __future__ import annotations

import hashlib
import hmac
import secrets

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequestException
from app.modules.integrations.models import TenantSocialChannel
from app.modules.integrations.token_crypto import decrypt_secret


def generate_api_key() -> str:
    return secrets.token_urlsafe(32)


def generate_api_secret() -> str:
    return secrets.token_urlsafe(48)


def sign_payload(secret: str, body: bytes) -> str:
    return hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()


async def resolve_channel(
    db: AsyncSession,
    *,
    channel_id: str,
    api_key: str,
) -> TenantSocialChannel:
    from uuid import UUID

    try:
        cid = UUID(channel_id)
    except ValueError as exc:
        raise BadRequestException("Invalid channel id") from exc

    row = (
        await db.execute(select(TenantSocialChannel).where(TenantSocialChannel.id == cid))
    ).scalar_one_or_none()
    if not row or not hmac.compare_digest(row.api_key, api_key):
        raise BadRequestException("Invalid webhook credentials")
    return row


def verify_signature(channel: TenantSocialChannel, body: bytes, signature: str | None) -> bool:
    if not signature:
        return False
    secret = decrypt_secret(channel.api_secret_encrypted)
    expected = sign_payload(secret, body)
    return hmac.compare_digest(expected, signature.strip())
