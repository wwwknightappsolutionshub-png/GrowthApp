"""Referral Engine — core referral program logic wrapper."""
from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.referrals import service as _svc


async def on_user_signup_with_ref(db: AsyncSession, new_user_id: uuid.UUID, ref_code: str) -> None:
    """Trigger referral event when a new user signs up with a referral code."""
    await _svc.on_user_signup_with_ref(db, new_user_id=new_user_id, ref_code=ref_code)


async def on_booking_created(db: AsyncSession, booking_id: uuid.UUID, tenant_id: uuid.UUID) -> None:
    """Trigger referral event when a booking is created."""
    await _svc.on_booking_created(db, booking_id=booking_id, tenant_id=tenant_id)


async def on_booking_completed(db: AsyncSession, booking_id: uuid.UUID, tenant_id: uuid.UUID) -> None:
    """Trigger referral reward on booking completion."""
    await _svc.on_booking_completed(db, booking_id=booking_id, tenant_id=tenant_id)


async def on_invoice_paid(db: AsyncSession, invoice_id: uuid.UUID, tenant_id: uuid.UUID) -> None:
    """Trigger referral reward on invoice payment."""
    await _svc.on_invoice_paid(db, invoice_id=invoice_id, tenant_id=tenant_id)


async def on_subscription_active_for_tenant(db: AsyncSession, tenant_id: uuid.UUID) -> None:
    """Trigger SaaS referral event when a tenant activates a subscription."""
    await _svc.on_subscription_active_for_tenant(db, tenant_id=tenant_id)


async def get_referral_dashboard(db: AsyncSession, user_id: uuid.UUID) -> dict[str, Any]:
    """Return referrer dashboard statistics for a user."""
    return await _svc.get_referral_dashboard(db, user_id=user_id)
