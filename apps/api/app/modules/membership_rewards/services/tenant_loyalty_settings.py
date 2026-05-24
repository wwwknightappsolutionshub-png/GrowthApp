"""Tenant loyalty settings bootstrap."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.membership_rewards.constants import DEFAULT_EARN_RULES, DEFAULT_TIERS
from app.modules.membership_rewards.models import MrLandingConfig, MrLoyaltyTier, MrTenantSettings
from app.modules.tenants.models import Tenant


async def get_or_create_settings(db: AsyncSession, tenant_id: uuid.UUID) -> MrTenantSettings:
    row = await db.get(MrTenantSettings, tenant_id)
    if not row:
        row = MrTenantSettings(
            tenant_id=tenant_id,
            earn_rules=dict(DEFAULT_EARN_RULES),
            landing_slug="memberships",
        )
        db.add(row)
        await db.flush()
    return row


async def get_settings(db: AsyncSession, tenant_id: uuid.UUID) -> MrTenantSettings:
    return await get_or_create_settings(db, tenant_id)


async def ensure_default_tiers(db: AsyncSession, tenant_id: uuid.UUID) -> None:
    count = (
        await db.execute(
            select(MrLoyaltyTier).where(MrLoyaltyTier.tenant_id == tenant_id).limit(1)
        )
    ).scalar_one_or_none()
    if count:
        return
    for t in DEFAULT_TIERS:
        db.add(
            MrLoyaltyTier(
                tenant_id=tenant_id,
                code=t["code"],
                name=t["name"],
                min_points_lifetime=t["min_points_lifetime"],
                sort_order=t["sort_order"],
            )
        )


async def ensure_landing_config(db: AsyncSession, tenant_id: uuid.UUID) -> MrLandingConfig:
    from app.modules.membership_rewards.landing import build_landing_content, default_booking_cta_url
    from app.modules.membership_rewards.models import MrMembershipPlan

    row = await db.get(MrLandingConfig, tenant_id)
    tenant = await db.get(Tenant, tenant_id)
    if not row:
        plans = list(
            (
                await db.execute(
                    select(MrMembershipPlan)
                    .where(
                        MrMembershipPlan.tenant_id == tenant_id,
                        MrMembershipPlan.is_active.is_(True),
                    )
                    .order_by(MrMembershipPlan.sort_order, MrMembershipPlan.name)
                )
            ).scalars().all()
        )
        tiers = (
            await db.execute(
                select(MrLoyaltyTier)
                .where(MrLoyaltyTier.tenant_id == tenant_id)
                .order_by(MrLoyaltyTier.sort_order)
            )
        ).scalars().all()
        content = build_landing_content(tenant, list(plans), list(tiers)) if tenant else {}
        row = MrLandingConfig(
            tenant_id=tenant_id,
            title=content.get("title", "Membership & Rewards"),
            meta_description=content.get("meta_description"),
            hero=content.get("hero", {}),
            benefits=content.get("benefits", []),
            cta_label=content.get("cta_label", "Join Our Membership Program"),
            cta_href=content.get("cta_href")
            or (default_booking_cta_url(tenant.slug) if tenant else None),
            auto_generated=True,
        )
        db.add(row)
        await db.flush()
    elif tenant and not row.cta_href:
        row.cta_href = default_booking_cta_url(tenant.slug)
        await db.flush()
    return row


async def bootstrap_tenant(db: AsyncSession, tenant_id: uuid.UUID) -> None:
    await get_or_create_settings(db, tenant_id)
    await ensure_default_tiers(db, tenant_id)
    await ensure_landing_config(db, tenant_id)
    await db.flush()
