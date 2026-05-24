"""Customer loyalty profile and ledger reads."""

from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.crm.models import Customer
from app.modules.membership_rewards.models import MrCustomerLoyalty, MrPointsLedger


async def get_or_create_loyalty(
    db: AsyncSession, tenant_id: uuid.UUID, customer_id: uuid.UUID
) -> MrCustomerLoyalty:
    row = await db.get(MrCustomerLoyalty, {"tenant_id": tenant_id, "customer_id": customer_id})
    if not row:
        row = MrCustomerLoyalty(tenant_id=tenant_id, customer_id=customer_id)
        db.add(row)
        await db.flush()
    return row


async def get_customer_loyalty(
    db: AsyncSession, tenant_id: uuid.UUID, customer_id: uuid.UUID
) -> MrCustomerLoyalty:
    return await get_or_create_loyalty(db, tenant_id, customer_id)


async def list_ledger(
    db: AsyncSession, tenant_id: uuid.UUID, customer_id: uuid.UUID, *, limit: int = 50
) -> list[MrPointsLedger]:
    q = (
        select(MrPointsLedger)
        .where(
            MrPointsLedger.tenant_id == tenant_id,
            MrPointsLedger.customer_id == customer_id,
        )
        .order_by(MrPointsLedger.created_at.desc())
        .limit(min(limit, 200))
    )
    return list((await db.execute(q)).scalars().all())


async def list_loyalty_leaderboard(
    db: AsyncSession, tenant_id: uuid.UUID, *, limit: int = 20
) -> list[dict]:
    q = (
        select(MrCustomerLoyalty, Customer)
        .join(Customer, Customer.id == MrCustomerLoyalty.customer_id)
        .where(MrCustomerLoyalty.tenant_id == tenant_id)
        .order_by(MrCustomerLoyalty.points_lifetime.desc())
        .limit(min(limit, 100))
    )
    rows = (await db.execute(q)).all()
    return [
        {
            "customer_id": str(loyalty.customer_id),
            "customer_name": f"{cust.first_name or ''} {cust.last_name or ''}".strip() or cust.email,
            "points_balance": loyalty.points_balance,
            "points_lifetime": loyalty.points_lifetime,
            "tier_code": loyalty.tier_code,
        }
        for loyalty, cust in rows
    ]


async def count_members_with_points(db: AsyncSession, tenant_id: uuid.UUID) -> int:
    return int(
        (
            await db.execute(
                select(func.count())
                .select_from(MrCustomerLoyalty)
                .where(
                    MrCustomerLoyalty.tenant_id == tenant_id,
                    MrCustomerLoyalty.points_balance > 0,
                )
            )
        ).scalar()
        or 0
    )
