"""Freelancer-managed clients (shadow tenants).

Each managed client is a Tenant row owned by the freelancer:
  * tenants.owner_user_id   = freelancer's User.id
  * tenants.is_managed_client = True
  * a TenantMember row makes the freelancer the 'owner' of that client tenant

This lets the freelancer "context-switch" into any client and use every
existing tenant-scoped tool (CRM, AI Social, Automations, Outreach, etc.)
with zero new parallel infrastructure.

Endpoints
---------
GET    /api/v1/freelancer/clients          → list my managed clients
POST   /api/v1/freelancer/clients          → create a new managed client
GET    /api/v1/freelancer/clients/{id}     → fetch one
PATCH  /api/v1/freelancer/clients/{id}     → update name/social handles/etc.
DELETE /api/v1/freelancer/clients/{id}     → soft-delete (deactivate)
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import and_, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import log_action
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.modules.admin.tool_config import BusinessCategoryConfig, FREELANCER_TOOL_HREFS
from app.modules.auth.models import User
from app.modules.crm.models import Customer
from app.modules.tenants.models import Tenant, TenantMember
from app.modules.tenants.service import _slugify

router = APIRouter(
    prefix="/api/v1/freelancer/clients",
    tags=["Freelancer — Clients"],
)


# ── Schemas ─────────────────────────────────────────────────────────────────

class SocialHandles(BaseModel):
    instagram: str | None = None
    facebook: str | None = None
    tiktok: str | None = None
    twitter: str | None = None
    linkedin: str | None = None
    youtube: str | None = None
    google_business: str | None = None


class FreelancerClientCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    contact_name: str | None = Field(default=None, max_length=255)
    business_type: str | None = Field(default="other", max_length=100)
    postcode: str | None = Field(default=None, max_length=10)
    email: str | None = None
    phone: str | None = None
    website_url: str | None = None
    social_handles: SocialHandles = Field(default_factory=SocialHandles)
    notes: str | None = None


class FreelancerClientUpdate(BaseModel):
    name: str | None = None
    contact_name: str | None = None
    business_type: str | None = None
    postcode: str | None = None
    email: str | None = None
    phone: str | None = None
    website_url: str | None = None
    social_handles: SocialHandles | None = None
    is_active: bool | None = None


class FreelancerClientOut(BaseModel):
    id: str
    slug: str
    name: str
    business_type: str | None
    postcode: str | None
    email: str | None
    phone: str | None
    website_url: str | None
    is_active: bool
    social_handles: dict[str, Any]
    created_at: datetime
    updated_at: datetime


class FreelancerModuleVisibilityOut(BaseModel):
    enabled_tools: list[str]


# ── Helpers ─────────────────────────────────────────────────────────────────

def _ensure_freelancer(user: User) -> None:
    if user.user_type != "freelancer":
        raise HTTPException(
            403, "Only freelancers can manage clients. Please upgrade your account type."
        )


async def _get_owned_client(
    db: AsyncSession, *, freelancer: User, client_id: uuid.UUID
) -> Tenant:
    row = (
        await db.execute(
            select(Tenant).where(
                and_(
                    Tenant.id == client_id,
                    Tenant.owner_user_id == freelancer.id,
                    Tenant.is_managed_client == True,  # noqa: E712
                )
            )
        )
    ).scalar_one_or_none()
    if row is None:
        raise HTTPException(404, "Client not found in your portfolio.")
    return row


def _serialize(t: Tenant) -> FreelancerClientOut:
    handles = t.social_handles if isinstance(t.social_handles, dict) else {}
    return FreelancerClientOut(
        id=str(t.id),
        slug=t.slug,
        name=t.name,
        business_type=t.business_type,
        postcode=t.postcode,
        email=t.email,
        phone=t.phone,
        website_url=t.website_url,
        is_active=t.is_active,
        social_handles=handles,
        created_at=t.created_at,
        updated_at=t.updated_at,
    )


@router.get("/module-visibility", response_model=FreelancerModuleVisibilityOut)
async def get_module_visibility(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> FreelancerModuleVisibilityOut:
    _ensure_freelancer(current_user)
    row = (
        await db.execute(
            select(BusinessCategoryConfig).where(BusinessCategoryConfig.category == "freelancer")
        )
    ).scalar_one_or_none()
    return FreelancerModuleVisibilityOut(
        enabled_tools=list(row.enabled_tools) if row else list(FREELANCER_TOOL_HREFS)
    )


async def _unique_slug(db: AsyncSession, base: str, freelancer_id: uuid.UUID) -> str:
    """Ensure slug is unique across all tenants (Tenant.slug is unique)."""
    slug = _slugify(base) or f"client-{uuid.uuid4().hex[:8]}"
    i = 0
    while True:
        candidate = slug if i == 0 else f"{slug}-{i}"
        exists = (
            await db.execute(select(Tenant.id).where(Tenant.slug == candidate))
        ).scalar_one_or_none()
        if exists is None:
            return candidate
        i += 1
        if i > 99:
            return f"{slug}-{uuid.uuid4().hex[:6]}"


def _split_contact_name(contact_name: str | None, fallback_name: str) -> tuple[str, str | None]:
    raw = (contact_name or "").strip()
    if not raw:
        return fallback_name.strip() or "Client", None
    parts = raw.split(maxsplit=1)
    return parts[0], parts[1] if len(parts) > 1 else None


async def _upsert_client_crm_customer(
    db: AsyncSession,
    *,
    tenant: Tenant,
    contact_name: str | None,
) -> None:
    """Keep each managed client represented as a CRM contact for upsell/follow-up."""
    first_name, last_name = _split_contact_name(contact_name, tenant.name)
    marker = f"managed_client:{tenant.id}"
    existing = (
        await db.execute(
            select(Customer).where(
                Customer.tenant_id == tenant.id,
                Customer.source == "freelancer_client",
                Customer.special_comments == marker,
                Customer.deleted_at.is_(None),
            )
        )
    ).scalar_one_or_none()

    customer = existing or Customer(
        id=uuid.uuid4(),
        tenant_id=tenant.id,
        source="freelancer_client",
        special_comments=marker,
    )
    customer.first_name = first_name
    customer.last_name = last_name
    customer.email = tenant.email
    customer.phone = tenant.phone
    customer.postcode = tenant.postcode or None
    customer.notes = (
        f"Managed freelancer client: {tenant.name}. "
        "Use this CRM record for service management, follow-up, and upsell opportunities."
    )
    db.add(customer)


# ── Routes ──────────────────────────────────────────────────────────────────

@router.get("", response_model=list[FreelancerClientOut])
async def list_clients(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    include_inactive: bool = False,
):
    _ensure_freelancer(current_user)
    stmt = select(Tenant).where(
        and_(
            Tenant.owner_user_id == current_user.id,
            Tenant.is_managed_client == True,  # noqa: E712
        )
    )
    if not include_inactive:
        stmt = stmt.where(Tenant.is_active == True)  # noqa: E712
    rows = (await db.execute(stmt.order_by(Tenant.created_at.desc()))).scalars().all()
    return [_serialize(r) for r in rows]


@router.post("", response_model=FreelancerClientOut, status_code=201)
async def create_client(
    body: FreelancerClientCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    _ensure_freelancer(current_user)

    slug = await _unique_slug(db, body.name, current_user.id)
    # NB: Tenant.postcode is NOT NULL on the model. Managed clients may not
    # have one yet — default to empty string so it can be filled in later.
    postcode = (body.postcode or "").upper().strip() or ""
    tenant = Tenant(
        id=uuid.uuid4(),
        slug=slug,
        name=body.name,
        business_type=body.business_type or "other",
        postcode=postcode,
        email=body.email,
        phone=body.phone,
        website_url=body.website_url,
        owner_user_id=current_user.id,
        is_managed_client=True,
        social_handles=body.social_handles.model_dump(exclude_none=True),
    )
    db.add(tenant)
    await db.flush()

    db.add(
        TenantMember(
            id=uuid.uuid4(),
            tenant_id=tenant.id,
            user_id=current_user.id,
            role="owner",
            joined_at=datetime.now(timezone.utc),
        )
    )
    await _upsert_client_crm_customer(db, tenant=tenant, contact_name=body.contact_name)
    await log_action(
        db,
        action="freelancer.client.created",
        resource="tenant",
        resource_id=tenant.id,
        user_id=current_user.id,
        tenant_id=tenant.id,
        metadata={"client_name": tenant.name, "social_handles": tenant.social_handles},
    )
    await db.commit()
    await db.refresh(tenant)
    if current_user.membership_rewards_opt_in:
        try:
            from app.modules.membership_rewards.hooks import on_tenant_signup

            await on_tenant_signup(db, tenant.id)
        except Exception:  # noqa: BLE001
            pass
    return _serialize(tenant)


@router.get("/{client_id}", response_model=FreelancerClientOut)
async def get_client(
    client_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    _ensure_freelancer(current_user)
    return _serialize(await _get_owned_client(db, freelancer=current_user, client_id=client_id))


@router.patch("/{client_id}", response_model=FreelancerClientOut)
async def update_client(
    client_id: uuid.UUID,
    body: FreelancerClientUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    _ensure_freelancer(current_user)
    tenant = await _get_owned_client(db, freelancer=current_user, client_id=client_id)

    if body.name is not None:
        tenant.name = body.name
    if body.business_type is not None:
        tenant.business_type = body.business_type
    if body.postcode is not None:
        tenant.postcode = body.postcode.upper() or None
    if body.email is not None:
        tenant.email = body.email
    if body.phone is not None:
        tenant.phone = body.phone
    if body.website_url is not None:
        tenant.website_url = body.website_url
    if body.is_active is not None:
        tenant.is_active = body.is_active
    if body.social_handles is not None:
        tenant.social_handles = body.social_handles.model_dump(exclude_none=True)

    db.add(tenant)
    if body.contact_name is not None or body.email is not None or body.phone is not None or body.postcode is not None or body.name is not None:
        await _upsert_client_crm_customer(db, tenant=tenant, contact_name=body.contact_name)
    await log_action(
        db,
        action="freelancer.client.updated",
        resource="tenant",
        resource_id=tenant.id,
        user_id=current_user.id,
        tenant_id=tenant.id,
        metadata=body.model_dump(exclude_none=True),
    )
    await db.commit()
    await db.refresh(tenant)
    return _serialize(tenant)


@router.delete("/{client_id}", status_code=204)
async def delete_client(
    client_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Soft-delete by setting is_active=False. Keeps historical data intact."""
    _ensure_freelancer(current_user)
    tenant = await _get_owned_client(db, freelancer=current_user, client_id=client_id)
    tenant.is_active = False
    db.add(tenant)
    await log_action(
        db,
        action="freelancer.client.deactivated",
        resource="tenant",
        resource_id=tenant.id,
        user_id=current_user.id,
        tenant_id=tenant.id,
    )
    await db.commit()


# ── Portfolio summary (for dashboard pie charts) ────────────────────────────

class PortfolioSummary(BaseModel):
    total_clients: int
    active_clients: int
    by_business_type: dict[str, int]
    by_social_platforms: dict[str, int]  # how many clients have each platform linked
    activity_per_client: list[dict[str, Any]]  # [{client_id, client_name, score}]


@router.get("/summary/portfolio", response_model=PortfolioSummary)
async def portfolio_summary(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Aggregate snapshot of the freelancer's portfolio for dashboard pie charts.

    Activity is approximated as (1 + number of social platforms linked) for each
    client until per-client activity tracking is wired through. This gives the
    pie chart something meaningful immediately and can be swapped for real
    activity counts later without API breakage.
    """
    _ensure_freelancer(current_user)
    rows = (
        await db.execute(
            select(Tenant).where(
                and_(
                    Tenant.owner_user_id == current_user.id,
                    Tenant.is_managed_client == True,  # noqa: E712
                )
            )
        )
    ).scalars().all()

    active = [r for r in rows if r.is_active]
    by_type: dict[str, int] = {}
    by_platform: dict[str, int] = {}
    activity: list[dict[str, Any]] = []

    for r in active:
        bt = (r.business_type or "other").lower()
        by_type[bt] = by_type.get(bt, 0) + 1
        handles = r.social_handles if isinstance(r.social_handles, dict) else {}
        linked = 0
        for k in ("instagram", "facebook", "tiktok", "twitter", "linkedin", "youtube", "google_business"):
            if handles.get(k):
                by_platform[k] = by_platform.get(k, 0) + 1
                linked += 1
        activity.append(
            {
                "client_id": str(r.id),
                "client_name": r.name,
                "score": 1 + linked,
            }
        )

    return PortfolioSummary(
        total_clients=len(rows),
        active_clients=len(active),
        by_business_type=by_type,
        by_social_platforms=by_platform,
        activity_per_client=activity,
    )
