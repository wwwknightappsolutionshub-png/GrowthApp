"""Reward catalog redemption."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequestException, NotFoundException
from app.modules.membership_rewards.models import MrPointsLedger, MrRewardCatalog, MrRewardRedemption
from app.modules.membership_rewards.services.customer_loyalty_service import get_or_create_loyalty


async def redeem_reward(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    customer_id: uuid.UUID,
    catalog_item_id: uuid.UUID,
) -> MrRewardRedemption:
    item = (
        await db.execute(
            select(MrRewardCatalog).where(
                MrRewardCatalog.id == catalog_item_id,
                MrRewardCatalog.tenant_id == tenant_id,
                MrRewardCatalog.is_active.is_(True),
            )
        )
    ).scalar_one_or_none()
    if not item:
        raise NotFoundException("Reward not found")
    if item.stock_remaining is not None and item.stock_remaining <= 0:
        raise BadRequestException("Reward out of stock")

    loyalty = await get_or_create_loyalty(db, tenant_id, customer_id)
    if loyalty.points_balance < item.points_cost:
        raise BadRequestException("insufficient points")

    loyalty.points_balance -= item.points_cost
    db.add(
        MrPointsLedger(
            tenant_id=tenant_id,
            customer_id=customer_id,
            amount=-item.points_cost,
            balance_after=loyalty.points_balance,
            source="redeem",
            reference_type="reward_catalog",
            reference_id=item.id,
            description=f"Redeemed: {item.name}",
        )
    )

    if item.stock_remaining is not None:
        item.stock_remaining -= 1

    redemption = MrRewardRedemption(
        tenant_id=tenant_id,
        customer_id=customer_id,
        catalog_item_id=item.id,
        points_spent=item.points_cost,
        status="fulfilled",
    )
    db.add(redemption)
    await db.commit()
    await db.refresh(redemption)
    return redemption
