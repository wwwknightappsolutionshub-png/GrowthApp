"""Cross-tenant operational flags for super-admin monitoring.

Aggregates simple heuristics per active tenant so the platform team can spot
stale leads, open conversations, overdue billing, etc., and nudge owners via
in-app notifications.
"""
from __future__ import annotations

import html
import uuid
from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from typing import Literal

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import log_action
from app.core.exceptions import NotFoundException
from app.modules.admin.deletion import active_tenants_filter
from app.modules.auth.models import User
from app.modules.booking.models import Booking
from app.modules.leads.models import Lead
from app.modules.messaging.models import Conversation
from app.modules.notifications.service import create_notification
from app.modules.quotes_invoices.models import Invoice
from app.modules.reputation.models import ReviewRequest
from app.modules.tenants.models import Tenant, TenantMember


@dataclass
class TenantHealthMetrics:
    missed_leads: int  # new leads older than SLA
    missed_messages: int  # unresolved conversations (needs reply)
    missed_calls: int  # missed-call capture rows still "new"
    missed_reviews: int  # review requests sent but not completed
    missed_bookings: int  # past bookings not marked completed/cancelled
    overdue_invoices: int


def _severity(m: TenantHealthMetrics) -> Literal["ok", "warn", "critical"]:
    if m.overdue_invoices > 0 or m.missed_calls > 0:
        return "critical"
    if (
        m.missed_leads
        + m.missed_messages
        + m.missed_reviews
        + m.missed_bookings
        + m.overdue_invoices
    ) > 0:
        return "warn"
    return "ok"


def _flags(m: TenantHealthMetrics) -> list[str]:
    out: list[str] = []
    if m.missed_leads:
        out.append("missed_leads")
    if m.missed_messages:
        out.append("missed_messages")
    if m.missed_calls:
        out.append("missed_calls")
    if m.missed_reviews:
        out.append("missed_reviews")
    if m.missed_bookings:
        out.append("missed_bookings")
    if m.overdue_invoices:
        out.append("overdue_invoices")
    return out


async def snapshot_tenant_health(
    db: AsyncSession,
    *,
    stale_lead_hours: int = 24,
    stale_review_days: int = 7,
) -> list[dict]:
    """Return one row per active tenant with metric counts and derived flags."""
    now = datetime.now(timezone.utc)
    stale_lead_cutoff = now - timedelta(hours=stale_lead_hours)
    stale_review_cutoff = now - timedelta(days=stale_review_days)
    today: date = now.date()

    tenants = (
        await db.execute(
            select(Tenant)
            .where(Tenant.is_active.is_(True), active_tenants_filter())
            .order_by(Tenant.name)
        )
    ).scalars().all()
    if not tenants:
        return []

    tid_list = [t.id for t in tenants]
    z = defaultdict(int)

    # --- missed_leads: status new, not spam, created before cutoff ----------------
    q1 = (
        select(Lead.tenant_id, func.count(Lead.id))
        .where(
            Lead.tenant_id.in_(tid_list),
            Lead.status == "new",
            Lead.is_spam.is_(False),
            Lead.deleted_at.is_(None),
            Lead.created_at < stale_lead_cutoff,
        )
        .group_by(Lead.tenant_id)
    )
    for tid, c in (await db.execute(q1)).all():
        z[tid, "missed_leads"] = int(c)

    # --- missed_calls: auto-created from missed-call handler --------------------
    q2 = (
        select(Lead.tenant_id, func.count(Lead.id))
        .where(
            Lead.tenant_id.in_(tid_list),
            Lead.source == "missed_call",
            Lead.status == "new",
            Lead.deleted_at.is_(None),
        )
        .group_by(Lead.tenant_id)
    )
    for tid, c in (await db.execute(q2)).all():
        z[tid, "missed_calls"] = int(c)

    # --- missed_messages: open conversations -----------------------------------
    q3 = (
        select(Conversation.tenant_id, func.count(Conversation.id))
        .where(
            Conversation.tenant_id.in_(tid_list),
            Conversation.is_resolved.is_(False),
        )
        .group_by(Conversation.tenant_id)
    )
    for tid, c in (await db.execute(q3)).all():
        z[tid, "missed_messages"] = int(c)

    # --- missed_reviews: sent request, no response ------------------------------
    q4 = (
        select(ReviewRequest.tenant_id, func.count(ReviewRequest.id))
        .where(
            ReviewRequest.tenant_id.in_(tid_list),
            ReviewRequest.status == "pending",
            ReviewRequest.sent_at.isnot(None),
            ReviewRequest.responded_at.is_(None),
            ReviewRequest.sent_at < stale_review_cutoff,
        )
        .group_by(ReviewRequest.tenant_id)
    )
    for tid, c in (await db.execute(q4)).all():
        z[tid, "missed_reviews"] = int(c)

    # --- missed_bookings: date passed, still active-ish -------------------------
    q5 = (
        select(Booking.tenant_id, func.count(Booking.id))
        .where(
            Booking.tenant_id.in_(tid_list),
            Booking.booking_date < today,
            Booking.status.notin_(("completed", "cancelled")),
        )
        .group_by(Booking.tenant_id)
    )
    for tid, c in (await db.execute(q5)).all():
        z[tid, "missed_bookings"] = int(c)

    # --- overdue_invoices --------------------------------------------------------
    overdue_cond = or_(
        Invoice.status == "overdue",
        and_(
            Invoice.due_date.isnot(None),
            Invoice.due_date < today,
            Invoice.status.in_(("sent", "partial")),
        ),
    )
    q6 = (
        select(Invoice.tenant_id, func.count(Invoice.id))
        .where(Invoice.tenant_id.in_(tid_list), overdue_cond)
        .group_by(Invoice.tenant_id)
    )
    for tid, c in (await db.execute(q6)).all():
        z[tid, "overdue_invoices"] = int(c)

    rows: list[dict] = []
    for t in tenants:
        m = TenantHealthMetrics(
            missed_leads=z[t.id, "missed_leads"],
            missed_messages=z[t.id, "missed_messages"],
            missed_calls=z[t.id, "missed_calls"],
            missed_reviews=z[t.id, "missed_reviews"],
            missed_bookings=z[t.id, "missed_bookings"],
            overdue_invoices=z[t.id, "overdue_invoices"],
        )
        rows.append(
            {
                "tenant_id": t.id,
                "name": t.name,
                "slug": t.slug,
                "email": t.email,
                "is_active": t.is_active,
                "metrics": {
                    "missed_leads": m.missed_leads,
                    "missed_messages": m.missed_messages,
                    "missed_calls": m.missed_calls,
                    "missed_reviews": m.missed_reviews,
                    "missed_bookings": m.missed_bookings,
                    "overdue_invoices": m.overdue_invoices,
                },
                "flags": _flags(m),
                "severity": _severity(m),
            }
        )

    rows.sort(
        key=lambda r: (
            0 if r["severity"] == "critical" else 1 if r["severity"] == "warn" else 2,
            -sum(r["metrics"].values()),
        )
    )
    return rows


async def send_tenant_action_reminder(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    admin_user_id: uuid.UUID,
    note: str | None = None,
) -> dict:
    """Post a tenant-wide in-app notification + best-effort owner email."""
    from app.adapters.email import get_email_adapter
    from app.adapters.email.base import EmailMessage

    tenant = (await db.execute(select(Tenant).where(Tenant.id == tenant_id))).scalar_one_or_none()
    if not tenant:
        raise NotFoundException("Tenant")

    flags = next(
        (r["flags"] for r in await snapshot_tenant_health(db) if r["tenant_id"] == tenant_id),
        [],
    )
    parts = (
        "Our team noticed items in your workspace that may need attention: "
        + (", ".join(f.replace("_", " ") for f in flags) if flags else "general follow-up")
        + "."
    )
    body_extra = f"\n\nNote from CustomerFlow: {note}" if note else ""
    title = "Action suggested in your CustomerFlow workspace"
    body = parts + body_extra + "\n\nOpen your dashboard to review leads, messages, bookings and billing."

    notif = await create_notification(
        db,
        tenant_id=tenant_id,
        user_id=None,
        kind="admin.nudge",
        title=title,
        body=body.strip(),
        link="/dashboard",
        extra={"flags": flags, "from_superadmin": True},
    )

    owners = (
        await db.execute(
            select(TenantMember).where(
                TenantMember.tenant_id == tenant_id,
                TenantMember.role == "owner",
            )
        )
    ).scalars().all()

    safe_body = html.escape(body)
    emailed = 0
    for mem in owners:
        u = (await db.execute(select(User).where(User.id == mem.user_id))).scalar_one_or_none()
        if not u or not u.email:
            continue
        try:
            await get_email_adapter().send(
                EmailMessage(
                    to=u.email,
                    to_name=u.full_name,
                    subject=f"[CustomerFlow] {title}",
                    html_body=f"<p>Hi {html.escape(u.full_name or 'there')},</p><p>{safe_body.replace(chr(10), '</p><p>')}</p>",
                )
            )
            emailed += 1
        except Exception:
            pass

    await log_action(
        db,
        action="tenant.reminder_sent",
        resource="tenant",
        resource_id=tenant_id,
        user_id=admin_user_id,
        tenant_id=tenant_id,
        metadata={"notification_id": str(notif.id), "flags": flags, "emailed_owners": emailed},
    )
    await db.commit()

    return {"notification_id": str(notif.id), "owners_emailed": emailed, "flags": flags}
