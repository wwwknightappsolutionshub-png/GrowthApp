"""Customer loyalty portal reads and writes."""

from __future__ import annotations

import base64
import uuid
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequestException, NotFoundException
from app.modules.crm.models import Customer
from app.modules.membership_rewards.customer_auth.credentials import get_credentials
from app.modules.membership_rewards.customer_auth.qr_tokens import issue_qr_token
from app.modules.membership_rewards.engines.tier_engine import list_tiers
from app.modules.membership_rewards.entitlement import tenant_has_membership_rewards
from app.modules.membership_rewards.landing import rewards_portal_url
from app.modules.membership_rewards.models import MrCustomerPushSubscription, MrRewardCatalog
from app.modules.membership_rewards.services.customer_loyalty_service import (
    get_customer_loyalty,
    list_ledger,
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
    return {
        "customer_id": customer.id,
        "first_name": customer.first_name,
        "last_name": customer.last_name,
        "email": customer.email,
        "phone": customer.phone,
        "points_balance": loyalty.points_balance,
        "points_lifetime": loyalty.points_lifetime,
        "tier_code": loyalty.tier_code,
        "tier_name": tier.name if tier else loyalty.tier_code.replace("_", " ").title(),
        "tier_benefits": tier.benefits if tier else [],
        "must_change_password": bool(creds and creds.must_change_password),
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
