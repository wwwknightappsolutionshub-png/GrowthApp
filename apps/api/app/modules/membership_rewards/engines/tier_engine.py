"""Tier calculation — upgrade-only recalc."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.membership_rewards.models import MrCustomerLoyalty, MrLoyaltyTier
from app.modules.membership_rewards.services.tenant_loyalty_settings import ensure_default_tiers


async def list_tiers(db: AsyncSession, tenant_id: uuid.UUID) -> list[MrLoyaltyTier]:
    await ensure_default_tiers(db, tenant_id)
    await db.flush()
    q = (
        select(MrLoyaltyTier)
        .where(MrLoyaltyTier.tenant_id == tenant_id)
        .order_by(MrLoyaltyTier.sort_order)
    )
    return list((await db.execute(q)).scalars().all())


async def recalc_tier(
    db: AsyncSession, tenant_id: uuid.UUID, customer_id: uuid.UUID, loyalty: MrCustomerLoyalty
) -> None:
    """Upgrade tier when lifetime points cross thresholds; never downgrade."""
    tiers = await list_tiers(db, tenant_id)
    if not tiers:
        return
    best = tiers[0]
    for t in tiers:
        if loyalty.points_lifetime >= t.min_points_lifetime:
            best = t
    current_order = next((t.sort_order for t in tiers if t.code == loyalty.tier_code), 0)
    if best.sort_order > current_order:
        loyalty.tier_code = best.code
        loyalty.tier_updated_at = datetime.now(timezone.utc)


async def set_tier(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    customer_id: uuid.UUID,
    tier_code: str,
    *,
    loyalty: MrCustomerLoyalty | None = None,
) -> MrCustomerLoyalty:
    """Set tier explicitly (e.g. public enrollment)."""
    from app.modules.membership_rewards.services.customer_loyalty_service import get_or_create_loyalty

    row = loyalty or await get_or_create_loyalty(db, tenant_id, customer_id)
    row.tier_code = tier_code
    row.tier_updated_at = datetime.now(timezone.utc)
    return row
