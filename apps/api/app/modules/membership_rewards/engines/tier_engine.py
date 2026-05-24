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
        old_code = loyalty.tier_code
        loyalty.tier_code = best.code
        loyalty.tier_updated_at = datetime.now(timezone.utc)
        try:
            from app.modules.membership_rewards.services.notification_triggers import notify_tier_upgrade

            await notify_tier_upgrade(
                db,
                tenant_id=tenant_id,
                customer_id=customer_id,
                tier_name=best.name,
            )
        except Exception:  # noqa: BLE001
            import logging

            logging.getLogger(__name__).exception(
                "loyalty push after tier upgrade failed tenant=%s customer=%s %s->%s",
                tenant_id,
                customer_id,
                old_code,
                best.code,
            )


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


def compute_tier_progress(
    tiers: list[MrLoyaltyTier], points_lifetime: int, current_tier_code: str
) -> dict[str, str | int | None]:
    """Return next-tier targets and progress percent for the customer wallet."""
    if not tiers:
        return {
            "next_tier_code": None,
            "next_tier_name": None,
            "points_to_next_tier": 0,
            "tier_progress_percent": 100,
        }

    ordered = sorted(tiers, key=lambda t: t.sort_order)
    current = next((t for t in ordered if t.code == current_tier_code), ordered[0])
    current_idx = next(i for i, t in enumerate(ordered) if t.code == current.code)

    if current_idx >= len(ordered) - 1:
        return {
            "next_tier_code": None,
            "next_tier_name": None,
            "points_to_next_tier": 0,
            "tier_progress_percent": 100,
        }

    nxt = ordered[current_idx + 1]
    span = max(1, nxt.min_points_lifetime - current.min_points_lifetime)
    progress = max(0, points_lifetime - current.min_points_lifetime)
    percent = min(100, int(round(progress / span * 100)))
    return {
        "next_tier_code": nxt.code,
        "next_tier_name": nxt.name,
        "points_to_next_tier": max(0, nxt.min_points_lifetime - points_lifetime),
        "tier_progress_percent": percent,
    }
