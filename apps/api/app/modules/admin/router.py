"""
Super-admin endpoints. Every route in this module is gated by
`require_superadmin`, which both checks the `is_superadmin` flag and clears
the RLS GUC so platform-wide SELECTs return every tenant's rows.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import SuperAdmin
from app.modules.admin.deletion import (
    active_tenants_filter,
    active_users_filter,
    delete_freelancer,
    delete_platform_user,
    delete_tenant,
)
from app.modules.admin.schemas import (
    AdminUserSummary,
    DeleteResponse,
    PlatformStats,
    RemindTenantResponse,
    TenantHealthMetricsOut,
    TenantHealthRow,
    TenantSummary,
    TenantToggleResponse,
)
from app.modules.auth.models import User
from app.modules.billing.models import Subscription, SubscriptionPlan
from app.modules.crm.models import Deal
from app.modules.leads.models import Lead, LeadRequest
from app.modules.leads.schemas import LeadRequestResponse, LeadRequestAdminAction
from app.modules.leads import service as leads_svc
from app.modules.admin import tool_config as tc
from app.modules.admin.tool_config import (
    CategoryToolConfigResponse,
    CategoryToolConfigUpdate,
    KNOWN_CATEGORIES,
    TOOL_LABELS,
    ALL_TOOL_HREFS,
)
from app.modules.quotes_invoices.models import Invoice
from app.modules.tenants.models import Tenant, TenantMember
from app.modules.admin.tenant_health_service import (
    send_tenant_action_reminder,
    snapshot_tenant_health,
)
from app.modules.booking.enterprise_schemas import BookingFormTemplateUpdate

router = APIRouter(prefix="/admin", tags=["Admin"])


def _i(value) -> int:
    return int(value or 0)


@router.get("/me")
async def admin_me(admin: SuperAdmin):
    """Quick identity check — the web app uses this to gate /admin routes."""
    return {
        "id": str(admin.id),
        "email": admin.email,
        "full_name": admin.full_name,
        "is_superadmin": True,
    }


@router.get("/stats", response_model=PlatformStats)
async def platform_stats(admin: SuperAdmin, db: AsyncSession = Depends(get_db)):
    """Aggregate metrics across every tenant."""
    thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)

    total_tenants = _i((await db.execute(
        select(func.count(Tenant.id)).where(active_tenants_filter())
    )).scalar_one())
    active_tenants = _i((await db.execute(
        select(func.count(Tenant.id)).where(Tenant.is_active == True, active_tenants_filter())
    )).scalar_one())
    new_tenants_30d = _i((await db.execute(
        select(func.count(Tenant.id)).where(
            Tenant.created_at >= thirty_days_ago,
            active_tenants_filter(),
        )
    )).scalar_one())
    total_users = _i((await db.execute(
        select(func.count(User.id)).where(User.deleted_at.is_(None))
    )).scalar_one())

    total_leads = _i((await db.execute(select(func.count(Lead.id)))).scalar_one())
    total_deals = _i((await db.execute(select(func.count(Deal.id)))).scalar_one())
    total_invoices = _i((await db.execute(select(func.count(Invoice.id)))).scalar_one())

    paid_pence = _i((await db.execute(
        select(func.coalesce(func.sum(Invoice.total_pence), 0)).where(Invoice.status == "paid")
    )).scalar_one())
    open_pence = _i((await db.execute(
        select(func.coalesce(func.sum(Invoice.total_pence), 0))
        .where(Invoice.status.in_(("draft", "sent", "overdue")))
    )).scalar_one())

    # MRR = sum of (plan.price_gbp_monthly * 100) across active subscriptions
    mrr_pence = _i((await db.execute(
        select(func.coalesce(func.sum(SubscriptionPlan.price_gbp_monthly * 100), 0))
        .select_from(Subscription)
        .join(SubscriptionPlan, Subscription.plan_id == SubscriptionPlan.id)
        .where(Subscription.status.in_(("active", "trialing")))
    )).scalar_one())

    return PlatformStats(
        total_tenants=total_tenants,
        active_tenants=active_tenants,
        suspended_tenants=total_tenants - active_tenants,
        total_users=total_users,
        total_leads=total_leads,
        total_deals=total_deals,
        total_invoices=total_invoices,
        paid_invoices_pence=paid_pence,
        open_invoices_pence=open_pence,
        mrr_pence=mrr_pence,
        new_tenants_30d=new_tenants_30d,
    )


@router.get("/tenants", response_model=list[TenantSummary])
async def list_tenants(
    admin: SuperAdmin,
    db: AsyncSession = Depends(get_db),
    q: str | None = None,
    limit: int = 100,
    offset: int = 0,
):
    """List active tenants with rolled-up counts. Archived (deleted) workspaces are excluded."""
    stmt = (
        select(Tenant)
        .where(active_tenants_filter())
        .order_by(Tenant.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    if q:
        like = f"%{q.lower()}%"
        stmt = stmt.where(
            func.lower(Tenant.name).like(like) | func.lower(Tenant.slug).like(like)
        )
    tenants = (await db.execute(stmt)).scalars().all()
    if not tenants:
        return []

    tenant_ids = [t.id for t in tenants]

    # Plan + subscription
    sub_rows = (await db.execute(
        select(Subscription, SubscriptionPlan)
        .join(SubscriptionPlan, Subscription.plan_id == SubscriptionPlan.id)
        .where(Subscription.tenant_id.in_(tenant_ids))
    )).all()
    plans_by_tenant = {sub.tenant_id: (sub, plan) for sub, plan in sub_rows}

    async def _counts(model):
        rows = (await db.execute(
            select(model.tenant_id, func.count(model.id))
            .where(model.tenant_id.in_(tenant_ids))
            .group_by(model.tenant_id)
        )).all()
        return {tid: c for tid, c in rows}

    member_counts = {
        tid: c for tid, c in (await db.execute(
            select(TenantMember.tenant_id, func.count(TenantMember.id))
            .where(TenantMember.tenant_id.in_(tenant_ids))
            .group_by(TenantMember.tenant_id)
        )).all()
    }
    lead_counts = await _counts(Lead)
    deal_counts = await _counts(Deal)
    invoice_totals = {
        tid: total for tid, total in (await db.execute(
            select(Invoice.tenant_id, func.coalesce(func.sum(Invoice.total_pence), 0))
            .where(Invoice.tenant_id.in_(tenant_ids))
            .group_by(Invoice.tenant_id)
        )).all()
    }

    out: list[TenantSummary] = []
    for t in tenants:
        sp = plans_by_tenant.get(t.id)
        plan_name = sp[1].name if sp else None
        plan_price = (sp[1].price_gbp_monthly * 100) if sp else 0
        sub_status = sp[0].status if sp else None
        out.append(TenantSummary(
            id=t.id,
            slug=t.slug,
            name=t.name,
            business_type=t.business_type,
            city=t.city,
            postcode=t.postcode,
            plan_name=plan_name,
            plan_price_pence=plan_price,
            subscription_status=sub_status,
            is_active=t.is_active,
            onboarding_completed=t.onboarding_completed,
            member_count=_i(member_counts.get(t.id)),
            lead_count=_i(lead_counts.get(t.id)),
            deal_count=_i(deal_counts.get(t.id)),
            invoice_total_pence=_i(invoice_totals.get(t.id)),
            created_at=t.created_at,
            trial_ends_at=t.trial_ends_at,
        ))
    return out


@router.get("/tenants/{tenant_id}", response_model=TenantSummary)
async def get_tenant(
    tenant_id: uuid.UUID,
    admin: SuperAdmin,
    db: AsyncSession = Depends(get_db),
):
    tenant = (await db.execute(select(Tenant).where(Tenant.id == tenant_id))).scalar_one_or_none()
    if not tenant:
        raise HTTPException(404, "Tenant not found")

    # Reuse list logic for consistent shape
    rows = await list_tenants(admin=admin, db=db, q=None, limit=1000, offset=0)
    for row in rows:
        if row.id == tenant_id:
            return row
    # Fallback (shouldn't happen)
    return TenantSummary(
        id=tenant.id, slug=tenant.slug, name=tenant.name,
        business_type=tenant.business_type, city=tenant.city, postcode=tenant.postcode,
        is_active=tenant.is_active, onboarding_completed=tenant.onboarding_completed,
        created_at=tenant.created_at, trial_ends_at=tenant.trial_ends_at,
    )


@router.post("/tenants/{tenant_id}/suspend", response_model=TenantToggleResponse)
async def suspend_tenant(
    tenant_id: uuid.UUID,
    admin: SuperAdmin,
    db: AsyncSession = Depends(get_db),
):
    """Flag a tenant as suspended. Owner can still log in but tenant queries 403."""
    tenant = (await db.execute(select(Tenant).where(Tenant.id == tenant_id))).scalar_one_or_none()
    if not tenant:
        raise HTTPException(404, "Tenant not found")
    tenant.is_active = False
    db.add(tenant)
    await db.commit()
    return TenantToggleResponse(id=tenant.id, is_active=False, message=f"{tenant.name} suspended")


@router.post("/tenants/{tenant_id}/reactivate", response_model=TenantToggleResponse)
async def reactivate_tenant(
    tenant_id: uuid.UUID,
    admin: SuperAdmin,
    db: AsyncSession = Depends(get_db),
):
    tenant = (await db.execute(select(Tenant).where(Tenant.id == tenant_id))).scalar_one_or_none()
    if not tenant:
        raise HTTPException(404, "Tenant not found")
    tenant.is_active = True
    db.add(tenant)
    await db.commit()
    return TenantToggleResponse(id=tenant.id, is_active=True, message=f"{tenant.name} reactivated")


@router.delete("/tenants/{tenant_id}", response_model=DeleteResponse)
async def remove_tenant(
    tenant_id: uuid.UUID,
    admin: SuperAdmin,
    db: AsyncSession = Depends(get_db),
):
    """Permanently archive a tenant workspace (soft delete)."""
    out = await delete_tenant(db, tenant_id)
    return DeleteResponse(id=uuid.UUID(out["id"]), message=out["message"])


@router.get("/users", response_model=list[AdminUserSummary])
async def list_users(
    admin: SuperAdmin,
    db: AsyncSession = Depends(get_db),
    q: str | None = None,
    limit: int = 100,
    offset: int = 0,
):
    stmt = (
        select(User)
        .where(active_users_filter())
        .order_by(User.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    if q:
        like = f"%{q.lower()}%"
        stmt = stmt.where(
            func.lower(User.email).like(like) | func.lower(User.full_name).like(like)
        )
    users = (await db.execute(stmt)).scalars().all()
    if not users:
        return []

    user_ids = [u.id for u in users]
    tc_rows = (await db.execute(
        select(TenantMember.user_id, func.count(TenantMember.id))
        .where(TenantMember.user_id.in_(user_ids))
        .group_by(TenantMember.user_id)
    )).all()
    tenant_counts = {uid: c for uid, c in tc_rows}

    return [
        AdminUserSummary(
            id=u.id,
            email=u.email,
            full_name=u.full_name,
            user_type=u.user_type or "tenant",
            is_superadmin=u.is_superadmin,
            totp_enabled=u.totp_enabled,
            email_verified_at=u.email_verified_at,
            created_at=u.created_at,
            tenant_count=_i(tenant_counts.get(u.id)),
        )
        for u in users
    ]


@router.delete("/users/{user_id}", response_model=DeleteResponse)
async def remove_user(
    user_id: uuid.UUID,
    admin: SuperAdmin,
    db: AsyncSession = Depends(get_db),
    permanent: bool = Query(False, description="Hard-delete user and owned workspaces"),
):
    """Archive (default) or permanently delete a freelancer or tenant owner account."""
    out = await delete_platform_user(db, user_id, permanent=permanent)
    return DeleteResponse(id=uuid.UUID(out["id"]), message=out["message"])


@router.delete("/freelancers/{user_id}", response_model=DeleteResponse)
async def remove_freelancer(
    user_id: uuid.UUID,
    admin: SuperAdmin,
    db: AsyncSession = Depends(get_db),
    permanent: bool = Query(False, description="Hard-delete freelancer and managed clients"),
):
    """Archive (default) or permanently delete a freelancer account."""
    out = await delete_freelancer(db, user_id, permanent=permanent)
    return DeleteResponse(id=uuid.UUID(out["id"]), message=out["message"])


@router.get("/tenant-health", response_model=list[TenantHealthRow])
async def tenant_health_snapshot(admin: SuperAdmin, db: AsyncSession = Depends(get_db)):
    """Per-tenant operational flags (stale leads, open inboxes, overdue invoices, …)."""
    raw = await snapshot_tenant_health(db)
    return [
        TenantHealthRow(
            tenant_id=r["tenant_id"],
            name=r["name"],
            slug=r["slug"],
            email=r.get("email"),
            is_active=r["is_active"],
            metrics=TenantHealthMetricsOut(**r["metrics"]),
            flags=r["flags"],
            severity=r["severity"],
        )
        for r in raw
    ]


@router.post("/tenant-health/{tenant_id}/remind", response_model=RemindTenantResponse)
async def tenant_health_remind(
    tenant_id: uuid.UUID,
    admin: SuperAdmin,
    db: AsyncSession = Depends(get_db),
    note: str | None = None,
):
    """Notify every member in-app (and email owners) to review flagged work.

    Optional `note` query string is included in the message body.
    """
    out = await send_tenant_action_reminder(
        db, tenant_id=tenant_id, admin_user_id=admin.id, note=note
    )
    return RemindTenantResponse(**out)


# ── Lead Requests (admin) ─────────────────────────────────────────────────────

@router.get("/lead-requests", response_model=list[LeadRequestResponse])
async def admin_list_lead_requests(
    admin: SuperAdmin,
    db: AsyncSession = Depends(get_db),
    status: str | None = None,
    limit: int = 100,
):
    """List all tenant lead requests across the platform."""
    return await leads_svc.admin_list_lead_requests(db, status=status, limit=limit)


@router.post("/lead-requests/{request_id}/approve", response_model=LeadRequestResponse)
async def admin_approve_lead_request(
    request_id: uuid.UUID,
    body: LeadRequestAdminAction,
    admin: SuperAdmin,
    db: AsyncSession = Depends(get_db),
):
    return await leads_svc.admin_action_lead_request(db, request_id, "approve", body)


@router.post("/lead-requests/{request_id}/reject", response_model=LeadRequestResponse)
async def admin_reject_lead_request(
    request_id: uuid.UUID,
    body: LeadRequestAdminAction,
    admin: SuperAdmin,
    db: AsyncSession = Depends(get_db),
):
    return await leads_svc.admin_action_lead_request(db, request_id, "reject", body)


@router.post("/lead-requests/{request_id}/fulfill", response_model=LeadRequestResponse)
async def admin_fulfill_lead_request(
    request_id: uuid.UUID,
    body: LeadRequestAdminAction,
    admin: SuperAdmin,
    db: AsyncSession = Depends(get_db),
):
    return await leads_svc.admin_action_lead_request(db, request_id, "fulfill", body)


# ── Tool / Module visibility configuration (per business category) ────────────

@router.get("/tool-configs/meta")
async def tool_config_meta(_: SuperAdmin):
    """Return the canonical list of tool hrefs and labels, plus known categories."""
    return {
        "categories": KNOWN_CATEGORIES,
        "tools": [{"href": h, "label": TOOL_LABELS[h]} for h in ALL_TOOL_HREFS],
    }


@router.get("/tool-configs", response_model=list[CategoryToolConfigResponse])
async def list_tool_configs(_: SuperAdmin, db: AsyncSession = Depends(get_db)):
    """Return the effective tool config for every business category."""
    return await tc.get_all_configs(db)


@router.put("/tool-configs/{category}", response_model=CategoryToolConfigResponse)
async def update_tool_config(
    category: str,
    body: CategoryToolConfigUpdate,
    admin: SuperAdmin,
    db: AsyncSession = Depends(get_db),
):
    """Overwrite the enabled-tool list for a category."""
    return await tc.upsert_config(db, category, body.enabled_tools, updated_by=admin.id)


@router.post("/tool-configs/{category}/reset", response_model=CategoryToolConfigResponse)
async def reset_tool_config(
    category: str,
    _: SuperAdmin,
    db: AsyncSession = Depends(get_db),
):
    """Delete any customisation for a category, reverting to system defaults."""
    return await tc.reset_config(db, category)


# ── Booking form templates (per business category) ─────────────────────────────

@router.get("/booking-forms/categories")
async def list_booking_form_categories(_: SuperAdmin):
    from app.modules.booking.form_builder import BOOKING_CATEGORIES

    return {"categories": list(BOOKING_CATEGORIES)}


@router.get("/booking-forms/templates")
async def list_booking_form_templates(_: SuperAdmin, db: AsyncSession = Depends(get_db)):
    from app.modules.booking.form_builder import list_all_templates
    from app.modules.booking.enterprise_schemas import BookingFormTemplateResponse

    rows = await list_all_templates(db)
    return [
        BookingFormTemplateResponse(
            category=r.category,
            name=r.name,
            form_schema=r.schema,
            updated_at=r.updated_at,
        )
        for r in rows
    ]


@router.get("/booking-forms/templates/{category}")
async def get_booking_form_template(category: str, _: SuperAdmin, db: AsyncSession = Depends(get_db)):
    from app.core.exceptions import NotFoundException
    from app.modules.booking.form_builder import list_all_templates
    from app.modules.booking.enterprise_schemas import BookingFormTemplateResponse

    rows = await list_all_templates(db)
    row = next((r for r in rows if r.category == category), None)
    if not row:
        raise NotFoundException("Template")
    return BookingFormTemplateResponse(
        category=row.category,
        name=row.name,
        form_schema=row.schema,
        updated_at=row.updated_at,
    )


@router.put("/booking-forms/templates/{category}")
async def put_booking_form_template(
    category: str,
    body: BookingFormTemplateUpdate,
    admin: SuperAdmin,
    db: AsyncSession = Depends(get_db),
):
    from app.core.exceptions import BadRequestException
    from app.modules.booking.enterprise_schemas import BookingFormTemplateResponse
    from app.modules.booking.form_builder import upsert_template

    try:
        row = await upsert_template(
            db,
            category,
            body.form_schema,
            name=body.name,
            user_id=admin.id,
        )
    except ValueError as exc:
        raise BadRequestException(str(exc)) from exc
    return BookingFormTemplateResponse(
        category=row.category,
        name=row.name,
        form_schema=row.schema,
        updated_at=row.updated_at,
    )
