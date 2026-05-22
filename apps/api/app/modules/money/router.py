"""Money Intelligence dashboard endpoints.

Aggregates over invoices, payments, and deals to give the owner a single view
of cash position, growth, and AI-suggested upsells.
"""
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import CurrentTenantContext
from app.modules.crm.models import Customer, Deal
from app.modules.quotes_invoices.models import Invoice, Payment

router = APIRouter(prefix="/money", tags=["Money"])
accounts_router = APIRouter(prefix="/accounts", tags=["Accounts"])


def _coerce_date_key(value: date | str) -> date:
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value)[:10])


class MoneyHeadline(BaseModel):
    revenue_30d_pence: int
    revenue_90d_pence: int
    revenue_ytd_pence: int
    outstanding_pence: int
    overdue_pence: int
    deals_open_pence: int


class CashflowPoint(BaseModel):
    date: date
    paid_pence: int
    invoiced_pence: int


class UpsellSuggestion(BaseModel):
    customer_id: UUID
    name: str
    lifetime_value_pence: int
    last_deal_at: datetime | None
    reason: str


class MoneyDashboardResponse(BaseModel):
    headline: MoneyHeadline
    cashflow_daily: list[CashflowPoint]
    upsell_suggestions: list[UpsellSuggestion]


@router.get("/dashboard", response_model=MoneyDashboardResponse)
async def get_money_dashboard(
    ctx: CurrentTenantContext,
    db: AsyncSession = Depends(get_db),
    days: int = 90,
):
    _, tenant, _ = ctx
    now = datetime.now(timezone.utc)
    today = now.date()
    start_30 = today - timedelta(days=30)
    start_90 = today - timedelta(days=max(30, days))
    ytd_start = date(today.year, 1, 1)

    # ── Headline ─────────────────────────────────────────────────────────
    async def _sum_payments(since: date) -> int:
        result = await db.execute(
            select(func.coalesce(func.sum(Payment.amount_pence), 0))
            .where(
                Payment.tenant_id == tenant.id,
                Payment.status == "succeeded",
                func.date(Payment.created_at) >= since,
            )
        )
        return int(result.scalar_one())

    rev_30 = await _sum_payments(start_30)
    rev_90 = await _sum_payments(start_90)
    rev_ytd = await _sum_payments(ytd_start)

    outstanding = (await db.execute(
        select(func.coalesce(func.sum(Invoice.total_pence - Invoice.paid_pence), 0))
        .where(
            Invoice.tenant_id == tenant.id,
            Invoice.status.in_(("sent", "overdue", "partial")),
        )
    )).scalar_one()

    overdue = (await db.execute(
        select(func.coalesce(func.sum(Invoice.total_pence - Invoice.paid_pence), 0))
        .where(
            Invoice.tenant_id == tenant.id,
            Invoice.status.in_(("sent", "overdue", "partial")),
            Invoice.due_date.is_not(None),
            Invoice.due_date < today,
        )
    )).scalar_one()

    deals_open = (await db.execute(
        select(func.coalesce(func.sum(Deal.value_pence), 0))
        .where(
            Deal.tenant_id == tenant.id,
            Deal.deleted_at.is_(None),
            Deal.stage.notin_(("Completed", "Lost")),
        )
    )).scalar_one()

    headline = MoneyHeadline(
        revenue_30d_pence=rev_30,
        revenue_90d_pence=rev_90,
        revenue_ytd_pence=rev_ytd,
        outstanding_pence=int(outstanding),
        overdue_pence=int(overdue),
        deals_open_pence=int(deals_open),
    )

    # ── Daily cashflow over `days` ───────────────────────────────────────
    payments_by_day = {
        _coerce_date_key(k): int(v)
        for k, v in (
            await db.execute(
                select(func.date(Payment.created_at), func.coalesce(func.sum(Payment.amount_pence), 0))
                .where(
                    Payment.tenant_id == tenant.id,
                    Payment.status == "succeeded",
                    func.date(Payment.created_at) >= start_90,
                )
                .group_by(func.date(Payment.created_at))
            )
        ).all()
    }
    invoiced_by_day = {
        _coerce_date_key(k): int(v)
        for k, v in (
            await db.execute(
                select(func.date(Invoice.created_at), func.coalesce(func.sum(Invoice.total_pence), 0))
                .where(
                    Invoice.tenant_id == tenant.id,
                    func.date(Invoice.created_at) >= start_90,
                )
                .group_by(func.date(Invoice.created_at))
            )
        ).all()
    }

    cashflow_daily: list[CashflowPoint] = []
    d = start_90
    while d <= today:
        cashflow_daily.append(CashflowPoint(
            date=d,
            paid_pence=int(payments_by_day.get(d, 0)),
            invoiced_pence=int(invoiced_by_day.get(d, 0)),
        ))
        d = d + timedelta(days=1)

    # ── Upsell suggestions ───────────────────────────────────────────────
    # Heuristic: customers with completed deals, no deal in last 90 days,
    # ranked by lifetime value descending. Phase 2 will replace this with
    # an AI segmentation call, but the heuristic is solid and free.
    cutoff = now - timedelta(days=90)
    upsell_rows = (
        await db.execute(
            select(
                Customer.id,
                func.coalesce(Customer.first_name, ""),
                func.coalesce(Customer.last_name, ""),
                func.coalesce(func.sum(Deal.value_pence), 0).label("ltv"),
                func.max(Deal.created_at).label("last_deal_at"),
            )
            .join(Deal, Deal.customer_id == Customer.id)
            .where(
                Customer.tenant_id == tenant.id,
                Customer.deleted_at.is_(None),
                Deal.deleted_at.is_(None),
            )
            .group_by(Customer.id, Customer.first_name, Customer.last_name)
            .having(
                and_(
                    func.coalesce(func.sum(Deal.value_pence), 0) >= 10000,  # ≥ £100
                    func.max(Deal.created_at) < cutoff,
                )
            )
            .order_by(func.coalesce(func.sum(Deal.value_pence), 0).desc())
            .limit(8)
        )
    ).all()

    suggestions: list[UpsellSuggestion] = []
    for row in upsell_rows:
        cid, first, last, ltv, last_deal_at = row
        suggestions.append(UpsellSuggestion(
            customer_id=cid,
            name=f"{first} {last}".strip() or "Unknown customer",
            lifetime_value_pence=int(ltv),
            last_deal_at=last_deal_at,
            reason=(
                f"High lifetime value (£{(int(ltv) / 100):.0f}) but no deal in 90+ days — "
                "ripe for a re-engagement campaign."
            ),
        ))

    return MoneyDashboardResponse(
        headline=headline,
        cashflow_daily=cashflow_daily,
        upsell_suggestions=suggestions,
    )


@accounts_router.get("/dashboard", response_model=MoneyDashboardResponse)
async def get_accounts_dashboard(
    ctx: CurrentTenantContext,
    db: AsyncSession = Depends(get_db),
    days: int = 90,
):
    """Alias for money dashboard — used by Accounts module UI."""
    return await get_money_dashboard(ctx, db, days=days)
