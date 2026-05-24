"""Rotating QR tokens for in-store customer identification."""

from __future__ import annotations

import secrets
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequestException, NotFoundException
from app.core.security import hash_token
from app.modules.membership_rewards.constants import CUSTOMER_QR_TOKEN_EXPIRE_MINUTES
from app.modules.membership_rewards.models import MrCustomerQrToken, MrQrScanEvent


async def issue_qr_token(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    customer_id: uuid.UUID,
) -> tuple[str, datetime]:
    """Return (raw_token, expires_at). Revokes previous active tokens for this customer."""
    now = datetime.now(timezone.utc)
    active = (
        await db.execute(
            select(MrCustomerQrToken).where(
                MrCustomerQrToken.tenant_id == tenant_id,
                MrCustomerQrToken.customer_id == customer_id,
                MrCustomerQrToken.revoked_at.is_(None),
                MrCustomerQrToken.expires_at > now,
            )
        )
    ).scalars().all()
    for tok in active:
        tok.revoked_at = now

    raw = secrets.token_urlsafe(32)
    expires_at = now + timedelta(minutes=CUSTOMER_QR_TOKEN_EXPIRE_MINUTES)
    db.add(
        MrCustomerQrToken(
            tenant_id=tenant_id,
            customer_id=customer_id,
            token_hash=hash_token(raw),
            expires_at=expires_at,
        )
    )
    await db.commit()
    return raw, expires_at


async def validate_qr_token(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    raw_token: str,
) -> MrCustomerQrToken:
    now = datetime.now(timezone.utc)
    row = (
        await db.execute(
            select(MrCustomerQrToken).where(
                MrCustomerQrToken.tenant_id == tenant_id,
                MrCustomerQrToken.token_hash == hash_token(raw_token),
                MrCustomerQrToken.revoked_at.is_(None),
                MrCustomerQrToken.expires_at > now,
            )
        )
    ).scalar_one_or_none()
    if not row:
        raise NotFoundException("QR code invalid or expired")
    return row


async def record_scan(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    customer_id: uuid.UUID,
    qr_token: MrCustomerQrToken,
    staff_user_id: uuid.UUID | None = None,
    points_awarded: int | None = None,
) -> MrQrScanEvent:
    if qr_token.customer_id != customer_id or qr_token.tenant_id != tenant_id:
        raise BadRequestException("QR token mismatch")
    event = MrQrScanEvent(
        tenant_id=tenant_id,
        customer_id=customer_id,
        staff_user_id=staff_user_id,
        qr_token_id=qr_token.id,
        points_awarded=points_awarded,
    )
    db.add(event)
    qr_token.revoked_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(event)
    return event
