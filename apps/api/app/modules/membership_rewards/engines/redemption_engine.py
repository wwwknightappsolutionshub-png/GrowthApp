"""Reward catalog redemption."""

from __future__ import annotations

import secrets
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequestException, NotFoundException
from app.modules.membership_rewards.models import MrPointsLedger, MrRewardCatalog, MrRewardRedemption
from app.modules.membership_rewards.services.customer_loyalty_service import get_or_create_loyalty

REDEMPTION_CODE_TTL_DAYS = 7


def _generate_fulfillment_code() -> str:
    return secrets.token_hex(4).upper()


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

    now = datetime.now(timezone.utc)
    redemption = MrRewardRedemption(
        tenant_id=tenant_id,
        customer_id=customer_id,
        catalog_item_id=item.id,
        points_spent=item.points_cost,
        status="pending",
        fulfillment_code=_generate_fulfillment_code(),
        code_expires_at=now + timedelta(days=REDEMPTION_CODE_TTL_DAYS),
    )
    db.add(redemption)
    await db.commit()
    await db.refresh(redemption)

    try:
        from app.modules.membership_rewards.services.notification_triggers import notify_reward_redeemed

        await notify_reward_redeemed(
            db,
            tenant_id=tenant_id,
            customer_id=customer_id,
            reward_name=item.name,
            fulfillment_code=redemption.fulfillment_code,
        )
    except Exception:  # noqa: BLE001
        import logging

        logging.getLogger(__name__).exception(
            "loyalty push after redeem failed tenant=%s customer=%s", tenant_id, customer_id
        )

    return redemption


async def fulfill_redemption_by_code(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    fulfillment_code: str,
) -> MrRewardRedemption:
    """Mark a pending redemption as fulfilled when staff validates the one-time code."""
    code = (fulfillment_code or "").strip().upper()
    if not code:
        raise BadRequestException("Redemption code is required")

    redemption = (
        await db.execute(
            select(MrRewardRedemption).where(
                MrRewardRedemption.tenant_id == tenant_id,
                MrRewardRedemption.fulfillment_code == code,
            )
        )
    ).scalar_one_or_none()
    if not redemption:
        raise NotFoundException("Redemption code not found")
    if redemption.status == "fulfilled":
        raise BadRequestException("This redemption code has already been used")
    if redemption.status == "cancelled":
        raise BadRequestException("This redemption code is no longer valid")

    expires = redemption.code_expires_at
    if expires:
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=timezone.utc)
        if expires <= datetime.now(timezone.utc):
            raise BadRequestException("This redemption code has expired")

    redemption.status = "fulfilled"
    redemption.fulfilled_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(redemption)
    return redemption
