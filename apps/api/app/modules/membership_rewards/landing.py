"""Membership landing page generation, sync, and URLs."""

from __future__ import annotations

import os
import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.membership_rewards.models import (
    MrLandingConfig,
    MrLoyaltyTier,
    MrMembershipPlan,
    MrTenantSettings,
)
from app.modules.tenants.models import Tenant


def frontend_base_url() -> str:
    return os.getenv("FRONTEND_URL", "https://app.customerflow.ai").rstrip("/")


def memberships_public_path(tenant_slug: str) -> str:
    return f"/p/{tenant_slug}/memberships"


def memberships_public_url(tenant_slug: str) -> str:
    return f"{frontend_base_url()}{memberships_public_path(tenant_slug)}"


def default_booking_cta_url(tenant_slug: str) -> str:
    return f"{frontend_base_url()}/book/{tenant_slug}"


def build_hero(tenant_name: str, plans: list[MrMembershipPlan]) -> dict[str, str]:
    if not plans:
        return {
            "headline": f"Welcome to {tenant_name} Rewards",
            "subheadline": "Earn points on every visit. Redeem rewards. Unlock member-only perks.",
        }
    cheapest = min(plans, key=lambda p: p.price_pence)
    price = f"£{cheapest.price_pence / 100:.2f}"
    return {
        "headline": f"Join {tenant_name} — memberships from {price}",
        "subheadline": (
            f"Choose from {len(plans)} plan{'s' if len(plans) != 1 else ''}. "
            "Earn loyalty points, unlock tiers, and enjoy member discounts."
        ),
    }


def build_benefits(
    plans: list[MrMembershipPlan], tiers: list[MrLoyaltyTier]
) -> list[dict[str, str]]:
    benefits: list[dict[str, str]] = [
        {
            "title": "Earn points",
            "body": "Get rewarded every time you book, purchase, or leave a review.",
        },
    ]
    if plans:
        max_discount = max((p.discount_percent for p in plans), default=0)
        if max_discount:
            benefits.append(
                {
                    "title": "Member pricing",
                    "body": f"Save up to {max_discount}% as a subscriber.",
                }
            )
        else:
            benefits.append(
                {
                    "title": "Flexible plans",
                    "body": f"{len(plans)} membership option{'s' if len(plans) != 1 else ''} to fit your needs.",
                }
            )
    if tiers:
        top = max(tiers, key=lambda t: t.sort_order)
        benefits.append(
            {
                "title": f"{top.name} tier & beyond",
                "body": "Climb Bronze → Platinum and unlock bigger perks over time.",
            }
        )
    else:
        benefits.append(
            {
                "title": "VIP tiers",
                "body": "Bronze through Platinum — the more you visit, the more you earn.",
            }
        )
    return benefits[:4]


def build_landing_content(
    tenant: Tenant,
    plans: list[MrMembershipPlan],
    tiers: list[MrLoyaltyTier],
) -> dict[str, Any]:
    biz = tenant.name or "Our Business"
    return {
        "title": f"{biz} — Membership & Rewards",
        "meta_description": (
            f"Join {biz}'s membership program. "
            + (f"Plans from £{min(p.price_pence for p in plans) / 100:.0f}." if plans else "Earn points and redeem rewards.")
        ),
        "hero": build_hero(biz, plans),
        "benefits": build_benefits(plans, tiers),
        "cta_label": "Book now" if plans else "Join Our Membership Program",
        "cta_href": default_booking_cta_url(tenant.slug),
    }


async def sync_landing_from_plans(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    *,
    force: bool = False,
    auto_publish: bool = False,
) -> MrLandingConfig:
    """Refresh auto-generated landing copy from active plans and tiers."""
    from app.modules.membership_rewards.service import (
        _ensure_landing_config,
        _get_or_create_settings,
        list_plans,
        list_tiers,
        publish_landing,
    )

    tenant = await db.get(Tenant, tenant_id)
    if not tenant:
        raise ValueError("tenant not found")

    cfg = await _ensure_landing_config(db, tenant_id)
    if not force and not cfg.auto_generated:
        if auto_publish:
            plans = await list_plans(db, tenant_id, active_only=True)
            if plans:
                await publish_landing(db, tenant_id)
        return cfg

    plans = await list_plans(db, tenant_id, active_only=True)
    tiers = await list_tiers(db, tenant_id)
    content = build_landing_content(tenant, plans, tiers)

    cfg.title = content["title"]
    cfg.meta_description = content["meta_description"]
    cfg.hero = content["hero"]
    cfg.benefits = content["benefits"]
    cfg.cta_label = content["cta_label"]
    if not cfg.cta_href or force:
        cfg.cta_href = content["cta_href"]
    cfg.auto_generated = True

    settings = await _get_or_create_settings(db, tenant_id)
    await db.flush()

    if auto_publish and plans:
        cfg.published = True
        settings.landing_published = True

    await db.commit()
    await db.refresh(cfg)
    return cfg


async def landing_urls(db: AsyncSession, tenant_id: uuid.UUID) -> dict[str, str | None]:
    tenant = await db.get(Tenant, tenant_id)
    settings = await db.get(MrTenantSettings, tenant_id)
    if not tenant:
        return {"public_url": None, "preview_path": None, "booking_cta_url": None}
    path = memberships_public_path(tenant.slug)
    published = bool(settings and settings.landing_published)
    return {
        "public_url": memberships_public_url(tenant.slug) if published else None,
        "preview_path": path,
        "booking_cta_url": default_booking_cta_url(tenant.slug),
    }
