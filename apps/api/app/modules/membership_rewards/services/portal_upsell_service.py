"""Upsell and engagement payloads for the customer rewards wallet."""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.booking.feedback import refer_url_for_slug
from app.modules.booking.review_link import get_public_google_review_url
from app.modules.crm.models import Customer
from app.modules.membership_rewards.landing import (
    default_booking_cta_url,
    memberships_public_url,
    rewards_portal_url,
)
from app.modules.membership_rewards.models import MrCustomerSubscription, MrMembershipPlan, MrRewardCatalog
from app.modules.membership_rewards.services.portal_service import build_customer_profile
from app.modules.tenants.models import Tenant


async def _resolve_google_review_url(db: AsyncSession, tenant: Tenant) -> str | None:
    url = (tenant.google_review_url or "").strip()
    if url:
        return url
    try:
        payload = await get_public_google_review_url(db, tenant)
        return (payload.get("review_url") or "").strip() or None
    except Exception:  # noqa: BLE001
        return None


async def _active_subscription_payload(
    db: AsyncSession, tenant_id: uuid.UUID, customer_id: uuid.UUID
) -> dict[str, Any] | None:
    row = (
        await db.execute(
            select(MrCustomerSubscription, MrMembershipPlan)
            .join(MrMembershipPlan, MrMembershipPlan.id == MrCustomerSubscription.plan_id)
            .where(
                MrCustomerSubscription.tenant_id == tenant_id,
                MrCustomerSubscription.customer_id == customer_id,
                MrCustomerSubscription.status == "active",
            )
            .order_by(MrCustomerSubscription.created_at.desc())
            .limit(1)
        )
    ).first()
    if not row:
        return None
    sub, plan = row
    benefits: list[str] = []
    if plan.discount_percent:
        benefits.append(f"{plan.discount_percent}% member discount")
    if plan.included_services:
        for svc in plan.included_services[:5]:
            if isinstance(svc, str):
                benefits.append(svc)
            elif isinstance(svc, dict) and svc.get("name"):
                benefits.append(str(svc["name"]))
    return {
        "plan_id": str(plan.id),
        "plan_name": plan.name,
        "plan_description": plan.description,
        "billing_cycle": plan.billing_cycle,
        "price_pence": plan.price_pence,
        "discount_percent": plan.discount_percent,
        "benefits": benefits,
        "status": sub.status,
        "current_period_end": sub.current_period_end.isoformat() if sub.current_period_end else None,
    }


def _build_targeted_offers(
    *,
    profile: dict[str, Any],
    has_active_subscription: bool,
    affordable_rewards: list[dict[str, Any]],
) -> list[dict[str, str]]:
    offers: list[dict[str, str]] = []
    booking_url = profile.get("booking_url") or ""
    memberships_url = profile.get("memberships_url") or ""
    rewards_url = profile.get("rewards_catalog_url") or ""

    if profile.get("points_to_next_tier", 0) > 0 and profile.get("next_tier_name"):
        pts = int(profile["points_to_next_tier"])
        tier = str(profile["next_tier_name"])
        offers.append(
            {
                "type": "tier_progress",
                "title": f"{pts} points to {tier}",
                "body": "Book your next visit and earn points faster toward your next tier.",
                "cta_label": "Book now",
                "cta_url": booking_url,
            }
        )

    if int(profile.get("points_expiring_soon") or 0) > 0:
        exp = int(profile["points_expiring_soon"])
        offers.append(
            {
                "type": "expiring_points",
                "title": f"{exp} points expiring soon",
                "body": "Redeem your points before they expire.",
                "cta_label": "Browse rewards",
                "cta_url": rewards_url,
            }
        )

    if affordable_rewards:
        top = affordable_rewards[0]
        offers.append(
            {
                "type": "redeem_ready",
                "title": f"Redeem: {top['name']}",
                "body": f"You have enough points for {top['name']} ({top['points_cost']} pts).",
                "cta_label": "Redeem now",
                "cta_url": rewards_url,
            }
        )

    if not has_active_subscription and memberships_url:
        offers.append(
            {
                "type": "upgrade_membership",
                "title": "Unlock member perks",
                "body": "Upgrade to a paid membership for exclusive discounts and bonus points.",
                "cta_label": "View plans",
                "cta_url": memberships_url,
            }
        )

    return offers[:4]


async def build_portal_upsell(
    db: AsyncSession, tenant: Tenant, customer: Customer
) -> dict[str, Any]:
    profile = await build_customer_profile(db, tenant, customer)
    slug = tenant.slug

    memberships_url = memberships_public_url(slug)
    refer_win_url = refer_url_for_slug(slug)
    booking_url = default_booking_cta_url(slug)
    rewards_catalog_url = f"{rewards_portal_url(slug)}/rewards"

    google_review_url = await _resolve_google_review_url(db, tenant)
    subscription = await _active_subscription_payload(db, tenant.id, customer.id)

    catalog = list(
        (
            await db.execute(
                select(MrRewardCatalog).where(
                    MrRewardCatalog.tenant_id == tenant.id,
                    MrRewardCatalog.is_active.is_(True),
                )
            )
        ).scalars().all()
    )
    balance = int(profile.get("points_balance") or 0)
    affordable = [
        {"id": str(item.id), "name": item.name, "points_cost": item.points_cost}
        for item in catalog
        if item.points_cost <= balance
        and (item.stock_remaining is None or item.stock_remaining > 0)
    ]
    affordable.sort(key=lambda x: x["points_cost"], reverse=True)

    profile_enriched = {
        **profile,
        "memberships_url": memberships_url,
        "refer_win_url": refer_win_url,
        "booking_url": booking_url,
        "rewards_catalog_url": rewards_catalog_url,
        "google_review_url": google_review_url,
    }

    targeted_offers = _build_targeted_offers(
        profile=profile_enriched,
        has_active_subscription=subscription is not None,
        affordable_rewards=affordable,
    )

    plans_count = len(
        list(
            (
                await db.execute(
                    select(MrMembershipPlan).where(
                        MrMembershipPlan.tenant_id == tenant.id,
                        MrMembershipPlan.is_active.is_(True),
                    )
                )
            ).scalars().all()
        )
    )

    return {
        "memberships_url": memberships_url,
        "refer_win_url": refer_win_url,
        "booking_url": booking_url,
        "google_review_url": google_review_url,
        "google_review_available": bool(google_review_url),
        "has_membership_plans": plans_count > 0,
        "active_subscription": subscription,
        "targeted_offers": targeted_offers,
        "affordable_rewards_count": len(affordable),
    }
