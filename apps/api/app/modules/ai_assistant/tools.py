"""Tool definitions for the AI assistant.

The assistant can call these tools to read CRM data on behalf of the user.
We expose READ-ONLY tools by default; writes happen through suggested actions
the UI renders, so the human is always in the loop.

Each tool is described in OpenAI/Anthropic-compatible JSON schema so the LLM
can decide when to call it. `execute_tool` dispatches by name.
"""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.crm.models import Customer, Deal
from app.modules.leads.models import Lead
from app.modules.quotes_invoices.models import Invoice, Quote
from app.modules.tasks.models import Task


def _tool_parameters(**properties: dict) -> dict:
    """OpenAI requires object schemas to declare ``required`` (may be empty)."""
    return {"type": "object", "properties": properties, "required": []}


TOOL_SCHEMAS: list[dict] = [
    {
        "type": "function",
        "function": {
            "name": "list_recent_leads",
            "description": "List the most recently received leads (newest first). Use when the user asks about new enquiries.",
            "parameters": _tool_parameters(
                limit={"type": "integer", "minimum": 1, "maximum": 25, "default": 10},
                status={"type": "string", "description": "Filter by lead status (new, contacted, qualified, …)"},
                min_score={"type": "integer", "description": "Only return leads with AI score >= this value"},
            ),
        },
    },
    {
        "type": "function",
        "function": {
            "name": "pipeline_summary",
            "description": "Return a count + total value of deals per pipeline stage. Use when the user asks about the pipeline.",
            "parameters": _tool_parameters(),
        },
    },
    {
        "type": "function",
        "function": {
            "name": "overdue_tasks",
            "description": "List tasks whose due date has passed and that are not done.",
            "parameters": _tool_parameters(
                limit={"type": "integer", "minimum": 1, "maximum": 25, "default": 10},
            ),
        },
    },
    {
        "type": "function",
        "function": {
            "name": "find_customer",
            "description": "Look up customers by name, email, phone, or postcode. Returns the top 5 matches.",
            "parameters": {
                "type": "object",
                "properties": {"query": {"type": "string", "minLength": 1}},
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "outstanding_invoices",
            "description": "List unpaid invoices, optionally filtered to those overdue.",
            "parameters": _tool_parameters(
                limit={"type": "integer", "minimum": 1, "maximum": 25, "default": 10},
                overdue_only={"type": "boolean", "default": False},
            ),
        },
    },
]


# ── Dispatch ─────────────────────────────────────────────────────────────────

async def execute_tool(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    name: str,
    arguments: str | dict,
) -> str:
    """Execute the named tool with the supplied arguments and return JSON output.

    Returned JSON is what we feed back into the LLM as a `tool` message.
    """
    args: dict
    if isinstance(arguments, str):
        try:
            args = json.loads(arguments or "{}")
        except json.JSONDecodeError:
            args = {}
    else:
        args = arguments or {}

    if name == "list_recent_leads":
        return await _list_recent_leads(db, tenant_id, args)
    if name == "pipeline_summary":
        return await _pipeline_summary(db, tenant_id)
    if name == "overdue_tasks":
        return await _overdue_tasks(db, tenant_id, args)
    if name == "find_customer":
        return await _find_customer(db, tenant_id, args)
    if name == "outstanding_invoices":
        return await _outstanding_invoices(db, tenant_id, args)

    return json.dumps({"error": f"unknown tool '{name}'"})


# ── Individual tools ─────────────────────────────────────────────────────────

async def _list_recent_leads(db, tenant_id, args):
    limit = min(25, max(1, int(args.get("limit", 10))))
    status = args.get("status")
    min_score = args.get("min_score")

    q = select(Lead).where(Lead.tenant_id == tenant_id, Lead.deleted_at.is_(None))
    if status:
        q = q.where(Lead.status == status)
    if min_score is not None:
        q = q.where(Lead.score >= int(min_score))
    rows = (await db.execute(q.order_by(desc(Lead.created_at)).limit(limit))).scalars().all()
    return json.dumps({
        "leads": [
            {
                "id": str(l.id),
                "name": f"{l.first_name} {l.last_name or ''}".strip(),
                "service_needed": l.service_needed,
                "score": l.score,
                "score_label": l.score_label,
                "status": l.status,
                "source": l.source,
                "created_at": l.created_at.isoformat() if l.created_at else None,
            }
            for l in rows
        ]
    })


async def _pipeline_summary(db, tenant_id):
    rows = (
        await db.execute(
            select(Deal.stage, func.count(Deal.id), func.coalesce(func.sum(Deal.value_pence), 0))
            .where(Deal.tenant_id == tenant_id, Deal.deleted_at.is_(None))
            .group_by(Deal.stage)
        )
    ).all()
    return json.dumps({
        "pipeline": [
            {"stage": stage, "count": int(count), "value_pence": int(value)}
            for stage, count, value in rows
        ]
    })


async def _overdue_tasks(db, tenant_id, args):
    limit = min(25, max(1, int(args.get("limit", 10))))
    now = datetime.now(timezone.utc)
    rows = (
        await db.execute(
            select(Task)
            .where(
                Task.tenant_id == tenant_id,
                Task.deleted_at.is_(None),
                Task.due_at.is_not(None),
                Task.due_at < now,
                Task.status.notin_(("done", "cancelled")),
            )
            .order_by(Task.due_at.asc())
            .limit(limit)
        )
    ).scalars().all()
    return json.dumps({
        "tasks": [
            {
                "id": str(t.id),
                "title": t.title,
                "status": t.status,
                "priority": t.priority,
                "due_at": t.due_at.isoformat() if t.due_at else None,
                "assigned_user_id": str(t.assigned_user_id) if t.assigned_user_id else None,
            }
            for t in rows
        ]
    })


async def _find_customer(db, tenant_id, args):
    query = (args.get("query") or "").strip().lower()
    if not query:
        return json.dumps({"customers": []})
    like = f"%{query}%"
    rows = (
        await db.execute(
            select(Customer)
            .where(
                Customer.tenant_id == tenant_id,
                Customer.deleted_at.is_(None),
                (
                    func.lower(Customer.first_name).like(like)
                    | func.lower(func.coalesce(Customer.last_name, "")).like(like)
                    | func.lower(func.coalesce(Customer.email, "")).like(like)
                    | func.lower(func.coalesce(Customer.phone, "")).like(like)
                    | func.lower(func.coalesce(Customer.postcode, "")).like(like)
                ),
            )
            .order_by(Customer.created_at.desc())
            .limit(5)
        )
    ).scalars().all()
    return json.dumps({
        "customers": [
            {
                "id": str(c.id),
                "name": f"{c.first_name} {c.last_name or ''}".strip(),
                "email": c.email,
                "phone": c.phone,
                "postcode": c.postcode,
            }
            for c in rows
        ]
    })


async def _outstanding_invoices(db, tenant_id, args):
    from datetime import date as date_cls

    limit = min(25, max(1, int(args.get("limit", 10))))
    overdue_only = bool(args.get("overdue_only", False))
    today = datetime.now(timezone.utc).date()

    q = select(Invoice).where(
        Invoice.tenant_id == tenant_id,
        Invoice.status.in_(("sent", "overdue", "partial")),
    )
    if overdue_only:
        q = q.where(Invoice.due_date < today)
    rows = (
        await db.execute(q.order_by(Invoice.due_date.asc().nullslast()).limit(limit))
    ).scalars().all()

    out = []
    for inv in rows:
        out.append({
            "id": str(inv.id),
            "invoice_number": inv.invoice_number,
            "status": inv.status,
            "total_pence": int(inv.total_pence or 0),
            "due_date": inv.due_date.isoformat() if inv.due_date else None,
        })
    return json.dumps({"invoices": out})
