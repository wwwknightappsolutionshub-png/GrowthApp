"""Customer loyalty notification triggers."""

from __future__ import annotations

import logging
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.membership_rewards.services.customer_push_service import send_loyalty_push

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
    sent = await send_loyalty_push(
        db,
        tenant_id=tenant_id,
        customer_id=customer_id,
        title=f"+{amount} points earned",
        body=f"{detail} Your balance is now {balance} pts.",
        path="dashboard",
    )
    if not sent:
        logger.info(
            "loyalty points earned tenant=%s customer=%s amount=%s balance=%s",
            tenant_id,
            customer_id,
            amount,
            balance,
        )


async def notify_tier_upgrade(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    customer_id: uuid.UUID,
    tier_name: str,
) -> None:
    sent = await send_loyalty_push(
        db,
        tenant_id=tenant_id,
        customer_id=customer_id,
        title="Tier upgrade!",
        body=f"Congratulations — you've reached {tier_name}.",
        path="dashboard",
    )
    if not sent:
        logger.info(
            "loyalty tier upgrade tenant=%s customer=%s tier=%s",
            tenant_id,
            customer_id,
            tier_name,
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
    sent = await send_loyalty_push(
        db,
        tenant_id=tenant_id,
        customer_id=customer_id,
        title="Reward redeemed",
        body=body,
        path="rewards",
    )
    if not sent:
        logger.info(
            "loyalty reward redeemed tenant=%s customer=%s reward=%s",
            tenant_id,
            customer_id,
            reward_name,
        )


async def notify_points_expiring_soon(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    customer_id: uuid.UUID,
    points: int,
    days_left: int,
) -> None:
    sent = await send_loyalty_push(
        db,
        tenant_id=tenant_id,
        customer_id=customer_id,
        title="Points expiring soon",
        body=f"{points} points expire in {days_left} days. Redeem them before they're gone.",
        path="rewards",
    )
    if not sent:
        logger.info(
            "loyalty points expiring tenant=%s customer=%s points=%s days=%s",
            tenant_id,
            customer_id,
            points,
            days_left,
        )
