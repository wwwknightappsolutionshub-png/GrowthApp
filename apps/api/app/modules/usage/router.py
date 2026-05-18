"""Usage tracking + quota enforcement.

Provides per-tenant rollups of AI spend over a date window. Quota enforcement
is plan-driven: each plan has a monthly AI-cost ceiling (pence). When a
tenant exceeds it, downstream callers can check `is_over_quota` and either
fall back to cheaper providers or block the action.
"""
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import CurrentTenantContext, SuperAdmin
from app.services.ai.models import AIUsageEvent

router = APIRouter(prefix="/usage", tags=["Usage"])


# Plan → monthly AI-cost ceiling in pence. Mirrors infra/billing config.
_PLAN_QUOTAS: dict[str, int] = {
    "free": 200,        # £2
    "starter": 5_000,   # £50
    "pro": 20_000,      # £200
    "business": 60_000, # £600
    "enterprise": 0,    # unlimited
}


def quota_for(plan: str | None) -> int:
    if not plan:
        return _PLAN_QUOTAS["starter"]
    return _PLAN_QUOTAS.get(plan.lower(), _PLAN_QUOTAS["starter"])


class UsageBreakdown(BaseModel):
    purpose: str
    calls: int
    input_tokens: int
    output_tokens: int
    cost_pence: int


class UsageRollup(BaseModel):
    tenant_id: UUID
    period_start: date
    period_end: date
    plan: str | None
    quota_pence: int
    used_pence: int
    used_pct: float
    over_quota: bool
    total_calls: int
    breakdown: list[UsageBreakdown]


async def _resolve_plan_name(db: AsyncSession, tenant_id: UUID) -> str | None:
    """Look up the subscription plan name for a tenant (best-effort)."""
    from app.modules.billing.models import Subscription, SubscriptionPlan

    row = (
        await db.execute(
            select(SubscriptionPlan.name)
            .join(Subscription, Subscription.plan_id == SubscriptionPlan.id)
            .where(Subscription.tenant_id == tenant_id)
        )
    ).scalar_one_or_none()
    return row


@router.get("/me", response_model=UsageRollup)
async def my_usage(
    ctx: CurrentTenantContext,
    db: AsyncSession = Depends(get_db),
    days: int = Query(default=30, ge=1, le=365),
):
    _, tenant, _ = ctx
    plan = await _resolve_plan_name(db, tenant.id)
    end = datetime.now(timezone.utc)
    start = end - timedelta(days=days)
    return await _rollup(db, tenant.id, plan=plan, start=start, end=end)


@router.get("/tenants/{tenant_id}", response_model=UsageRollup)
async def tenant_usage(
    tenant_id: UUID,
    _admin: SuperAdmin,
    db: AsyncSession = Depends(get_db),
    days: int = Query(default=30, ge=1, le=365),
):
    plan = await _resolve_plan_name(db, tenant_id)
    end = datetime.now(timezone.utc)
    start = end - timedelta(days=days)
    return await _rollup(db, tenant_id, plan=plan, start=start, end=end)


async def _rollup(
    db: AsyncSession,
    tenant_id: UUID,
    *,
    plan: str | None,
    start: datetime,
    end: datetime,
) -> UsageRollup:
    rows = (
        await db.execute(
            select(
                AIUsageEvent.purpose,
                func.count(AIUsageEvent.id),
                func.coalesce(func.sum(AIUsageEvent.input_tokens), 0),
                func.coalesce(func.sum(AIUsageEvent.output_tokens), 0),
                func.coalesce(func.sum(AIUsageEvent.cost_pence), 0),
            )
            .where(
                AIUsageEvent.tenant_id == tenant_id,
                AIUsageEvent.created_at >= start,
                AIUsageEvent.created_at <= end,
                AIUsageEvent.status == "success",
            )
            .group_by(AIUsageEvent.purpose)
        )
    ).all()

    breakdown = [
        UsageBreakdown(
            purpose=str(r[0] or "unknown"),
            calls=int(r[1] or 0),
            input_tokens=int(r[2] or 0),
            output_tokens=int(r[3] or 0),
            cost_pence=int(r[4] or 0),
        )
        for r in rows
    ]
    total_cost = sum(b.cost_pence for b in breakdown)
    total_calls = sum(b.calls for b in breakdown)
    quota = quota_for(plan)
    over = bool(quota and total_cost > quota)
    pct = (total_cost / quota * 100.0) if quota else 0.0

    return UsageRollup(
        tenant_id=tenant_id,
        period_start=start.date(),
        period_end=end.date(),
        plan=plan,
        quota_pence=quota,
        used_pence=total_cost,
        used_pct=round(pct, 1),
        over_quota=over,
        total_calls=total_calls,
        breakdown=sorted(breakdown, key=lambda b: -b.cost_pence),
    )


async def is_tenant_over_quota(
    db: AsyncSession, tenant_id: UUID, plan: str | None
) -> bool:
    """Helper for downstream services to gate AI calls when over quota."""
    quota = quota_for(plan)
    if not quota:
        return False
    end = datetime.now(timezone.utc)
    start = end - timedelta(days=30)
    used = (
        await db.execute(
            select(func.coalesce(func.sum(AIUsageEvent.cost_pence), 0)).where(
                AIUsageEvent.tenant_id == tenant_id,
                AIUsageEvent.created_at >= start,
                AIUsageEvent.status == "success",
            )
        )
    ).scalar() or 0
    return int(used) > quota
