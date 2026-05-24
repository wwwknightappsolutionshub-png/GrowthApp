"""Membership & Rewards — tenant plans, points ledger, tiers, trial, landing."""

from __future__ import annotations

import logging
import os
import uuid
from datetime import date, datetime, timedelta, timezone
from typing import Any

from dateutil.relativedelta import relativedelta
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import BadRequestException, NotFoundException
from app.modules.accounting.models import TenantAddon
from app.modules.membership_rewards.constants import (
    BILLING_CYCLES,
    FEATURE_MEMBERSHIP_REWARDS,
    TRIAL_DAYS,
    WINBACK_DISCOUNT_PERCENT,
)
from app.modules.membership_rewards.entitlement import tenant_has_membership_rewards
from app.modules.membership_rewards.engines.earning_engine import adjust_points, earn_points
from app.modules.membership_rewards.engines.redemption_engine import redeem_reward
from app.modules.membership_rewards.engines.reward_rules import (
    has_loyalty_signup_bonus,
    membership_signup_bonus_points,
)
from app.modules.membership_rewards.engines.tier_engine import list_tiers
from app.modules.membership_rewards.services.customer_loyalty_service import (
    get_customer_loyalty,
    list_ledger,
    list_loyalty_leaderboard,
)
from app.modules.membership_rewards.services.tenant_loyalty_settings import (
    bootstrap_tenant,
    ensure_landing_config as _ensure_landing_config,
    get_or_create_settings as _get_or_create_settings,
    get_settings,
)
from app.modules.crm.models import Customer
from app.modules.membership_rewards.models import (
    MrCustomerLoyalty,
    MrCustomerSubscription,
    MrLandingConfig,
    MrLoyaltyTier,
    MrMembershipPlan,
    MrPointsLedger,
    MrRewardCatalog,
    MrRewardRedemption,
    MrTenantSettings,
    MrTrialReminders,
)
from app.modules.membership_rewards.services.customer_loyalty_service import get_or_create_loyalty
from app.modules.membership_rewards.schemas import (
    CatalogItemCreate,
    EarnRulesUpdate,
    LandingConfigUpdate,
    PlanCreate,
    PlanUpdate,
)
from app.modules.tenants.models import Tenant

logger = logging.getLogger(__name__)


# ── Status & entitlement ─────────────────────────────────────────────────────


async def get_status(db: AsyncSession, tenant_id: uuid.UUID) -> dict[str, Any]:
    row = (
        await db.execute(
            select(TenantAddon).where(
                TenantAddon.tenant_id == tenant_id,
                TenantAddon.feature_code == FEATURE_MEMBERSHIP_REWARDS,
            )
        )
    ).scalar_one_or_none()
    active = await tenant_has_membership_rewards(db, tenant_id)
    trial = (
        await db.execute(select(MrTrialReminders).where(MrTrialReminders.tenant_id == tenant_id))
    ).scalar_one_or_none()
    tenant_settings = await _get_or_create_settings(db, tenant_id)
    tenant = await db.get(Tenant, tenant_id)
    landing_url = None
    if tenant and tenant_settings.landing_published:
        frontend = os.getenv("FRONTEND_URL", "https://app.customerflow.ai").rstrip("/")
        landing_url = f"{frontend}/p/{tenant.slug}/memberships"
    from app.modules.membership_rewards.reminders import get_trial_status

    trial_payload = await get_trial_status(db, tenant_id)
    now = datetime.now(timezone.utc)
    expires = row.expires_at if row else None
    if expires and expires.tzinfo is None:
        expires = expires.replace(tzinfo=timezone.utc)
    is_trial = bool(
        row
        and row.status == "active"
        and expires
        and expires > now
        and not (trial and trial.converted_at)
    )
    is_paid = bool(
        active
        and not is_trial
        and row
        and (row.stripe_subscription_item_id or (trial and trial.converted_at))
    )
    billing_source: str | None = None
    if active:
        if is_trial:
            billing_source = "trial"
        elif row and row.stripe_subscription_item_id:
            billing_source = "stripe"
        else:
            billing_source = "grant"
    return {
        "has_membership_rewards": active,
        "feature_code": FEATURE_MEMBERSHIP_REWARDS,
        "status": row.status if row else None,
        "expires_at": row.expires_at if row else None,
        "trial_ends_at": trial.trial_ends_at if trial and not trial.converted_at else None,
        "landing_url": landing_url,
        "trial": trial_payload,
        "stripe_configured": bool(settings.STRIPE_PRICE_MEMBERSHIP_REWARDS),
        "is_trial": is_trial,
        "is_paid": is_paid,
        "billing_source": billing_source,
    }


async def grant_addon(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    *,
    granted_by: uuid.UUID | None = None,
    expires_at: datetime | None = None,
    mark_trial_converted: bool = True,
) -> TenantAddon:
    row = (
        await db.execute(
            select(TenantAddon).where(
                TenantAddon.tenant_id == tenant_id,
                TenantAddon.feature_code == FEATURE_MEMBERSHIP_REWARDS,
            )
        )
    ).scalar_one_or_none()
    now = datetime.now(timezone.utc)
    if row:
        row.status = "active"
        row.granted_by = granted_by
        row.granted_at = now
        row.expires_at = expires_at
    else:
        row = TenantAddon(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            feature_code=FEATURE_MEMBERSHIP_REWARDS,
            status="active",
            granted_by=granted_by,
            granted_at=now,
            expires_at=expires_at,
        )
        db.add(row)
    await bootstrap_tenant(db, tenant_id)
    if mark_trial_converted:
        trial = (
            await db.execute(select(MrTrialReminders).where(MrTrialReminders.tenant_id == tenant_id))
        ).scalar_one_or_none()
        if trial and not trial.converted_at:
            trial.converted_at = now
    await db.commit()
    await db.refresh(row)
    return row


async def revoke_addon(db: AsyncSession, tenant_id: uuid.UUID) -> None:
    row = (
        await db.execute(
            select(TenantAddon).where(
                TenantAddon.tenant_id == tenant_id,
                TenantAddon.feature_code == FEATURE_MEMBERSHIP_REWARDS,
            )
        )
    ).scalar_one_or_none()
    if row:
        row.status = "canceled"
        await db.commit()


async def start_trial_for_tenant(db: AsyncSession, tenant_id: uuid.UUID) -> TenantAddon:
    """Grant 7-day trial on signup; idempotent if already active."""
    if await tenant_has_membership_rewards(db, tenant_id):
        return (
            await db.execute(
                select(TenantAddon).where(
                    TenantAddon.tenant_id == tenant_id,
                    TenantAddon.feature_code == FEATURE_MEMBERSHIP_REWARDS,
                )
            )
        ).scalar_one()

    now = datetime.now(timezone.utc)
    ends = now + timedelta(days=TRIAL_DAYS)
    addon = await grant_addon(db, tenant_id, expires_at=ends, mark_trial_converted=False)

    existing = (
        await db.execute(select(MrTrialReminders).where(MrTrialReminders.tenant_id == tenant_id))
    ).scalar_one_or_none()
    if not existing:
        db.add(
            MrTrialReminders(
                tenant_id=tenant_id,
                trial_started_at=now,
                trial_ends_at=ends,
                winback_discount_percent=WINBACK_DISCOUNT_PERCENT,
            )
        )
        await db.commit()
    return addon


# ── Settings ─────────────────────────────────────────────────────────────────


async def update_settings(db: AsyncSession, tenant_id: uuid.UUID, data: EarnRulesUpdate) -> MrTenantSettings:
    row = await _get_or_create_settings(db, tenant_id)
    row.earn_rules = data.earn_rules
    row.points_expire_days = data.points_expire_days
    await db.commit()
    await db.refresh(row)
    return row


# ── Plans ────────────────────────────────────────────────────────────────────


async def list_plans(db: AsyncSession, tenant_id: uuid.UUID, *, active_only: bool = False) -> list[MrMembershipPlan]:
    q = select(MrMembershipPlan).where(MrMembershipPlan.tenant_id == tenant_id)
    if active_only:
        q = q.where(MrMembershipPlan.is_active.is_(True))
    q = q.order_by(MrMembershipPlan.sort_order, MrMembershipPlan.name)
    return list((await db.execute(q)).scalars().all())


async def create_plan(db: AsyncSession, tenant_id: uuid.UUID, data: PlanCreate) -> MrMembershipPlan:
    if data.billing_cycle not in BILLING_CYCLES:
        raise BadRequestException(f"billing_cycle must be one of: {', '.join(sorted(BILLING_CYCLES))}")
    row = MrMembershipPlan(tenant_id=tenant_id, **data.model_dump())
    db.add(row)
    await db.commit()
    await db.refresh(row)
    from app.modules.membership_rewards.landing import sync_landing_from_plans

    await sync_landing_from_plans(db, tenant_id, auto_publish=True)
    return row


async def update_plan(
    db: AsyncSession, tenant_id: uuid.UUID, plan_id: uuid.UUID, data: PlanUpdate
) -> MrMembershipPlan:
    row = await _get_plan(db, tenant_id, plan_id)
    for k, v in data.model_dump(exclude_unset=True).items():
        if k == "billing_cycle" and v not in BILLING_CYCLES:
            raise BadRequestException(f"billing_cycle must be one of: {', '.join(sorted(BILLING_CYCLES))}")
        setattr(row, k, v)
    await db.commit()
    await db.refresh(row)
    from app.modules.membership_rewards.landing import sync_landing_from_plans

    await sync_landing_from_plans(db, tenant_id, auto_publish=False)
    return row


async def delete_plan(db: AsyncSession, tenant_id: uuid.UUID, plan_id: uuid.UUID) -> None:
    row = await _get_plan(db, tenant_id, plan_id)
    active_subs = (
        await db.execute(
            select(func.count())
            .select_from(MrCustomerSubscription)
            .where(
                MrCustomerSubscription.tenant_id == tenant_id,
                MrCustomerSubscription.plan_id == plan_id,
                MrCustomerSubscription.status == "active",
            )
        )
    ).scalar_one()
    if active_subs:
        raise BadRequestException(
            "Cannot delete a plan with active subscriptions. Deactivate the plan instead."
        )
    await db.delete(row)
    await db.commit()
    from app.modules.membership_rewards.landing import sync_landing_from_plans

    await sync_landing_from_plans(db, tenant_id, auto_publish=False)


async def _get_plan(db: AsyncSession, tenant_id: uuid.UUID, plan_id: uuid.UUID) -> MrMembershipPlan:
    row = (
        await db.execute(
            select(MrMembershipPlan).where(
                MrMembershipPlan.id == plan_id,
                MrMembershipPlan.tenant_id == tenant_id,
            )
        )
    ).scalar_one_or_none()
    if not row:
        raise NotFoundException("Membership plan not found")
    return row


# ── Tiers & catalog ──────────────────────────────────────────────────────────


async def _get_tier(db: AsyncSession, tenant_id: uuid.UUID, tier_id: uuid.UUID) -> MrLoyaltyTier:
    row = (
        await db.execute(
            select(MrLoyaltyTier).where(
                MrLoyaltyTier.id == tier_id,
                MrLoyaltyTier.tenant_id == tenant_id,
            )
        )
    ).scalar_one_or_none()
    if not row:
        raise NotFoundException("Tier not found")
    return row


async def update_tier(
    db: AsyncSession, tenant_id: uuid.UUID, tier_id: uuid.UUID, data
) -> MrLoyaltyTier:
    row = await _get_tier(db, tenant_id, tier_id)
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(row, field, value)
    await db.commit()
    await db.refresh(row)
    return row


async def list_catalog(db: AsyncSession, tenant_id: uuid.UUID) -> list[MrRewardCatalog]:
    q = (
        select(MrRewardCatalog)
        .where(MrRewardCatalog.tenant_id == tenant_id)
        .order_by(MrRewardCatalog.points_cost)
    )
    return list((await db.execute(q)).scalars().all())


async def create_catalog_item(
    db: AsyncSession, tenant_id: uuid.UUID, data: CatalogItemCreate
) -> MrRewardCatalog:
    row = MrRewardCatalog(tenant_id=tenant_id, **data.model_dump())
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return row


# ── Landing (public) ─────────────────────────────────────────────────────────


async def get_landing_config(db: AsyncSession, tenant_id: uuid.UUID) -> dict[str, Any]:
    from app.modules.membership_rewards.landing import landing_urls

    cfg = await _ensure_landing_config(db, tenant_id)
    plans = await list_plans(db, tenant_id, active_only=True)
    tiers = await list_tiers(db, tenant_id)
    urls = await landing_urls(db, tenant_id)
    return {
        "title": cfg.title,
        "meta_description": cfg.meta_description,
        "hero": cfg.hero or {},
        "benefits": cfg.benefits or [],
        "cta_label": cfg.cta_label,
        "cta_href": cfg.cta_href,
        "published": cfg.published,
        "auto_generated": cfg.auto_generated,
        "public_url": urls.get("public_url"),
        "preview_path": urls.get("preview_path"),
        "booking_cta_url": urls.get("booking_cta_url"),
        "plans": plans,
        "tiers": [
            {
                "code": t.code,
                "name": t.name,
                "min_points_lifetime": t.min_points_lifetime,
                "benefits": t.benefits or [],
            }
            for t in tiers
        ],
    }


async def update_landing_config(
    db: AsyncSession, tenant_id: uuid.UUID, data: LandingConfigUpdate
) -> MrLandingConfig:
    cfg = await _ensure_landing_config(db, tenant_id)
    settings = await _get_or_create_settings(db, tenant_id)
    payload = data.model_dump(exclude_unset=True)
    content_fields = {"title", "meta_description", "hero", "benefits", "cta_label", "cta_href"}
    if content_fields & payload.keys():
        cfg.auto_generated = False
    was_published = cfg.published
    for k, v in payload.items():
        setattr(cfg, k, v)
    if was_published or data.published is True:
        cfg.published = True
        settings.landing_published = True
    elif data.published is False:
        settings.landing_published = False
    await db.commit()
    await db.refresh(cfg)
    return cfg


async def get_public_memberships_page(db: AsyncSession, tenant_slug: str) -> dict[str, Any]:
    tenant = (
        await db.execute(select(Tenant).where(Tenant.slug == tenant_slug))
    ).scalar_one_or_none()
    if not tenant:
        raise NotFoundException("Business not found")

    from app.modules.membership_rewards.entitlement import require_public_membership_rewards

    await require_public_membership_rewards(db, tenant.id)

    settings = await _get_or_create_settings(db, tenant.id)
    if not settings.landing_published:
        raise NotFoundException("Membership page is not published")

    cfg = await _ensure_landing_config(db, tenant.id)
    if not cfg.published:
        raise NotFoundException("Membership page is not published")

    plans = await list_plans(db, tenant.id, active_only=True)
    tiers = await list_tiers(db, tenant.id)
    from app.modules.booking.feedback import refer_url_for_slug
    from app.modules.membership_rewards.landing import (
        loyalty_public_url,
        memberships_public_url,
        rewards_portal_url,
    )

    return {
        "tenant_slug": tenant.slug,
        "tenant_name": tenant.name,
        "title": cfg.title,
        "meta_description": cfg.meta_description,
        "hero": cfg.hero or {},
        "benefits": cfg.benefits or [],
        "cta_label": cfg.cta_label,
        "cta_href": cfg.cta_href,
        "refer_win_url": refer_url_for_slug(tenant.slug),
        "memberships_url": memberships_public_url(tenant.slug),
        "loyalty_url": loyalty_public_url(tenant.slug),
        "rewards_portal_url": rewards_portal_url(tenant.slug),
        "tiers": [
            {
                "code": t.code,
                "name": t.name,
                "min_points_lifetime": t.min_points_lifetime,
                "benefits": t.benefits or [],
            }
            for t in tiers
        ],
        "plans": [
            {
                "id": str(p.id),
                "name": p.name,
                "description": p.description,
                "billing_cycle": p.billing_cycle,
                "price_pence": p.price_pence,
                "discount_percent": p.discount_percent,
                "included_services": p.included_services or [],
            }
            for p in plans
        ],
    }


async def publish_landing(db: AsyncSession, tenant_id: uuid.UUID) -> MrLandingConfig:
    plans = await list_plans(db, tenant_id, active_only=True)
    if not plans:
        raise BadRequestException("Add at least one active membership plan before publishing.")
    cfg = await _ensure_landing_config(db, tenant_id)
    settings = await _get_or_create_settings(db, tenant_id)
    cfg.published = True
    settings.landing_published = True
    await db.commit()
    await db.refresh(cfg)
    return cfg


async def regenerate_landing(db: AsyncSession, tenant_id: uuid.UUID) -> MrLandingConfig:
    from app.modules.membership_rewards.landing import sync_landing_from_plans

    return await sync_landing_from_plans(db, tenant_id, force=True, auto_publish=False)


async def submit_membership_interest(
    db: AsyncSession,
    tenant_slug: str,
    *,
    first_name: str,
    last_name: str | None,
    email: str | None,
    phone: str | None,
    message: str | None,
    plan_id: uuid.UUID | None,
    ip_address: str | None,
) -> None:
    """Capture membership interest as a lead (public memberships page)."""
    from app.modules.leads.schemas import LeadCreate
    from app.modules.leads import service as leads_service

    tenant = (
        await db.execute(select(Tenant).where(Tenant.slug == tenant_slug, Tenant.is_active == True))  # noqa: E712
    ).scalar_one_or_none()
    if not tenant:
        raise NotFoundException("Business not found")

    from app.modules.membership_rewards.entitlement import require_public_membership_rewards

    await require_public_membership_rewards(db, tenant.id)

    settings = await _get_or_create_settings(db, tenant.id)
    if not settings.landing_published:
        raise NotFoundException("Membership page is not published")

    plan_name = None
    if plan_id:
        plan = (
            await db.execute(
                select(MrMembershipPlan).where(
                    MrMembershipPlan.id == plan_id,
                    MrMembershipPlan.tenant_id == tenant.id,
                    MrMembershipPlan.is_active.is_(True),
                )
            )
        ).scalar_one_or_none()
        if plan:
            plan_name = plan.name

    body = message or ""
    if plan_name:
        body = f"Interested in plan: {plan_name}\n{body}".strip()

    data = LeadCreate(
        first_name=first_name,
        last_name=last_name,
        email=email,
        phone=phone,
        message=body or "Membership enquiry from public page",
        service_needed=plan_name or "membership",
        source="memberships_page",
    )
    await leads_service.create_lead_public(db=db, tenant=tenant, data=data, ip_address=ip_address)


async def submit_loyalty_enrollment(
    db: AsyncSession,
    tenant_slug: str,
    *,
    name: str,
    email: str | None,
    phone: str | None,
    tier_code: str,
    ip_address: str | None,
) -> dict[str, Any]:
    """Enroll a customer in the loyalty program from the public memberships page."""
    from app.modules.booking.crm_link import _split_name, resolve_customer_for_booking
    from app.modules.leads.schemas import LeadCreate
    from app.modules.leads import service as leads_service
    from app.modules.membership_rewards.customer_auth.provisioning import ensure_portal_account
    from app.modules.membership_rewards.services.customer_loyalty_service import (
        contact_already_enrolled_in_loyalty,
        is_loyalty_program_enrolled,
    )

    tier = (tier_code or "").strip().lower()
    email_norm = (email or "").strip()
    phone_norm = (phone or "").strip()

    if not email_norm and not phone_norm:
        raise BadRequestException("Email or phone is required")
    if not email_norm:
        raise BadRequestException(
            "Email is required to create your rewards wallet and receive your login link."
        )

    tenant = (
        await db.execute(select(Tenant).where(Tenant.slug == tenant_slug, Tenant.is_active == True))  # noqa: E712
    ).scalar_one_or_none()
    if not tenant:
        raise NotFoundException("Business not found")

    from app.modules.membership_rewards.entitlement import require_public_membership_rewards

    await require_public_membership_rewards(db, tenant.id)

    settings = await _get_or_create_settings(db, tenant.id)
    if not settings.landing_published:
        raise NotFoundException("Membership page is not published")

    tiers = await list_tiers(db, tenant.id)
    tier_row = next((t for t in tiers if t.code == tier), None)
    if not tier_row:
        raise BadRequestException(f"Invalid tier: {tier_code}")

    if await contact_already_enrolled_in_loyalty(
        db, tenant.id, email=email_norm, phone=phone_norm
    ):
        raise BadRequestException(
            "This email or phone number is already registered in our loyalty program."
        )

    first_name, last_name = _split_name(name)
    customer_id = await resolve_customer_for_booking(
        db,
        tenant.id,
        customer_id=None,
        customer_name=name,
        customer_email=email_norm,
        customer_phone=phone_norm or None,
        channel="loyalty_program",
    )
    if not customer_id:
        raise BadRequestException("Could not create customer record")

    if await is_loyalty_program_enrolled(db, tenant.id, customer_id):
        raise BadRequestException(
            "This email or phone number is already registered in our loyalty program."
        )

    loyalty = await get_or_create_loyalty(db, tenant.id, customer_id)
    loyalty.tier_code = tier
    loyalty.tier_updated_at = datetime.now(timezone.utc)

    tier_name = tier_row.name

    signup_bonus = await membership_signup_bonus_points(db, tenant.id)
    awarded_bonus = False
    points_balance = 0
    if signup_bonus > 0 and not await has_loyalty_signup_bonus(db, tenant.id, customer_id):
        entry = await earn_points(
            db,
            tenant.id,
            customer_id,
            signup_bonus,
            source="membership",
            description="Welcome bonus — loyalty program signup",
            reference_type="loyalty_signup",
        )
        points_balance = entry.balance_after
        awarded_bonus = True
    else:
        await db.commit()
        loyalty_row = await get_customer_loyalty(db, tenant.id, customer_id)
        points_balance = loyalty_row.points_balance

    portal = await ensure_portal_account(
        db,
        tenant_id=tenant.id,
        customer_id=customer_id,
        email=email_norm,
        customer_name=first_name,
        tier_code=tier,
        source="loyalty_enroll",
        award_signup_bonus=False,
    )

    lead_data = LeadCreate(
        first_name=first_name,
        last_name=last_name,
        email=email_norm,
        phone=phone_norm or None,
        message=f"Joined loyalty program — selected {tier_name} tier",
        service_needed="loyalty",
        source="memberships_loyalty",
    )
    try:
        await leads_service.create_lead_public(
            db=db, tenant=tenant, data=lead_data, ip_address=ip_address
        )
    except Exception:  # noqa: BLE001
        logger.exception(
            "Lead capture failed after loyalty enroll tenant=%s customer=%s",
            tenant.id,
            customer_id,
        )

    return {
        "message": "Welcome! You're enrolled in our loyalty program.",
        "tier_code": tier,
        "tier_name": tier_name,
        "signup_bonus_points": signup_bonus if awarded_bonus else 0,
        "points_balance": points_balance,
        "portal_account_created": portal.get("credentials_created", False),
        "rewards_email_sent": portal.get("magic_link_sent", False),
    }


# ── Subscriptions (tenant-level customer plans) ──────────────────────────────


def _period_end(start: date, billing_cycle: str) -> date:
    if billing_cycle == "weekly":
        return start + timedelta(days=7)
    if billing_cycle == "quarterly":
        return start + relativedelta(months=3)
    if billing_cycle == "yearly":
        return start + relativedelta(years=1)
    return start + relativedelta(months=1)


async def list_subscriptions(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    *,
    customer_id: uuid.UUID | None = None,
    status: str | None = None,
) -> list[MrCustomerSubscription]:
    q = select(MrCustomerSubscription).where(MrCustomerSubscription.tenant_id == tenant_id)
    if customer_id:
        q = q.where(MrCustomerSubscription.customer_id == customer_id)
    if status:
        q = q.where(MrCustomerSubscription.status == status)
    q = q.order_by(MrCustomerSubscription.created_at.desc())
    return list((await db.execute(q)).scalars().all())


async def get_subscription(
    db: AsyncSession, tenant_id: uuid.UUID, subscription_id: uuid.UUID
) -> MrCustomerSubscription:
    row = (
        await db.execute(
            select(MrCustomerSubscription).where(
                MrCustomerSubscription.id == subscription_id,
                MrCustomerSubscription.tenant_id == tenant_id,
            )
        )
    ).scalar_one_or_none()
    if not row:
        raise NotFoundException("Subscription not found")
    return row


async def create_subscription(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    *,
    customer_id: uuid.UUID,
    plan_id: uuid.UUID,
    started_at: date | None = None,
) -> MrCustomerSubscription:
    cust = (
        await db.execute(
            select(Customer).where(Customer.id == customer_id, Customer.tenant_id == tenant_id)
        )
    ).scalar_one_or_none()
    if not cust:
        raise NotFoundException("Customer not found")
    plan = await _get_plan(db, tenant_id, plan_id)
    if not plan.is_active:
        raise BadRequestException("Plan is not active")

    active = (
        await db.execute(
            select(MrCustomerSubscription).where(
                MrCustomerSubscription.tenant_id == tenant_id,
                MrCustomerSubscription.customer_id == customer_id,
                MrCustomerSubscription.status == "active",
            )
        )
    ).scalar_one_or_none()
    if active:
        raise BadRequestException("Customer already has an active membership subscription")

    start = started_at or date.today()
    sub = MrCustomerSubscription(
        tenant_id=tenant_id,
        customer_id=customer_id,
        plan_id=plan_id,
        status="active",
        started_at=start,
        current_period_end=_period_end(start, plan.billing_cycle),
    )
    db.add(sub)
    await db.commit()
    await db.refresh(sub)

    from app.modules.membership_rewards.hooks import on_subscription_created

    await on_subscription_created(db, tenant_id=tenant_id, subscription_id=sub.id)
    return sub


async def cancel_subscription(
    db: AsyncSession, tenant_id: uuid.UUID, subscription_id: uuid.UUID
) -> MrCustomerSubscription:
    sub = await get_subscription(db, tenant_id, subscription_id)
    if sub.status == "canceled":
        return sub
    sub.status = "canceled"
    sub.canceled_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(sub)
    return sub


# ── Add-on checkout (tenant pays for Membership & Rewards SKU) ─────────────


async def create_addon_checkout(
    db: AsyncSession,
    tenant: Tenant,
    *,
    success_url: str,
    cancel_url: str,
) -> str:
    if not settings.STRIPE_PRICE_MEMBERSHIP_REWARDS:
        raise BadRequestException(
            "Membership & Rewards add-on is not configured for billing yet. Contact support."
        )

    from app.modules.billing.models import Subscription

    sub = (
        await db.execute(select(Subscription).where(Subscription.tenant_id == tenant.id))
    ).scalar_one_or_none()

    from app.adapters import get_payment_adapter

    adapter = get_payment_adapter()
    if sub and sub.stripe_customer_id:
        customer_id = sub.stripe_customer_id
    else:
        customer_id = await adapter.create_customer(
            email=tenant.email or "",
            name=tenant.name,
            metadata={"tenant_id": str(tenant.id)},
        )

    import stripe

    stripe.api_key = settings.STRIPE_SECRET_KEY
    session = stripe.checkout.Session.create(
        customer=customer_id,
        payment_method_types=["card"],
        line_items=[{"price": settings.STRIPE_PRICE_MEMBERSHIP_REWARDS, "quantity": 1}],
        mode="subscription",
        success_url=success_url,
        cancel_url=cancel_url,
        metadata={"tenant_id": str(tenant.id), "feature_code": FEATURE_MEMBERSHIP_REWARDS},
    )
    return session.url


async def activate_from_checkout_metadata(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    stripe_subscription_item_id: str | None = None,
    checkout_session_id: str | None = None,
) -> None:
    row = (
        await db.execute(
            select(TenantAddon).where(
                TenantAddon.tenant_id == tenant_id,
                TenantAddon.feature_code == FEATURE_MEMBERSHIP_REWARDS,
            )
        )
    ).scalar_one_or_none()
    now = datetime.now(timezone.utc)
    if row:
        row.status = "active"
        row.stripe_subscription_item_id = stripe_subscription_item_id or row.stripe_subscription_item_id
        row.stripe_checkout_session_id = checkout_session_id or row.stripe_checkout_session_id
        row.granted_at = now
        row.expires_at = None
    else:
        db.add(
            TenantAddon(
                id=uuid.uuid4(),
                tenant_id=tenant_id,
                feature_code=FEATURE_MEMBERSHIP_REWARDS,
                status="active",
                stripe_subscription_item_id=stripe_subscription_item_id,
                stripe_checkout_session_id=checkout_session_id,
                granted_at=now,
            )
        )
    trial = (
        await db.execute(select(MrTrialReminders).where(MrTrialReminders.tenant_id == tenant_id))
    ).scalar_one_or_none()
    if trial and not trial.converted_at:
        trial.converted_at = now
    await bootstrap_tenant(db, tenant_id)
    await db.commit()


# ── Dashboard summary ────────────────────────────────────────────────────────


async def get_dashboard(db: AsyncSession, tenant_id: uuid.UUID) -> dict[str, Any]:
    active_subs = (
        await db.execute(
            select(func.count())
            .select_from(MrCustomerSubscription)
            .where(
                MrCustomerSubscription.tenant_id == tenant_id,
                MrCustomerSubscription.status == "active",
            )
        )
    ).scalar() or 0
    members_with_points = (
        await db.execute(
            select(func.count())
            .select_from(MrCustomerLoyalty)
            .where(
                MrCustomerLoyalty.tenant_id == tenant_id,
                MrCustomerLoyalty.points_balance > 0,
            )
        )
    ).scalar() or 0
    points_issued = (
        await db.execute(
            select(func.coalesce(func.sum(MrPointsLedger.amount), 0)).where(
                MrPointsLedger.tenant_id == tenant_id,
                MrPointsLedger.amount > 0,
            )
        )
    ).scalar() or 0
    redemptions = (
        await db.execute(
            select(func.count())
            .select_from(MrRewardRedemption)
            .where(MrRewardRedemption.tenant_id == tenant_id)
        )
    ).scalar() or 0
    plan_count = (
        await db.execute(
            select(func.count())
            .select_from(MrMembershipPlan)
            .where(MrMembershipPlan.tenant_id == tenant_id, MrMembershipPlan.is_active.is_(True))
        )
    ).scalar() or 0
    settings_row = await _get_or_create_settings(db, tenant_id)
    return {
        "active_subscriptions": int(active_subs),
        "members_with_points": int(members_with_points),
        "points_issued_lifetime": int(points_issued),
        "redemptions_count": int(redemptions),
        "active_plans": int(plan_count),
        "landing_published": settings_row.landing_published,
    }


async def get_analytics(db: AsyncSession, tenant_id: uuid.UUID) -> dict[str, Any]:
    from app.modules.membership_rewards.services.analytics import get_analytics as _get_analytics

    return await _get_analytics(db, tenant_id)


async def list_loyalty_customers(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    *,
    search: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> dict[str, Any]:
    from app.modules.membership_rewards.services.analytics import list_loyalty_customers as _list

    return await _list(db, tenant_id, search=search, limit=limit, offset=offset)


async def list_redemptions(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    *,
    status: str | None = None,
    limit: int = 50,
) -> list[dict[str, Any]]:
    from app.modules.membership_rewards.services.analytics import list_redemptions as _list

    return await _list(db, tenant_id, status=status, limit=limit)
