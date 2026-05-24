"""Points earning, adjustments, and expiration sweep."""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequestException
from app.modules.membership_rewards.constants import POINT_SOURCES
from app.modules.membership_rewards.engines.tier_engine import recalc_tier
from app.modules.membership_rewards.models import MrCustomerLoyalty, MrPointsLedger
from app.modules.membership_rewards.services.customer_loyalty_service import get_or_create_loyalty
from app.modules.membership_rewards.services.tenant_loyalty_settings import get_or_create_settings

logger = logging.getLogger(__name__)


async def earn_points(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    customer_id: uuid.UUID,
    amount: int,
    *,
    source: str,
    description: str | None = None,
    reference_type: str | None = None,
    reference_id: uuid.UUID | None = None,
) -> MrPointsLedger:
    if amount <= 0:
        raise BadRequestException("earn amount must be positive")
    if source not in POINT_SOURCES:
        raise BadRequestException(f"invalid source: {source}")

    loyalty = await get_or_create_loyalty(db, tenant_id, customer_id)
    loyalty.points_balance += amount
    loyalty.points_lifetime += amount
    balance = loyalty.points_balance

    settings = await get_or_create_settings(db, tenant_id)
    expires_at = None
    if settings.points_expire_days:
        expires_at = datetime.now(timezone.utc) + timedelta(days=settings.points_expire_days)

    entry = MrPointsLedger(
        tenant_id=tenant_id,
        customer_id=customer_id,
        amount=amount,
        balance_after=balance,
        source=source,
        reference_type=reference_type,
        reference_id=reference_id,
        description=description,
        expires_at=expires_at,
    )
    db.add(entry)
    await recalc_tier(db, tenant_id, customer_id, loyalty)
    await db.commit()
    await db.refresh(entry)
    return entry


async def adjust_points(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    customer_id: uuid.UUID,
    amount: int,
    *,
    source: str = "adjustment",
    description: str | None = None,
) -> MrPointsLedger:
    if amount == 0:
        raise BadRequestException("amount cannot be zero")
    if source not in POINT_SOURCES:
        raise BadRequestException(f"invalid source: {source}")

    loyalty = await get_or_create_loyalty(db, tenant_id, customer_id)
    if amount < 0 and loyalty.points_balance + amount < 0:
        raise BadRequestException("insufficient points balance")

    loyalty.points_balance += amount
    if amount > 0:
        loyalty.points_lifetime += amount
    balance = loyalty.points_balance

    entry = MrPointsLedger(
        tenant_id=tenant_id,
        customer_id=customer_id,
        amount=amount,
        balance_after=balance,
        source=source,
        description=description,
    )
    db.add(entry)
    await recalc_tier(db, tenant_id, customer_id, loyalty)
    await db.commit()
    await db.refresh(entry)
    return entry


async def sweep_expired_points(db: AsyncSession) -> int:
    """Expire positive ledger entries past expires_at; deduct from balance once per entry."""
    now = datetime.now(timezone.utc)
    q = (
        select(MrPointsLedger)
        .where(
            MrPointsLedger.amount > 0,
            MrPointsLedger.expires_at.isnot(None),
            MrPointsLedger.expires_at <= now,
        )
        .order_by(MrPointsLedger.expires_at)
        .limit(500)
    )
    rows = list((await db.execute(q)).scalars().all())
    expired_count = 0

    for entry in rows:
        already = (
            await db.execute(
                select(MrPointsLedger.id)
                .where(
                    MrPointsLedger.tenant_id == entry.tenant_id,
                    MrPointsLedger.customer_id == entry.customer_id,
                    MrPointsLedger.source == "expiration",
                    MrPointsLedger.reference_type == "points_ledger",
                    MrPointsLedger.reference_id == entry.id,
                )
                .limit(1)
            )
        ).scalar_one_or_none()
        if already:
            continue

        loyalty = await db.get(
            MrCustomerLoyalty,
            {"tenant_id": entry.tenant_id, "customer_id": entry.customer_id},
        )
        if not loyalty:
            continue

        deduct = min(entry.amount, max(0, loyalty.points_balance))
        if deduct <= 0:
            continue

        loyalty.points_balance -= deduct
        db.add(
            MrPointsLedger(
                tenant_id=entry.tenant_id,
                customer_id=entry.customer_id,
                amount=-deduct,
                balance_after=loyalty.points_balance,
                source="expiration",
                reference_type="points_ledger",
                reference_id=entry.id,
                description=f"Points expired ({deduct} pts)",
            )
        )
        expired_count += 1

    if expired_count:
        await db.commit()
        logger.info("loyalty points expiration sweep: expired_entries=%s", expired_count)
    return expired_count
