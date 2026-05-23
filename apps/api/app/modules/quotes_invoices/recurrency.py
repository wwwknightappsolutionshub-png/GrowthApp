"""Service renewal / recurrency helpers (reminder-only, not auto-billing)."""
from __future__ import annotations

import uuid
from datetime import date, datetime, timedelta, timezone

from dateutil.relativedelta import relativedelta
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.models import User
from app.modules.crm.models import Customer
from app.modules.quotes_invoices.models import Invoice
from app.modules.tenants.models import Tenant, TenantMember

RECURRENCY_CHOICES = frozenset({"yearly", "bi_yearly", "quarterly", "monthly"})

RECURRENCY_LABELS = {
    "yearly": "Yearly",
    "bi_yearly": "Bi-Yearly",
    "quarterly": "Quarterly",
    "monthly": "Monthly",
}

REMINDER_DAYS_BEFORE = 7


def validate_recurrency(value: str | None) -> str | None:
    if value is None or value == "":
        return None
    v = value.strip().lower().replace("-", "_").replace(" ", "_")
    if v in ("bi_yearly", "biyearly"):
        return "bi_yearly"
    if v not in RECURRENCY_CHOICES:
        raise ValueError(
            f"Invalid recurrency. Choose one of: {', '.join(sorted(RECURRENCY_CHOICES))}"
        )
    return v


def add_recurrency_period(anchor: date, recurrency: str) -> date:
    if recurrency == "monthly":
        return anchor + relativedelta(months=1)
    if recurrency == "quarterly":
        return anchor + relativedelta(months=3)
    if recurrency == "bi_yearly":
        return anchor + relativedelta(months=6)
    if recurrency == "yearly":
        return anchor + relativedelta(years=1)
    raise ValueError(f"Unknown recurrency: {recurrency}")


def renewal_anchor_date(inv: Invoice) -> date:
    if inv.paid_at:
        return inv.paid_at.date()
    if inv.due_date:
        return inv.due_date
    return date.today()


def apply_invoice_renewal_schedule(inv: Invoice) -> None:
    """Set renewal_due_date from recurrency; clear reminder flag when date changes."""
    if not inv.recurrency:
        inv.renewal_due_date = None
        inv.renewal_reminder_sent_at = None
        return
    anchor = renewal_anchor_date(inv)
    new_due = add_recurrency_period(anchor, inv.recurrency)
    if inv.renewal_due_date != new_due:
        inv.renewal_reminder_sent_at = None
    inv.renewal_due_date = new_due


async def sync_customer_service_renewal(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    inv: Invoice,
) -> None:
    customer = (
        await db.execute(
            select(Customer).where(
                Customer.id == inv.customer_id,
                Customer.tenant_id == tenant_id,
                Customer.deleted_at.is_(None),
            )
        )
    ).scalar_one_or_none()
    if not customer:
        return
    if inv.recurrency and inv.renewal_due_date:
        customer.service_recurrency = inv.recurrency
        customer.service_renewal_date = inv.renewal_due_date
        customer.service_renewal_invoice_id = inv.id
    db.add(customer)


async def _tenant_owner_email(db: AsyncSession, tenant_id: uuid.UUID) -> tuple[str | None, str]:
    tenant = (await db.execute(select(Tenant).where(Tenant.id == tenant_id))).scalar_one_or_none()
    if not tenant:
        return None, "Your business"
    owner = (
        await db.execute(
            select(User)
            .join(TenantMember, TenantMember.user_id == User.id)
            .where(TenantMember.tenant_id == tenant_id, TenantMember.role == "owner")
            .limit(1)
        )
    ).scalar_one_or_none()
    if owner and owner.email:
        return owner.email, tenant.name
    if tenant.email:
        return tenant.email, tenant.name
    return None, tenant.name


async def sweep_service_renewal_reminders(db: AsyncSession) -> int:
    """Email tenant owners 7 days before a customer's service renewal date."""
    remind_on = date.today() + timedelta(days=REMINDER_DAYS_BEFORE)
    sent = 0

    rows = (
        await db.execute(
            select(Invoice, Customer)
            .join(Customer, Customer.id == Invoice.customer_id)
            .where(
                Invoice.recurrency.is_not(None),
                Invoice.renewal_due_date == remind_on,
                Invoice.renewal_reminder_sent_at.is_(None),
                Invoice.status.in_(("paid", "sent", "partial", "viewed")),
            )
        )
    ).all()

    from app.core.config import settings
    from app.templates.renderer import render_email
    from app.workers.queue import enqueue

    frontend = settings.FRONTEND_URL.rstrip("/")

    for inv, customer in rows:
        to_email, business_name = await _tenant_owner_email(db, inv.tenant_id)
        if not to_email:
            continue

        customer_name = f"{customer.first_name} {customer.last_name or ''}".strip()
        label = RECURRENCY_LABELS.get(inv.recurrency or "", inv.recurrency or "")

        html = render_email(
            "emails/service_renewal_reminder.html",
            {
                "subject": f"Renewal in {REMINDER_DAYS_BEFORE} days — {customer_name}",
                "business_name": business_name,
                "customer_name": customer_name,
                "invoice_number": inv.invoice_number,
                "invoice_title": inv.title,
                "recurrency_label": label,
                "renewal_date": inv.renewal_due_date.isoformat() if inv.renewal_due_date else "",
                "days_until": REMINDER_DAYS_BEFORE,
                "customer_url": f"{frontend}/dashboard/crm/customers/{customer.id}",
                "invoices_url": f"{frontend}/dashboard/invoices",
            },
        )
        await enqueue(
            "send_email_task",
            to=to_email,
            subject=f"Service renewal in {REMINDER_DAYS_BEFORE} days: {customer_name}",
            html=html,
            tenant_id=str(inv.tenant_id),
        )
        inv.renewal_reminder_sent_at = datetime.now(timezone.utc)
        db.add(inv)
        sent += 1

    if sent:
        await db.commit()
    return sent
