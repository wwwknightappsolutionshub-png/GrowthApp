"""Customer loyalty portal reads and writes."""

from __future__ import annotations

import base64
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequestException, NotFoundException
from app.modules.crm.models import Customer
from app.modules.membership_rewards.customer_auth.credentials import get_credentials
from app.modules.membership_rewards.customer_auth.qr_tokens import issue_qr_token
from app.modules.membership_rewards.engines.tier_engine import compute_tier_progress, list_tiers
from app.modules.membership_rewards.entitlement import tenant_has_membership_rewards
from app.modules.membership_rewards.landing import rewards_portal_url
from app.modules.membership_rewards.models import (
    MrCustomerPushSubscription,
    MrPointsLedger,
    MrRewardCatalog,
    MrRewardRedemption,
)
from app.modules.membership_rewards.services.customer_loyalty_service import (
    get_customer_loyalty,
    list_ledger,
)
from app.modules.membership_rewards.services.customer_preferences_service import (
    get_or_create_preferences,
    preferences_payload,
)
from app.modules.tenants.models import Tenant
from app.modules.tenants.site_service import qr_png_bytes


async def resolve_tenant_by_slug(db: AsyncSession, tenant_slug: str) -> Tenant:
    tenant = (
        await db.execute(select(Tenant).where(Tenant.slug == tenant_slug, Tenant.is_active.is_(True)))
    ).scalar_one_or_none()
    if not tenant:
        raise NotFoundException("Business not found")
    return tenant


async def find_customer_by_email(
    db: AsyncSession, tenant_id: uuid.UUID, email: str
) -> Customer | None:
    normalized = email.lower().strip()
    if not normalized:
        return None
    return (
        await db.execute(
            select(Customer).where(
                Customer.tenant_id == tenant_id,
                func.lower(Customer.email) == normalized,
                Customer.deleted_at.is_(None),
            )
        )
    ).scalar_one_or_none()


async def get_portal_branding(db: AsyncSession, tenant_slug: str) -> dict[str, Any]:
    tenant = await resolve_tenant_by_slug(db, tenant_slug)
    has_rewards = await tenant_has_membership_rewards(db, tenant.id)
    return {
        "tenant_slug": tenant.slug,
        "tenant_name": tenant.name,
        "logo_url": tenant.logo_url,
        "primary_color": tenant.primary_color or "#2563EB",
        "rewards_portal_url": rewards_portal_url(tenant.slug),
        "loyalty_enabled": has_rewards,
    }


async def build_customer_profile(
    db: AsyncSession, tenant: Tenant, customer: Customer
) -> dict[str, Any]:
    loyalty = await get_customer_loyalty(db, tenant.id, customer.id)
    tiers = await list_tiers(db, tenant.id)
    tier = next((t for t in tiers if t.code == loyalty.tier_code), None)
    creds = await get_credentials(db, tenant.id, customer.id)
    progress = compute_tier_progress(tiers, loyalty.points_lifetime, loyalty.tier_code)

    ledger_rows = await list_ledger(db, tenant.id, customer.id, limit=500)
    points_redeemed = sum(abs(row.amount) for row in ledger_rows if row.amount < 0)
    points_earned = sum(row.amount for row in ledger_rows if row.amount > 0)

    now = datetime.now(timezone.utc)
    exp_cutoff = now + timedelta(days=30)
    points_expiring_soon = 0
    for row in ledger_rows:
        if row.amount <= 0 or not row.expires_at:
            continue
        expires = row.expires_at
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=timezone.utc)
        if now < expires <= exp_cutoff:
            points_expiring_soon += row.amount

    push_count = int(
        (
            await db.execute(
                select(func.count())
                .select_from(MrCustomerPushSubscription)
                .where(
                    MrCustomerPushSubscription.tenant_id == tenant.id,
                    MrCustomerPushSubscription.customer_id == customer.id,
                )
            )
        ).scalar()
        or 0
    )

    pending_redemptions = int(
        (
            await db.execute(
                select(func.count())
                .select_from(MrRewardRedemption)
                .where(
                    MrRewardRedemption.tenant_id == tenant.id,
                    MrRewardRedemption.customer_id == customer.id,
                    MrRewardRedemption.status == "pending",
                )
            )
        ).scalar()
        or 0
    )

    prefs = await get_or_create_preferences(db, tenant.id, customer.id)
    pref_data = preferences_payload(prefs, customer)

    return {
        "customer_id": customer.id,
        "first_name": customer.first_name,
        "last_name": customer.last_name,
        "email": customer.email,
        "phone": customer.phone,
        "points_balance": loyalty.points_balance,
        "points_lifetime": loyalty.points_lifetime,
        "points_earned": points_earned,
        "points_redeemed": points_redeemed,
        "points_expiring_soon": points_expiring_soon,
        "pending_redemptions": pending_redemptions,
        "tier_code": loyalty.tier_code,
        "tier_name": tier.name if tier else loyalty.tier_code.replace("_", " ").title(),
        "tier_benefits": tier.benefits if tier else [],
        "next_tier_code": progress["next_tier_code"],
        "next_tier_name": progress["next_tier_name"],
        "points_to_next_tier": progress["points_to_next_tier"],
        "tier_progress_percent": progress["tier_progress_percent"],
        "must_change_password": bool(creds and creds.must_change_password),
        "push_notifications_enabled": push_count > 0,
        **pref_data,
        "tenant_slug": tenant.slug,
        "tenant_name": tenant.name,
    }


async def list_active_rewards(db: AsyncSession, tenant_id: uuid.UUID) -> list[MrRewardCatalog]:
    q = (
        select(MrRewardCatalog)
        .where(
            MrRewardCatalog.tenant_id == tenant_id,
            MrRewardCatalog.is_active.is_(True),
        )
        .order_by(MrRewardCatalog.points_cost)
    )
    return list((await db.execute(q)).scalars().all())


async def get_customer_qr_payload(
    db: AsyncSession, tenant_id: uuid.UUID, customer_id: uuid.UUID
) -> dict[str, Any]:
    raw, expires_at = await issue_qr_token(db, tenant_id, customer_id)
    payload = f"cf-loyalty:{tenant_id}:{customer_id}:{raw}"
    png = qr_png_bytes(payload)
    return {
        "token": raw,
        "expires_at": expires_at.isoformat(),
        "qr_data_url": f"data:image/png;base64,{base64.b64encode(png).decode('ascii')}",
        "payload": payload,
    }


async def upsert_customer_push_subscription(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    customer_id: uuid.UUID,
    endpoint: str,
    p256dh: str,
    auth: str,
    user_agent: str | None = None,
) -> MrCustomerPushSubscription:
    endpoint = endpoint.strip()
    if not endpoint:
        raise BadRequestException("Push endpoint is required")

    existing = (
        await db.execute(
            select(MrCustomerPushSubscription).where(
                MrCustomerPushSubscription.tenant_id == tenant_id,
                MrCustomerPushSubscription.customer_id == customer_id,
                MrCustomerPushSubscription.endpoint == endpoint,
            )
        )
    ).scalar_one_or_none()

    if existing:
        existing.p256dh = p256dh
        existing.auth = auth
        existing.user_agent = user_agent
        await db.commit()
        await db.refresh(existing)
        return existing

    row = MrCustomerPushSubscription(
        tenant_id=tenant_id,
        customer_id=customer_id,
        endpoint=endpoint,
        p256dh=p256dh,
        auth=auth,
        user_agent=user_agent,
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return row


async def list_pending_redemptions(
    db: AsyncSession, tenant_id: uuid.UUID, customer_id: uuid.UUID
) -> list[dict[str, Any]]:
    rows = (
        await db.execute(
            select(MrRewardRedemption, MrRewardCatalog)
            .join(MrRewardCatalog, MrRewardCatalog.id == MrRewardRedemption.catalog_item_id)
            .where(
                MrRewardRedemption.tenant_id == tenant_id,
                MrRewardRedemption.customer_id == customer_id,
                MrRewardRedemption.status == "pending",
            )
            .order_by(MrRewardRedemption.created_at.desc())
        )
    ).all()
    return [
        {
            "id": redemption.id,
            "reward_name": catalog.name,
            "points_spent": redemption.points_spent,
            "fulfillment_code": redemption.fulfillment_code or "",
            "code_expires_at": redemption.code_expires_at,
            "status": redemption.status,
        }
        for redemption, catalog in rows
    ]


async def delete_customer_push_subscriptions(
    db: AsyncSession, tenant_id: uuid.UUID, customer_id: uuid.UUID
) -> int:
    from sqlalchemy import delete

    result = await db.execute(
        delete(MrCustomerPushSubscription).where(
            MrCustomerPushSubscription.tenant_id == tenant_id,
            MrCustomerPushSubscription.customer_id == customer_id,
        )
    )
    await db.commit()
    return int(result.rowcount or 0)
