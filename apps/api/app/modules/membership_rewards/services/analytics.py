"""Loyalty analytics aggregates for tenant dashboard."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.crm.models import Customer
from app.modules.membership_rewards.models import (
    MrCustomerLoyalty,
    MrPointsLedger,
    MrRewardCatalog,
    MrRewardRedemption,
)
from app.modules.membership_rewards.services.customer_loyalty_service import list_loyalty_leaderboard


async def get_analytics(db: AsyncSession, tenant_id: uuid.UUID) -> dict[str, Any]:
    now = datetime.now(timezone.utc)
    since_30d = now - timedelta(days=30)
    expiring_before = now + timedelta(days=30)

    points_by_source_rows = (
        await db.execute(
            select(MrPointsLedger.source, func.coalesce(func.sum(MrPointsLedger.amount), 0))
            .where(
                MrPointsLedger.tenant_id == tenant_id,
                MrPointsLedger.amount > 0,
            )
            .group_by(MrPointsLedger.source)
            .order_by(func.sum(MrPointsLedger.amount).desc())
        )
    ).all()
    points_by_source = {source: int(total) for source, total in points_by_source_rows}

    tier_rows = (
        await db.execute(
            select(MrCustomerLoyalty.tier_code, func.count())
            .where(MrCustomerLoyalty.tenant_id == tenant_id)
            .group_by(MrCustomerLoyalty.tier_code)
        )
    ).all()
    tier_distribution = {code: int(count) for code, count in tier_rows}

    members_total = int(
        (
            await db.execute(
                select(func.count())
                .select_from(MrCustomerLoyalty)
                .where(MrCustomerLoyalty.tenant_id == tenant_id)
            )
        ).scalar()
        or 0
    )
    members_with_balance = int(
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

    redemptions_total = int(
        (
            await db.execute(
                select(func.count())
                .select_from(MrRewardRedemption)
                .where(MrRewardRedemption.tenant_id == tenant_id)
            )
        ).scalar()
        or 0
    )
    redemptions_30d = int(
        (
            await db.execute(
                select(func.count())
                .select_from(MrRewardRedemption)
                .where(
                    MrRewardRedemption.tenant_id == tenant_id,
                    MrRewardRedemption.created_at >= since_30d,
                )
            )
        ).scalar()
        or 0
    )

    points_issued_30d = int(
        (
            await db.execute(
                select(func.coalesce(func.sum(MrPointsLedger.amount), 0)).where(
                    MrPointsLedger.tenant_id == tenant_id,
                    MrPointsLedger.amount > 0,
                    MrPointsLedger.created_at >= since_30d,
                )
            )
        ).scalar()
        or 0
    )
    points_redeemed_30d = int(
        abs(
            (
                await db.execute(
                    select(func.coalesce(func.sum(MrPointsLedger.amount), 0)).where(
                        MrPointsLedger.tenant_id == tenant_id,
                        MrPointsLedger.source == "redeem",
                        MrPointsLedger.created_at >= since_30d,
                    )
                )
            ).scalar()
            or 0
        )
    )

    expiring_points_soon = int(
        (
            await db.execute(
                select(func.coalesce(func.sum(MrPointsLedger.amount), 0)).where(
                    MrPointsLedger.tenant_id == tenant_id,
                    MrPointsLedger.amount > 0,
                    MrPointsLedger.expires_at.isnot(None),
                    MrPointsLedger.expires_at > now,
                    MrPointsLedger.expires_at <= expiring_before,
                )
            )
        ).scalar()
        or 0
    )

    redemption_rate = 0.0
    if members_with_balance > 0:
        redemption_rate = round(redemptions_total / members_with_balance * 100, 1)

    top_customers = await list_loyalty_leaderboard(db, tenant_id, limit=10)

    recent_redemptions = await list_redemptions(db, tenant_id, limit=10)

    return {
        "points_by_source": points_by_source,
        "tier_distribution": tier_distribution,
        "members_total": members_total,
        "members_with_balance": members_with_balance,
        "redemptions_total": redemptions_total,
        "redemptions_30d": redemptions_30d,
        "redemption_rate_percent": redemption_rate,
        "points_issued_30d": points_issued_30d,
        "points_redeemed_30d": points_redeemed_30d,
        "expiring_points_soon": expiring_points_soon,
        "top_customers": top_customers,
        "recent_redemptions": recent_redemptions,
    }


async def list_loyalty_customers(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    *,
    search: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> dict[str, Any]:
    base_filters = [
        MrCustomerLoyalty.tenant_id == tenant_id,
        Customer.tenant_id == tenant_id,
        Customer.deleted_at.is_(None),
    ]
    if search and search.strip():
        term = f"%{search.strip().lower()}%"
        base_filters.append(
            func.lower(Customer.first_name).like(term)
            | func.lower(Customer.last_name).like(term)
            | func.lower(func.coalesce(Customer.email, "")).like(term)
            | func.lower(func.coalesce(Customer.phone, "")).like(term)
        )

    total = int(
        (
            await db.execute(
                select(func.count())
                .select_from(MrCustomerLoyalty)
                .join(Customer, Customer.id == MrCustomerLoyalty.customer_id)
                .where(*base_filters)
            )
        ).scalar()
        or 0
    )

    q = (
        select(MrCustomerLoyalty, Customer)
        .join(Customer, Customer.id == MrCustomerLoyalty.customer_id)
        .where(*base_filters)
        .order_by(MrCustomerLoyalty.points_lifetime.desc())
        .offset(offset)
        .limit(min(limit, 100))
    )
    rows = (await db.execute(q)).all()

    items = [
        {
            "customer_id": str(loyalty.customer_id),
            "customer_name": f"{cust.first_name or ''} {cust.last_name or ''}".strip() or cust.email,
            "email": cust.email,
            "phone": cust.phone,
            "points_balance": loyalty.points_balance,
            "points_lifetime": loyalty.points_lifetime,
            "tier_code": loyalty.tier_code,
        }
        for loyalty, cust in rows
    ]
    return {"items": items, "total": total, "limit": limit, "offset": offset}


async def list_redemptions(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    *,
    status: str | None = None,
    limit: int = 50,
) -> list[dict[str, Any]]:
    q = (
        select(MrRewardRedemption, MrRewardCatalog, Customer)
        .join(MrRewardCatalog, MrRewardCatalog.id == MrRewardRedemption.catalog_item_id)
        .join(Customer, Customer.id == MrRewardRedemption.customer_id)
        .where(MrRewardRedemption.tenant_id == tenant_id)
    )
    if status:
        q = q.where(MrRewardRedemption.status == status)
    q = q.order_by(MrRewardRedemption.created_at.desc()).limit(min(limit, 200))
    rows = (await db.execute(q)).all()

    return [
        {
            "id": str(redemption.id),
            "customer_id": str(redemption.customer_id),
            "customer_name": f"{cust.first_name or ''} {cust.last_name or ''}".strip() or cust.email,
            "reward_name": catalog.name,
            "points_spent": redemption.points_spent,
            "status": redemption.status,
            "created_at": redemption.created_at.isoformat() if redemption.created_at else None,
        }
        for redemption, catalog, cust in rows
    ]
