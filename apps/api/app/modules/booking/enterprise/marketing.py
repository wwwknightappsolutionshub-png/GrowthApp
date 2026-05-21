"""Promo codes, packages, credits, abandoned sessions, booking links."""
from __future__ import annotations

import secrets
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import BadRequestException, NotFoundException
from app.modules.booking.enterprise_schemas import (
    AbandonedSessionCreate,
    BookingPackageCreate,
    BookingPromoCreate,
)
from app.modules.booking.enterprise_models import (
    BookingAbandonedSession,
    BookingCustomerCredit,
    BookingPackage,
    BookingPromoCode,
)
from app.modules.booking.models import Booking


async def create_package(db: AsyncSession, tenant_id: uuid.UUID, data: BookingPackageCreate) -> BookingPackage:
    row = BookingPackage(id=uuid.uuid4(), tenant_id=tenant_id, **data.model_dump())
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return row


async def list_packages(db: AsyncSession, tenant_id: uuid.UUID) -> list[BookingPackage]:
    return list(
        (
            await db.execute(
                select(BookingPackage)
                .where(BookingPackage.tenant_id == tenant_id, BookingPackage.is_active == True)  # noqa: E712
            )
        ).scalars().all()
    )


async def purchase_package_credit(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    package_id: uuid.UUID,
    customer_email: str,
    customer_id: uuid.UUID | None = None,
) -> BookingCustomerCredit:
    pkg = (
        await db.execute(
            select(BookingPackage).where(
                BookingPackage.id == package_id, BookingPackage.tenant_id == tenant_id
            )
        )
    ).scalar_one_or_none()
    if not pkg:
        raise NotFoundException("Package")

    credit = BookingCustomerCredit(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        customer_id=customer_id,
        customer_email=customer_email,
        package_id=pkg.id,
        sessions_remaining=pkg.sessions_included,
        expires_at=datetime.now(timezone.utc) + timedelta(days=pkg.valid_days),
    )
    db.add(credit)
    await db.commit()
    await db.refresh(credit)
    return credit


async def apply_promo(
    db: AsyncSession, tenant_id: uuid.UUID, code: str, amount_pence: int
) -> tuple[int, str]:
    promo = (
        await db.execute(
            select(BookingPromoCode).where(
                BookingPromoCode.tenant_id == tenant_id,
                BookingPromoCode.code == code.upper(),
                BookingPromoCode.is_active == True,  # noqa: E712
            )
        )
    ).scalar_one_or_none()
    if not promo:
        raise NotFoundException("Promo code")
    if promo.expires_at and promo.expires_at < datetime.now(timezone.utc):
        raise BadRequestException("Promo code expired")
    if promo.max_uses is not None and promo.uses_count >= promo.max_uses:
        raise BadRequestException("Promo code fully redeemed")

    discount = promo.discount_pence
    if promo.discount_percent:
        discount = max(discount, int(amount_pence * promo.discount_percent / 100))

    promo.uses_count += 1
    db.add(promo)
    await db.flush()
    return max(0, amount_pence - discount), promo.code


async def create_promo(db: AsyncSession, tenant_id: uuid.UUID, data: BookingPromoCreate) -> BookingPromoCode:
    row = BookingPromoCode(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        code=data.code.upper().strip(),
        discount_percent=data.discount_percent,
        discount_pence=data.discount_pence,
        max_uses=data.max_uses,
        expires_at=data.expires_at,
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return row


async def record_abandoned(db: AsyncSession, tenant_id: uuid.UUID, data: AbandonedSessionCreate) -> BookingAbandonedSession:
    existing = (
        await db.execute(
            select(BookingAbandonedSession).where(
                BookingAbandonedSession.session_token == data.session_token
            )
        )
    ).scalar_one_or_none()
    if existing:
        existing.payload = data.payload
        existing.customer_email = data.customer_email
        db.add(existing)
        await db.commit()
        await db.refresh(existing)
        return existing

    row = BookingAbandonedSession(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        session_token=data.session_token,
        customer_email=data.customer_email,
        payload=data.payload,
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)

    from app.modules.booking.enterprise.automation import schedule_abandoned_recovery

    await schedule_abandoned_recovery(db, tenant_id, data.session_token, data.customer_email)
    return row


def booking_link_for_tenant(slug: str) -> str:
    base = (settings.FRONTEND_URL or "http://localhost:3000").rstrip("/")
    return f"{base}/book/{slug}"


def generate_manage_token() -> str:
    return secrets.token_urlsafe(32)
