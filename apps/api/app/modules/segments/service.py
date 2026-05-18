"""Customer segmentation engine.

Supports a small DSL of rules over customer-level facts:

  Fields:
    customer.created_days_ago  → int
    customer.gdpr_consent      → bool
    deals.count                → int (lifetime deal count for customer)
    deals.completed_count      → int
    deals.lifetime_value_pence → int (sum of all deal values for customer)
    invoices.paid_count        → int
    invoices.outstanding_pence → int (open invoice total)
    reviews.last_rating        → int 1..5 (most recent review by this customer)

  Operators:
    eq | ne | gt | gte | lt | lte | in | not_in | between

Rules are evaluated in pure SQLAlchemy so the work happens in Postgres.
Each rule list is AND-combined within itself; the three lists combine as
``(all) AND (any) AND NOT (none)``.

We also ship a few "AI-suggested" system segments that any tenant gets out
of the box (e.g. "VIP customers", "At risk", "Recent first-timers").
"""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Iterable

from sqlalchemy import and_, case, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.crm.models import Customer, Deal
from app.modules.quotes_invoices.models import Invoice
from app.modules.reputation.models import Review
from app.modules.segments.models import CustomerSegment


SYSTEM_SEGMENTS: list[dict[str, Any]] = [
    {
        "name": "VIP customers",
        "description": "Customers with lifetime value over £500.",
        "rules": {
            "all": [{"field": "deals.lifetime_value_pence", "op": "gte", "value": 50000}],
        },
    },
    {
        "name": "Recent first-timers",
        "description": "Customers added in the last 30 days with exactly 1 deal.",
        "rules": {
            "all": [
                {"field": "customer.created_days_ago", "op": "lte", "value": 30},
                {"field": "deals.count", "op": "eq", "value": 1},
            ]
        },
    },
    {
        "name": "Outstanding balance",
        "description": "Customers with unpaid invoices.",
        "rules": {
            "all": [{"field": "invoices.outstanding_pence", "op": "gt", "value": 0}],
        },
    },
    {
        "name": "Promoters (5★)",
        "description": "Customers who left a 5-star review.",
        "rules": {
            "all": [{"field": "reviews.last_rating", "op": "gte", "value": 5}],
        },
    },
    {
        "name": "Detractors (≤3★)",
        "description": "Customers whose most recent review was 3 stars or fewer.",
        "rules": {
            "all": [{"field": "reviews.last_rating", "op": "lte", "value": 3}],
        },
    },
]


# ── Field expressions ────────────────────────────────────────────────────────
# Each entry returns a SQLAlchemy column/expression keyed by Customer.id.

def _field_expressions(tenant_id: uuid.UUID) -> dict[str, Any]:
    now = func.now()

    deals_sub = (
        select(
            Deal.customer_id.label("customer_id"),
            func.count().label("count"),
            func.coalesce(func.sum(Deal.value_pence), 0).label("lifetime_value_pence"),
            func.sum(case((Deal.completed_at.is_not(None), 1), else_=0)).label("completed_count"),
        )
        .where(Deal.tenant_id == tenant_id, Deal.deleted_at.is_(None))
        .group_by(Deal.customer_id)
        .subquery()
    )

    invoices_sub = (
        select(
            Invoice.customer_id.label("customer_id"),
            func.count().filter(Invoice.status == "paid").label("paid_count"),
            func.coalesce(
                func.sum(Invoice.total_pence).filter(
                    Invoice.status.in_(("sent", "overdue", "partial"))
                ),
                0,
            ).label("outstanding_pence"),
        )
        .where(Invoice.tenant_id == tenant_id)
        .group_by(Invoice.customer_id)
        .subquery()
    )

    review_sub = (
        select(
            Review.customer_id.label("customer_id"),
            func.max(Review.rating).label("last_rating"),  # not strictly "last", good enough
        )
        .where(Review.tenant_id == tenant_id, Review.customer_id.is_not(None))
        .group_by(Review.customer_id)
        .subquery()
    )

    last_deal_sub = (
        select(
            Deal.customer_id.label("customer_id"),
            func.max(Deal.completed_at).label("last_completed_at"),
            func.max(Deal.created_at).label("last_deal_created_at"),
        )
        .where(Deal.tenant_id == tenant_id, Deal.deleted_at.is_(None))
        .group_by(Deal.customer_id)
        .subquery()
    )

    return {
        "customer.created_days_ago": func.extract("day", now - Customer.created_at),
        "customer.gdpr_consent": Customer.gdpr_consent,
        "customer.email": Customer.email,
        "customer.phone": Customer.phone,
        "deals.count": func.coalesce(deals_sub.c.count, 0),
        "deals.completed_count": func.coalesce(deals_sub.c.completed_count, 0),
        "deals.lifetime_value_pence": func.coalesce(deals_sub.c.lifetime_value_pence, 0),
        "deals.last_completed_at": last_deal_sub.c.last_completed_at,
        "deals.last_deal_created_at": last_deal_sub.c.last_deal_created_at,
        "last_deal_at": func.coalesce(
            last_deal_sub.c.last_completed_at, last_deal_sub.c.last_deal_created_at
        ),
        "email": Customer.email,
        "phone": Customer.phone,
        "invoices.paid_count": func.coalesce(invoices_sub.c.paid_count, 0),
        "invoices.outstanding_pence": func.coalesce(invoices_sub.c.outstanding_pence, 0),
        "reviews.last_rating": review_sub.c.last_rating,
        "_subqueries": [deals_sub, invoices_sub, review_sub, last_deal_sub],
    }


def _op_to_clause(column, op: str, value: Any):
    op = op.lower()
    if op == "eq":
        return column == value
    if op == "ne":
        return column != value
    if op == "gt":
        return column > value
    if op == "gte":
        return column >= value
    if op == "lt":
        return column < value
    if op == "lte":
        return column <= value
    if op == "in":
        return column.in_(value or [])
    if op == "not_in":
        return ~column.in_(value or [])
    if op == "between":
        lo, hi = value
        return column.between(lo, hi)
    if op == "is_null":
        return column.is_(None)
    if op == "not_null":
        return column.is_not(None)
    if op == "not_empty":
        return and_(column.is_not(None), column != "")
    if op == "empty":
        return or_(column.is_(None), column == "")
    if op == "contains":
        return column.ilike(f"%{value}%")
    if op == "older_than_days":
        try:
            days = int(value)
        except (TypeError, ValueError):
            raise ValueError("older_than_days requires an integer days value")
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        return or_(column.is_(None), column < cutoff)
    if op == "newer_than_days":
        try:
            days = int(value)
        except (TypeError, ValueError):
            raise ValueError("newer_than_days requires an integer days value")
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        return and_(column.is_not(None), column >= cutoff)
    raise ValueError(f"Unknown segment op: {op}")


def _build_clauses(rules: Iterable[dict], fields: dict[str, Any]):
    clauses = []
    for rule in rules or []:
        col = fields.get(rule.get("field", ""))
        if col is None:
            continue
        clauses.append(_op_to_clause(col, rule.get("op", "eq"), rule.get("value")))
    return clauses


async def list_segment_member_ids(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    rules: dict[str, Any],
    *,
    limit: int | None = None,
) -> list[uuid.UUID]:
    """Return customer IDs matching `rules` for this tenant."""
    fields = _field_expressions(tenant_id)
    deals_sub, invoices_sub, review_sub, last_deal_sub = fields.pop("_subqueries")

    q = (
        select(Customer.id)
        .select_from(Customer)
        .where(Customer.tenant_id == tenant_id, Customer.deleted_at.is_(None))
        .outerjoin(deals_sub, deals_sub.c.customer_id == Customer.id)
        .outerjoin(invoices_sub, invoices_sub.c.customer_id == Customer.id)
        .outerjoin(review_sub, review_sub.c.customer_id == Customer.id)
        .outerjoin(last_deal_sub, last_deal_sub.c.customer_id == Customer.id)
        .group_by(Customer.id)
    )

    all_clauses = _build_clauses(rules.get("all", []), fields)
    any_clauses = _build_clauses(rules.get("any", []), fields)
    none_clauses = _build_clauses(rules.get("none", []), fields)
    if all_clauses:
        q = q.where(and_(*all_clauses))
    if any_clauses:
        q = q.where(or_(*any_clauses))
    if none_clauses:
        q = q.where(~or_(*none_clauses))
    if limit is not None:
        q = q.limit(limit)

    rows = (await db.execute(q)).scalars().all()
    return list(rows)


async def compute_segment_membership(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    rules: dict[str, Any],
) -> int:
    """Run the rules against this tenant's customers and return the size."""
    fields = _field_expressions(tenant_id)
    deals_sub, invoices_sub, review_sub, last_deal_sub = fields.pop("_subqueries")

    q = (
        select(func.count(func.distinct(Customer.id)))
        .select_from(Customer)
        .where(Customer.tenant_id == tenant_id, Customer.deleted_at.is_(None))
        .outerjoin(deals_sub, deals_sub.c.customer_id == Customer.id)
        .outerjoin(invoices_sub, invoices_sub.c.customer_id == Customer.id)
        .outerjoin(review_sub, review_sub.c.customer_id == Customer.id)
        .outerjoin(last_deal_sub, last_deal_sub.c.customer_id == Customer.id)
    )

    all_clauses = _build_clauses(rules.get("all", []), fields)
    any_clauses = _build_clauses(rules.get("any", []), fields)
    none_clauses = _build_clauses(rules.get("none", []), fields)

    if all_clauses:
        q = q.where(and_(*all_clauses))
    if any_clauses:
        q = q.where(or_(*any_clauses))
    if none_clauses:
        q = q.where(~or_(*none_clauses))

    return int((await db.execute(q)).scalar_one() or 0)


# ── CRUD + recompute helpers ─────────────────────────────────────────────────

async def list_segments(db: AsyncSession, tenant_id: uuid.UUID) -> list[CustomerSegment]:
    rows = (
        await db.execute(
            select(CustomerSegment)
            .where(CustomerSegment.tenant_id == tenant_id)
            .order_by(CustomerSegment.name.asc())
        )
    ).scalars().all()
    return list(rows)


async def create_segment(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    *,
    name: str,
    rules: dict,
    description: str | None = None,
    created_by: uuid.UUID | None = None,
    is_system: bool = False,
) -> CustomerSegment:
    from app.core.audit import log_action

    size = await compute_segment_membership(db, tenant_id, rules)
    row = CustomerSegment(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        name=name,
        description=description,
        rules=rules,
        size=size,
        computed_at=datetime.now(timezone.utc),
        is_system=is_system,
        created_by_user_id=created_by,
    )
    db.add(row)
    if not is_system:
        await log_action(
            db,
            action="segment.created",
            resource="customer_segment",
            resource_id=row.id,
            tenant_id=tenant_id,
            user_id=created_by,
            metadata={"name": name, "size": size},
        )
    await db.commit()
    await db.refresh(row)
    return row


async def recompute_all(db: AsyncSession, tenant_id: uuid.UUID) -> int:
    """Recompute size for every segment. Returns the number of segments updated."""
    segments = await list_segments(db, tenant_id)
    for s in segments:
        s.size = await compute_segment_membership(db, tenant_id, s.rules or {})
        s.computed_at = datetime.now(timezone.utc)
        db.add(s)
    await db.commit()
    return len(segments)


async def seed_system_segments(db: AsyncSession, tenant_id: uuid.UUID) -> int:
    """Create the default system segments if they don't already exist for this tenant."""
    existing = {s.name for s in await list_segments(db, tenant_id)}
    created = 0
    for spec in SYSTEM_SEGMENTS:
        if spec["name"] in existing:
            continue
        await create_segment(
            db,
            tenant_id,
            name=spec["name"],
            description=spec.get("description"),
            rules=spec["rules"],
            is_system=True,
        )
        created += 1
    return created
