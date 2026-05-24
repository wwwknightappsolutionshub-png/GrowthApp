"""Customer loyalty notification triggers."""

from __future__ import annotations

import logging
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.membership_rewards.services.customer_notification_service import notify_loyalty_customer

logger = logging.getLogger(__name__)


async def notify_points_earned(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    customer_id: uuid.UUID,
    amount: int,
    balance: int,
    description: str | None = None,
) -> None:
    detail = description or "Thanks for your loyalty!"
    await notify_loyalty_customer(
        db,
        tenant_id=tenant_id,
        customer_id=customer_id,
        title=f"+{amount} points earned",
        body=f"{detail} Your balance is now {balance} pts.",
        path="dashboard",
        kind="loyalty.points_earned",
    )


async def notify_tier_upgrade(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    customer_id: uuid.UUID,
    tier_name: str,
) -> None:
    await notify_loyalty_customer(
        db,
        tenant_id=tenant_id,
        customer_id=customer_id,
        title="Tier upgrade!",
        body=f"Congratulations — you've reached {tier_name}.",
        path="dashboard",
        kind="loyalty.tier_upgrade",
    )


async def notify_reward_redeemed(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    customer_id: uuid.UUID,
    reward_name: str,
    fulfillment_code: str | None = None,
) -> None:
    body = f"You redeemed {reward_name}."
    if fulfillment_code:
        body = f"{body} Show code {fulfillment_code} in store."
    await notify_loyalty_customer(
        db,
        tenant_id=tenant_id,
        customer_id=customer_id,
        title="Reward redeemed",
        body=body,
        path="rewards",
        kind="loyalty.reward_redeemed",
    )


async def notify_points_expiring_soon(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    customer_id: uuid.UUID,
    points: int,
    days_left: int,
) -> None:
    await notify_loyalty_customer(
        db,
        tenant_id=tenant_id,
        customer_id=customer_id,
        title="Points expiring soon",
        body=f"{points} points expire in {days_left} days. Redeem them before they're gone.",
        path="rewards",
        kind="loyalty.points_expiring",
    )
