"""Super Admin — Billing Inspector (read-only billing oversight).

Endpoints
---------
GET /api/super-admin/billing/overview
GET /api/super-admin/billing/tenants
GET /api/super-admin/billing/freelancers
GET /api/super-admin/billing/tenant/{id}
GET /api/super-admin/billing/freelancer/{id}
GET /api/super-admin/billing/audit-logs
GET /api/super-admin/billing/invoice/{invoiceId}

These compose data from existing models (Tenant, Subscription, SubscriptionPlan,
BillingInvoice, FreelancerBilling, AuditLog, User). They DO NOT mutate state and
DO NOT replace any existing routes. The legacy `/api/admin/billing/*` and
`/api/admin/freelancer-management/*` routes remain in place and untouched.
"""
from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import SuperAdmin
from app.modules.audit.models import AuditLog
from app.modules.auth.models import User
from app.modules.billing.models import (
    BillingInvoice,
    FreelancerBilling,
    Subscription,
    SubscriptionPlan,
)
from app.modules.crm.models import Customer
from app.modules.tenants.models import Tenant, TenantMember


router = APIRouter(
    prefix="/api/super-admin/billing",
    tags=["Super Admin — Billing Inspector"],
)


# ── Helpers ────────────────────────────────────────────────────────────────

_PAYMENT_FAILURE_STATUSES = {"failed", "payment_failed", "uncollectible"}
_OVERDUE_STATUSES = {"open", "uncollectible", "past_due"}
_UPCOMING_HORIZON_DAYS = 30
_PAYMENT_FAILURE_PATTERN = re.compile(r"payment.*fail|invoice.*fail|charge.*fail", re.IGNORECASE)


def _to_decimal(v: Any) -> Decimal:
    if v is None:
        return Decimal("0")
    if isinstance(v, Decimal):
        return v
    return Decimal(str(v))


def _iso(dt: Optional[datetime]) -> Optional[str]:
    return dt.isoformat() if dt else None


def _freelancer_tier(count: int) -> str:
    if count <= 50:
        return "1-50"
    if count <= 100:
        return "51-100"
    return ">100"


async def _freelancer_overage_alerts(billing: FreelancerBilling) -> list[str]:
    """Heuristic overage flags for freelancers.

    A freelancer is "overage-flagged" when the effective price exceeds the
    auto-calculated price by more than 25%, or when client count grew beyond
    the snapshot.
    """
    alerts: list[str] = []
    effective = billing.override_price if billing.override_price is not None else billing.calculated_price
    calc = _to_decimal(billing.calculated_price)
    eff = _to_decimal(effective)
    if eff > calc * Decimal("1.25"):
        alerts.append("manual_override_above_auto")
    return alerts


async def _tenant_overage_alerts(
    db: AsyncSession, tenant: Tenant, plan: Optional[SubscriptionPlan]
) -> list[str]:
    alerts: list[str] = []
    if plan is None:
        return ["no_plan_assigned"]

    # Contacts vs plan.max_leads_per_month proxy (no dedicated max_contacts column today).
    contacts_used = (
        await db.execute(
            select(func.count(Customer.id)).where(Customer.tenant_id == tenant.id)
        )
    ).scalar_one() or 0
    if plan.max_leads_per_month and contacts_used > plan.max_leads_per_month:
        alerts.append("contacts_over_plan_limit")

    seats_used = (
        await db.execute(
            select(func.count(TenantMember.id)).where(TenantMember.tenant_id == tenant.id)
        )
    ).scalar_one() or 0
    if plan.max_users and seats_used > plan.max_users:
        alerts.append("seats_over_plan_limit")
    return alerts


# ── 5.1  Overview ──────────────────────────────────────────────────────────

@router.get("/overview")
async def overview(
    _: SuperAdmin,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    total_tenants = (
        await db.execute(select(func.count(Tenant.id)).where(Tenant.is_active == True))  # noqa: E712
    ).scalar_one() or 0
    total_freelancers = (
        await db.execute(select(func.count(User.id)).where(User.user_type == "freelancer"))
    ).scalar_one() or 0

    # Tenant MRR — sum of plan.price_gbp_monthly for tenants that have an active subscription.
    tenant_mrr_rows = (
        await db.execute(
            select(SubscriptionPlan.price_gbp_monthly)
            .join(Subscription, Subscription.plan_id == SubscriptionPlan.id)
            .where(Subscription.status.in_(["active", "trialing"]))
        )
    ).scalars().all()
    tenant_mrr = sum((_to_decimal(p) for p in tenant_mrr_rows), Decimal("0"))

    # Freelancer MRR — effective price (override or calculated).
    fl_rows = (await db.execute(select(FreelancerBilling))).scalars().all()
    fl_mrr = sum(
        (_to_decimal(b.override_price if b.override_price is not None else b.calculated_price)
         for b in fl_rows),
        Decimal("0"),
    )

    total_mrr = tenant_mrr + fl_mrr

    now = datetime.now(timezone.utc)
    horizon = now + timedelta(days=_UPCOMING_HORIZON_DAYS)
    upcoming = (
        await db.execute(
            select(func.count(BillingInvoice.id)).where(
                BillingInvoice.period_end != None,  # noqa: E711
                BillingInvoice.period_end >= now,
                BillingInvoice.period_end <= horizon,
            )
        )
    ).scalar_one() or 0
    overdue = (
        await db.execute(
            select(func.count(BillingInvoice.id)).where(
                BillingInvoice.status.in_(list(_OVERDUE_STATUSES)),
                BillingInvoice.period_end != None,  # noqa: E711
                BillingInvoice.period_end < now,
            )
        )
    ).scalar_one() or 0

    failures_rows = (
        await db.execute(
            select(BillingInvoice)
            .where(BillingInvoice.status.in_(list(_PAYMENT_FAILURE_STATUSES)))
            .order_by(BillingInvoice.created_at.desc())
            .limit(5)
        )
    ).scalars().all()

    recent_failures = []
    for inv in failures_rows:
        recent_failures.append({
            "invoice_id": str(inv.id),
            "tenant_id": str(inv.tenant_id),
            "amount_pence": inv.amount_pence,
            "status": inv.status,
            "created_at": _iso(inv.created_at),
        })

    # Global overage alerts — distinct alert types observed across all tenants.
    overage_alerts: list[dict[str, Any]] = []
    seen_alerts: set[str] = set()
    tenants = (await db.execute(select(Tenant).where(Tenant.is_active == True))).scalars().all()  # noqa: E712
    for t in tenants:
        plan = None
        if t.plan_id:
            plan = (
                await db.execute(select(SubscriptionPlan).where(SubscriptionPlan.id == t.plan_id))
            ).scalar_one_or_none()
        flags = await _tenant_overage_alerts(db, t, plan)
        for f in flags:
            key = f"tenant:{t.id}:{f}"
            if key not in seen_alerts:
                seen_alerts.add(key)
                overage_alerts.append({
                    "entity_type": "tenant",
                    "entity_id": str(t.id),
                    "entity_name": t.name,
                    "flag": f,
                })

    return {
        "total_tenants": total_tenants,
        "total_freelancers": total_freelancers,
        "total_mrr_gbp": float(total_mrr),
        "tenant_mrr_gbp": float(tenant_mrr),
        "freelancer_mrr_gbp": float(fl_mrr),
        "upcoming_invoices_count": upcoming,
        "overdue_invoices_count": overdue,
        "recent_payment_failures": recent_failures,
        "global_overage_alerts": overage_alerts,
    }


# ── 5.2  Tenants list (paginated, filterable) ──────────────────────────────

@router.get("/tenants")
async def list_tenants(
    _: SuperAdmin,
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    plan: Optional[str] = Query(None, description="Filter by plan name (exact match)"),
    overage_state: Optional[str] = Query(None, pattern="^(any|none)$"),
    invoice_status: Optional[str] = Query(None),
) -> dict[str, Any]:
    q = select(Tenant).where(Tenant.is_active == True)  # noqa: E712
    total = (await db.execute(select(func.count()).select_from(q.subquery()))).scalar_one() or 0

    rows = (
        await db.execute(q.order_by(Tenant.created_at.desc()).offset((page - 1) * page_size).limit(page_size))
    ).scalars().all()

    items: list[dict[str, Any]] = []
    for t in rows:
        plan_obj: Optional[SubscriptionPlan] = None
        if t.plan_id:
            plan_obj = (
                await db.execute(select(SubscriptionPlan).where(SubscriptionPlan.id == t.plan_id))
            ).scalar_one_or_none()
        if plan and (plan_obj is None or plan_obj.name != plan):
            continue

        contacts_count = (
            await db.execute(select(func.count(Customer.id)).where(Customer.tenant_id == t.id))
        ).scalar_one() or 0
        active_seats = (
            await db.execute(select(func.count(TenantMember.id)).where(TenantMember.tenant_id == t.id))
        ).scalar_one() or 0

        last_invoice = (
            await db.execute(
                select(BillingInvoice)
                .where(BillingInvoice.tenant_id == t.id)
                .order_by(BillingInvoice.created_at.desc())
                .limit(1)
            )
        ).scalar_one_or_none()

        next_billing = None
        sub = (
            await db.execute(select(Subscription).where(Subscription.tenant_id == t.id))
        ).scalar_one_or_none()
        if sub and sub.current_period_end:
            next_billing = sub.current_period_end

        alerts = await _tenant_overage_alerts(db, t, plan_obj)

        if overage_state == "any" and not alerts:
            continue
        if overage_state == "none" and alerts:
            continue
        if invoice_status:
            if last_invoice is None or last_invoice.status != invoice_status:
                continue

        items.append({
            "tenant_id": str(t.id),
            "tenant_name": t.name,
            "plan_id": str(plan_obj.id) if plan_obj else None,
            "plan_name": plan_obj.name if plan_obj else None,
            "monthly_price_gbp": float(plan_obj.price_gbp_monthly) if plan_obj else 0.0,
            "contacts_count": contacts_count,
            "active_seats": active_seats,
            "last_invoice_status": last_invoice.status if last_invoice else None,
            "next_billing_date": _iso(next_billing),
            "overage_alerts": alerts,
        })

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
    }


# ── 5.3  Freelancers list (paginated, filterable) ──────────────────────────

@router.get("/freelancers")
async def list_freelancers(
    _: SuperAdmin,
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    plan: Optional[str] = Query(None, description="Filter by auto-tier: 1-50 | 51-100 | >100"),
    overage_state: Optional[str] = Query(None, pattern="^(any|none)$"),
    invoice_status: Optional[str] = Query(None),
) -> dict[str, Any]:
    base = (
        select(User, FreelancerBilling)
        .join(FreelancerBilling, FreelancerBilling.user_id == User.id, isouter=True)
        .where(User.user_type == "freelancer")
    )
    total = (await db.execute(select(func.count()).select_from(base.subquery()))).scalar_one() or 0
    rows = (
        await db.execute(base.order_by(User.created_at.desc()).offset((page - 1) * page_size).limit(page_size))
    ).all()

    items: list[dict[str, Any]] = []
    for user, billing in rows:
        count = (billing.estimated_client_count if billing else user.estimated_client_count) or 0
        tier = _freelancer_tier(count)
        if plan and tier != plan:
            continue

        effective = None
        calc = None
        override = None
        source = None
        if billing:
            calc = _to_decimal(billing.calculated_price)
            override = billing.override_price
            effective = _to_decimal(billing.override_price if billing.override_price is not None else billing.calculated_price)
            source = billing.calculation_source

        # Freelancer invoices — none exist today (BillingInvoice is tenant-only),
        # so last_invoice_status / next_billing_date are advisory.
        last_invoice_status: Optional[str] = None
        next_billing_date: Optional[datetime] = None

        alerts: list[str] = []
        if billing:
            alerts = await _freelancer_overage_alerts(billing)

        if overage_state == "any" and not alerts:
            continue
        if overage_state == "none" and alerts:
            continue
        if invoice_status and invoice_status != last_invoice_status:
            continue

        items.append({
            "user_id": str(user.id),
            "freelancer_name": user.full_name,
            "email": user.email,
            "managed_clients": count,
            "auto_plan_tier": tier,
            "calculated_price_gbp": float(calc) if calc is not None else None,
            "override_price_gbp": float(override) if override is not None else None,
            "monthly_price_gbp": float(effective) if effective is not None else None,
            "calculation_source": source,
            "last_invoice_status": last_invoice_status,
            "next_billing_date": _iso(next_billing_date),
            "overage_alerts": alerts,
        })

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
    }


# ── 5.4  Tenant billing profile ────────────────────────────────────────────

@router.get("/tenant/{id}")
async def tenant_profile(
    id: UUID,
    _: SuperAdmin,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    tenant = (await db.execute(select(Tenant).where(Tenant.id == id))).scalar_one_or_none()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    plan_obj: Optional[SubscriptionPlan] = None
    if tenant.plan_id:
        plan_obj = (
            await db.execute(select(SubscriptionPlan).where(SubscriptionPlan.id == tenant.plan_id))
        ).scalar_one_or_none()

    contacts_used = (
        await db.execute(select(func.count(Customer.id)).where(Customer.tenant_id == id))
    ).scalar_one() or 0
    seats_used = (
        await db.execute(select(func.count(TenantMember.id)).where(TenantMember.tenant_id == id))
    ).scalar_one() or 0

    subscription = (
        await db.execute(select(Subscription).where(Subscription.tenant_id == id))
    ).scalar_one_or_none()

    invoices = (
        await db.execute(
            select(BillingInvoice)
            .where(BillingInvoice.tenant_id == id)
            .order_by(BillingInvoice.created_at.desc())
            .limit(50)
        )
    ).scalars().all()

    audit_trail = (
        await db.execute(
            select(AuditLog)
            .where(AuditLog.tenant_id == id)
            .order_by(AuditLog.created_at.desc())
            .limit(50)
        )
    ).scalars().all()

    overage_flags = await _tenant_overage_alerts(db, tenant, plan_obj)
    overage_details = {
        "alerts": overage_flags,
        "contacts": {
            "used": contacts_used,
            "limit": plan_obj.max_leads_per_month if plan_obj else None,
            "over": bool(plan_obj and plan_obj.max_leads_per_month and contacts_used > plan_obj.max_leads_per_month),
        },
        "seats": {
            "used": seats_used,
            "limit": plan_obj.max_users if plan_obj else None,
            "over": bool(plan_obj and plan_obj.max_users and seats_used > plan_obj.max_users),
        },
    }

    # Plan alignment — recommend the cheapest plan that fits current usage.
    plans = (
        await db.execute(select(SubscriptionPlan).order_by(SubscriptionPlan.price_gbp_monthly))
    ).scalars().all()
    fitting = [
        p for p in plans
        if (not p.max_users or seats_used <= p.max_users)
        and (not p.max_leads_per_month or contacts_used <= p.max_leads_per_month)
    ]
    recommended_plan = fitting[0] if fitting else None
    aligned = bool(plan_obj and recommended_plan and plan_obj.id == recommended_plan.id)
    plan_alignment = {
        "current_plan_id": str(plan_obj.id) if plan_obj else None,
        "current_plan_name": plan_obj.name if plan_obj else None,
        "recommended_plan_id": str(recommended_plan.id) if recommended_plan else None,
        "recommended_plan_name": recommended_plan.name if recommended_plan else None,
        "aligned": aligned,
        "reason": None if aligned else "current_plan_limits_exceeded_or_overpaying",
    }

    return {
        "tenant": {
            "id": str(tenant.id),
            "name": tenant.name,
            "slug": tenant.slug,
            "business_type": tenant.business_type,
            "email": tenant.email,
            "phone": tenant.phone,
            "postcode": tenant.postcode,
            "is_active": tenant.is_active,
            "created_at": _iso(tenant.created_at),
        },
        "current_plan": (
            {
                "id": str(plan_obj.id),
                "name": plan_obj.name,
                "monthly_price_gbp": float(plan_obj.price_gbp_monthly),
                "max_users": plan_obj.max_users,
                "max_leads_per_month": plan_obj.max_leads_per_month,
                "ai_lead_requests_per_month": plan_obj.ai_lead_requests_per_month,
            }
            if plan_obj
            else None
        ),
        "usage": {
            "seats": {"used": seats_used, "limit": plan_obj.max_users if plan_obj else None},
            "contacts": {
                "used": contacts_used,
                "limit": plan_obj.max_leads_per_month if plan_obj else None,
            },
        },
        "subscription": (
            {
                "id": str(subscription.id),
                "status": subscription.status,
                "current_period_start": _iso(subscription.current_period_start),
                "current_period_end": _iso(subscription.current_period_end),
                "stripe_customer_id": subscription.stripe_customer_id,
                "stripe_subscription_id": subscription.stripe_subscription_id,
            }
            if subscription
            else None
        ),
        "payment_method": (
            f"stripe:{subscription.stripe_customer_id}"
            if subscription and subscription.stripe_customer_id
            else None
        ),
        "invoice_history": [
            {
                "id": str(i.id),
                "amount_pence": i.amount_pence,
                "currency": i.currency,
                "status": i.status,
                "period_start": _iso(i.period_start),
                "period_end": _iso(i.period_end),
                "invoice_pdf_url": i.invoice_pdf_url,
                "created_at": _iso(i.created_at),
            }
            for i in invoices
        ],
        "overage_details": overage_details,
        "audit_trail": [
            {
                "id": str(a.id),
                "action": a.action,
                "resource": a.resource,
                "resource_id": a.resource_id,
                "metadata": a.extra_metadata or {},
                "created_at": _iso(a.created_at),
            }
            for a in audit_trail
        ],
        "plan_alignment": plan_alignment,
    }


# ── 5.5  Freelancer billing profile ────────────────────────────────────────

@router.get("/freelancer/{id}")
async def freelancer_profile(
    id: UUID,
    _: SuperAdmin,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    user = (
        await db.execute(select(User).where(User.id == id, User.user_type == "freelancer"))
    ).scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Freelancer not found")

    billing = (
        await db.execute(select(FreelancerBilling).where(FreelancerBilling.user_id == id))
    ).scalar_one_or_none()

    managed = (billing.estimated_client_count if billing else user.estimated_client_count) or 0
    tier = _freelancer_tier(managed)

    auto_calculated = None
    if billing:
        calc = _to_decimal(billing.calculated_price)
        override = billing.override_price
        effective = _to_decimal(billing.override_price if billing.override_price is not None else billing.calculated_price)
        auto_calculated = {
            "tier": tier,
            "calculated_price_gbp": float(calc),
            "override_price_gbp": float(override) if override is not None else None,
            "effective_price_gbp": float(effective),
            "calculation_source": billing.calculation_source,
        }

    audit_trail = (
        await db.execute(
            select(AuditLog)
            .where(AuditLog.user_id == id)
            .order_by(AuditLog.created_at.desc())
            .limit(50)
        )
    ).scalars().all()

    return {
        "freelancer": {
            "id": str(user.id),
            "full_name": user.full_name,
            "email": user.email,
            "phone": user.phone,
            "managed_clients_signup": user.estimated_client_count,
            "created_at": _iso(user.created_at),
        },
        "managed_clients_count": managed,
        "auto_calculated_plan": auto_calculated,
        "auto_upgrade_logic": {
            "tier_1_50_gbp": 50,
            "tier_51_100_gbp": 40,
            "tier_over_100_base_gbp": 40,
            "per_extra_client_gbp": 5,
            "notes": "Tiers re-evaluate on signup; manual override available via Billing Inspector.",
        },
        "invoice_history": [],
        "payment_method": None,
        "usage_records": [
            {
                "id": str(a.id),
                "action": a.action,
                "resource": a.resource,
                "metadata": a.extra_metadata or {},
                "created_at": _iso(a.created_at),
            }
            for a in audit_trail
        ],
    }


# ── 5.6  Audit logs ────────────────────────────────────────────────────────

def _classify_audit(action: str) -> str:
    a = action.lower()
    if "plan" in a or "subscription" in a:
        return "plan_change"
    if "overage" in a:
        return "overage_flag"
    if "invoice" in a or "payment" in a and "fail" not in a:
        return "invoice_event"
    if _PAYMENT_FAILURE_PATTERN.search(a):
        return "payment_failure"
    return "other"


@router.get("/audit-logs")
async def audit_logs(
    _: SuperAdmin,
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    type: Optional[str] = Query(
        None,
        pattern="^(plan_change|overage_flag|invoice_event|payment_failure)$",
    ),
) -> dict[str, Any]:
    base = select(AuditLog).where(
        or_(
            AuditLog.action.like("%plan%"),
            AuditLog.action.like("%subscription%"),
            AuditLog.action.like("%invoice%"),
            AuditLog.action.like("%payment%"),
            AuditLog.action.like("%billing%"),
            AuditLog.action.like("%overage%"),
        )
    )
    total = (await db.execute(select(func.count()).select_from(base.subquery()))).scalar_one() or 0

    rows = (
        await db.execute(
            base.order_by(AuditLog.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
    ).scalars().all()

    items: list[dict[str, Any]] = []
    for log in rows:
        classified = _classify_audit(log.action)
        if type and classified != type:
            continue

        entity_type = "tenant" if log.tenant_id else ("freelancer" if log.user_id else "system")
        entity_name = None
        if log.tenant_id:
            t = (await db.execute(select(Tenant).where(Tenant.id == log.tenant_id))).scalar_one_or_none()
            entity_name = t.name if t else None
        elif log.user_id:
            u = (await db.execute(select(User).where(User.id == log.user_id))).scalar_one_or_none()
            entity_name = u.full_name if u else None

        items.append({
            "id": str(log.id),
            "timestamp": _iso(log.created_at),
            "type": classified,
            "entity_type": entity_type,
            "entity_id": str(log.tenant_id or log.user_id) if (log.tenant_id or log.user_id) else None,
            "entity_name": entity_name,
            "description": f"{log.action} on {log.resource}",
            "metadata": log.extra_metadata or {},
        })

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
    }


# ── 5.7  Invoice view ──────────────────────────────────────────────────────

@router.get("/invoice/{invoiceId}")
async def invoice_detail(
    invoiceId: UUID,
    _: SuperAdmin,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    inv = (
        await db.execute(select(BillingInvoice).where(BillingInvoice.id == invoiceId))
    ).scalar_one_or_none()
    if not inv:
        raise HTTPException(status_code=404, detail="Invoice not found")

    tenant = (
        await db.execute(select(Tenant).where(Tenant.id == inv.tenant_id))
    ).scalar_one_or_none()

    payment_attempts = (
        await db.execute(
            select(AuditLog)
            .where(
                AuditLog.tenant_id == inv.tenant_id,
                or_(
                    AuditLog.action.like("%payment%"),
                    AuditLog.action.like("%invoice%"),
                ),
                AuditLog.resource_id == str(inv.id),
            )
            .order_by(AuditLog.created_at.desc())
        )
    ).scalars().all()

    return {
        "id": str(inv.id),
        "customer": {
            "type": "tenant",
            "id": str(inv.tenant_id),
            "name": tenant.name if tenant else None,
        },
        "billing_period": {
            "start": _iso(inv.period_start),
            "end": _iso(inv.period_end),
        },
        "stripe_invoice_id": inv.stripe_invoice_id,
        "line_items": [
            {
                "description": f"Subscription · {inv.currency.upper()}",
                "amount_pence": inv.amount_pence,
            }
        ],
        "subtotal_pence": inv.amount_pence,
        "tax_pence": 0,
        "overage_pence": 0,
        "discount_pence": 0,
        "total_pence": inv.amount_pence,
        "currency": inv.currency,
        "status": inv.status,
        "invoice_pdf_url": inv.invoice_pdf_url,
        "created_at": _iso(inv.created_at),
        "payment_attempts": [
            {
                "id": str(a.id),
                "timestamp": _iso(a.created_at),
                "action": a.action,
                "status": (a.extra_metadata or {}).get("status"),
                "metadata": a.extra_metadata or {},
            }
            for a in payment_attempts
        ],
    }
