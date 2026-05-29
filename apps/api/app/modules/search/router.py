"""Global search endpoint — powers the Cmd-K palette and top-bar search.

Strategy:

  * One tenant-scoped query, ILIKE/LOWER on the most-searched fields per
    resource (customer name, lead name, deal title, quote/invoice number).
  * Per-resource hit cap so a single huge resource type doesn't drown others.
  * Results are merged into a uniform shape: ``{type, id, label, sublabel,
    url, score}`` so the UI can render any hit identically.

This is intentionally simple. For tenants with > 100k rows of any one entity,
swap the implementation for Postgres tsvector or Meilisearch behind the same
endpoint contract.
"""
from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import CurrentTenantContext
from app.modules.crm.models import Customer, Deal
from app.modules.leads.models import Lead
from app.modules.quotes_invoices.models import Invoice, Quote
from app.modules.tasks.models import Task

router = APIRouter(prefix="/search", tags=["Search"])

DEFAULT_PER_TYPE_LIMIT = 5


class SearchHit(BaseModel):
    type: str
    id: uuid.UUID
    label: str
    sublabel: str | None = None
    url: str
    score: float = 0.0


class SearchResponse(BaseModel):
    hits: list[SearchHit]
    by_type: dict[str, int]


def _escape_like(term: str) -> str:
    """Escape LIKE-special characters so user input is treated as literals."""
    return term.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def _ilike(col, term: str):
    """Cross-dialect case-insensitive substring filter."""
    safe = _escape_like(term.lower())
    return func.lower(col).like(f"%{safe}%", escape="\\")


@router.get("", response_model=SearchResponse)
async def search(
    ctx: CurrentTenantContext,
    q: str = Query(..., min_length=1, max_length=120),
    limit_per_type: int = Query(DEFAULT_PER_TYPE_LIMIT, ge=1, le=20),
    types: list[str] | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
):
    _, tenant, _ = ctx
    types = set(types or ["customer", "lead", "deal", "quote", "invoice", "task"])

    hits: list[SearchHit] = []

    # ── Customers ────────────────────────────────────────────────────────
    if "customer" in types:
        rows = (
            await db.execute(
                select(Customer)
                .where(
                    Customer.tenant_id == tenant.id,
                    Customer.deleted_at.is_(None),
                    or_(
                        _ilike(Customer.first_name, q),
                        _ilike(func.coalesce(Customer.last_name, ""), q),
                        _ilike(func.coalesce(Customer.email, ""), q),
                        _ilike(func.coalesce(Customer.phone, ""), q),
                    ),
                )
                .order_by(Customer.created_at.desc())
                .limit(limit_per_type)
            )
        ).scalars().all()
        for c in rows:
            full = f"{c.first_name} {c.last_name or ''}".strip()
            hits.append(SearchHit(
                type="customer", id=c.id, label=full,
                sublabel=c.email or c.phone or None,
                url=f"/customers/{c.id}", score=1.0,
            ))

    # ── Leads ────────────────────────────────────────────────────────────
    if "lead" in types:
        rows = (
            await db.execute(
                select(Lead)
                .where(
                    Lead.tenant_id == tenant.id,
                    Lead.deleted_at.is_(None),
                    or_(
                        _ilike(Lead.first_name, q),
                        _ilike(func.coalesce(Lead.last_name, ""), q),
                        _ilike(func.coalesce(Lead.email, ""), q),
                        _ilike(func.coalesce(Lead.phone, ""), q),
                        _ilike(func.coalesce(Lead.service_needed, ""), q),
                    ),
                )
                .order_by(Lead.created_at.desc())
                .limit(limit_per_type)
            )
        ).scalars().all()
        for l in rows:
            full = f"{l.first_name} {l.last_name or ''}".strip()
            hits.append(SearchHit(
                type="lead", id=l.id, label=full,
                sublabel=l.service_needed or l.email or l.phone or None,
                url=f"/leads/{l.id}", score=0.9,
            ))

    # ── Deals ────────────────────────────────────────────────────────────
    if "deal" in types:
        rows = (
            await db.execute(
                select(Deal)
                .where(
                    Deal.tenant_id == tenant.id,
                    Deal.deleted_at.is_(None),
                    or_(_ilike(Deal.title, q), _ilike(func.coalesce(Deal.description, ""), q)),
                )
                .order_by(Deal.created_at.desc())
                .limit(limit_per_type)
            )
        ).scalars().all()
        for d in rows:
            hits.append(SearchHit(
                type="deal", id=d.id, label=d.title,
                sublabel=f"{d.stage} · £{d.value_pence / 100:.2f}",
                url=f"/crm/deals/{d.id}", score=0.85,
            ))

    # ── Quotes ───────────────────────────────────────────────────────────
    if "quote" in types:
        rows = (
            await db.execute(
                select(Quote)
                .where(
                    Quote.tenant_id == tenant.id,
                    or_(_ilike(Quote.quote_number, q), _ilike(Quote.title, q)),
                )
                .order_by(Quote.created_at.desc())
                .limit(limit_per_type)
            )
        ).scalars().all()
        for x in rows:
            hits.append(SearchHit(
                type="quote", id=x.id, label=f"Quote {x.quote_number}",
                sublabel=x.title,
                url=f"/quotes/{x.id}", score=0.8,
            ))

    # ── Invoices ─────────────────────────────────────────────────────────
    if "invoice" in types:
        rows = (
            await db.execute(
                select(Invoice)
                .where(Invoice.tenant_id == tenant.id, _ilike(Invoice.invoice_number, q))
                .order_by(Invoice.created_at.desc())
                .limit(limit_per_type)
            )
        ).scalars().all()
        for x in rows:
            hits.append(SearchHit(
                type="invoice", id=x.id, label=f"Invoice {x.invoice_number}",
                sublabel=getattr(x, "status", None),
                url=f"/invoices/{x.id}", score=0.75,
            ))

    # ── Tasks ────────────────────────────────────────────────────────────
    if "task" in types:
        rows = (
            await db.execute(
                select(Task)
                .where(
                    Task.tenant_id == tenant.id,
                    Task.deleted_at.is_(None),
                    or_(_ilike(Task.title, q), _ilike(func.coalesce(Task.description, ""), q)),
                )
                .order_by(Task.created_at.desc())
                .limit(limit_per_type)
            )
        ).scalars().all()
        for t in rows:
            hits.append(SearchHit(
                type="task", id=t.id, label=t.title,
                sublabel=f"{t.status} · {t.priority}",
                url=f"/tasks/{t.id}", score=0.7,
            ))

    # Aggregate counts for header chips in the UI.
    by_type: dict[str, int] = {}
    for h in hits:
        by_type[h.type] = by_type.get(h.type, 0) + 1

    return SearchResponse(hits=hits, by_type=by_type)
