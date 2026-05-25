from __future__ import annotations

import csv
import io
import logging
import uuid
from datetime import date, datetime, timedelta, timezone
from typing import Any

from dateutil.relativedelta import relativedelta
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.audit import log_action
from app.core.config import settings
from app.core.exceptions import BadRequestException, NotFoundException
from app.modules.accounting.entitlement import tenant_has_accounting
from app.modules.accounting.models import (
    FEATURE_ACCOUNTING,
    Expense,
    RecurringInvoiceSchedule,
    TenantAccountingSettings,
    TenantAddon,
)
from app.modules.accounting.schemas import (
    AccountingSettingsUpdate,
    ExpenseCreate,
    RecurringLineItem,
    RecurringScheduleCreate,
)
from app.modules.crm.models import Customer, Deal
from app.modules.quotes_invoices.models import Invoice, Payment, Quote
from app.modules.quotes_invoices.schemas import InvoiceCreate, QuoteItemIn
from app.modules.quotes_invoices import service as qi_service
from app.modules.tenants.models import Tenant

logger = logging.getLogger(__name__)


async def get_status(db: AsyncSession, tenant_id: uuid.UUID) -> dict[str, Any]:
    row = (
        await db.execute(
            select(TenantAddon).where(
                TenantAddon.tenant_id == tenant_id,
                TenantAddon.feature_code == FEATURE_ACCOUNTING,
            )
        )
    ).scalar_one_or_none()
    active = await tenant_has_accounting(db, tenant_id)
    return {
        "has_accounting": active,
        "feature_code": FEATURE_ACCOUNTING,
        "status": row.status if row else None,
        "expires_at": row.expires_at if row else None,
    }


async def grant_addon(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    *,
    granted_by: uuid.UUID | None = None,
    expires_at: datetime | None = None,
) -> TenantAddon:
    row = (
        await db.execute(
            select(TenantAddon).where(
                TenantAddon.tenant_id == tenant_id,
                TenantAddon.feature_code == FEATURE_ACCOUNTING,
            )
        )
    ).scalar_one_or_none()
    now = datetime.now(timezone.utc)
    if row:
        row.status = "active"
        row.granted_by = granted_by
        row.granted_at = now
        row.expires_at = expires_at
    else:
        row = TenantAddon(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            feature_code=FEATURE_ACCOUNTING,
            status="active",
            granted_by=granted_by,
            granted_at=now,
            expires_at=expires_at,
        )
        db.add(row)
    await _ensure_settings(db, tenant_id)
    await db.commit()
    await db.refresh(row)
    return row


async def revoke_addon(db: AsyncSession, tenant_id: uuid.UUID) -> None:
    row = (
        await db.execute(
            select(TenantAddon).where(
                TenantAddon.tenant_id == tenant_id,
                TenantAddon.feature_code == FEATURE_ACCOUNTING,
            )
        )
    ).scalar_one_or_none()
    if row:
        row.status = "canceled"
        await db.commit()


async def create_accounting_checkout(
    db: AsyncSession,
    tenant: Tenant,
    *,
    success_url: str,
    cancel_url: str,
) -> str:
    if not settings.STRIPE_PRICE_ACCOUNTING:
        raise BadRequestException("Accounting add-on is not configured for billing yet. Contact support.")

    from app.adapters import get_payment_adapter
    from app.modules.billing.models import Subscription

    sub = (
        await db.execute(select(Subscription).where(Subscription.tenant_id == tenant.id))
    ).scalar_one_or_none()

    adapter = get_payment_adapter()
    if sub and sub.stripe_customer_id:
        customer_id = sub.stripe_customer_id
    else:
        customer_id = await adapter.create_customer(
            email=tenant.email or "",
            name=tenant.name,
            metadata={"tenant_id": str(tenant.id)},
        )

    import stripe

    stripe.api_key = settings.STRIPE_SECRET_KEY
    session = stripe.checkout.Session.create(
        customer=customer_id,
        payment_method_types=["card"],
        line_items=[{"price": settings.STRIPE_PRICE_ACCOUNTING, "quantity": 1}],
        mode="subscription",
        success_url=success_url,
        cancel_url=cancel_url,
        metadata={"tenant_id": str(tenant.id), "feature_code": FEATURE_ACCOUNTING},
    )
    return session.url


async def activate_from_checkout_metadata(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    stripe_subscription_item_id: str | None = None,
    checkout_session_id: str | None = None,
) -> None:
    row = (
        await db.execute(
            select(TenantAddon).where(
                TenantAddon.tenant_id == tenant_id,
                TenantAddon.feature_code == FEATURE_ACCOUNTING,
            )
        )
    ).scalar_one_or_none()
    now = datetime.now(timezone.utc)
    if row:
        row.status = "active"
        row.stripe_subscription_item_id = stripe_subscription_item_id or row.stripe_subscription_item_id
        row.stripe_checkout_session_id = checkout_session_id or row.stripe_checkout_session_id
        row.granted_at = now
    else:
        db.add(
            TenantAddon(
                id=uuid.uuid4(),
                tenant_id=tenant_id,
                feature_code=FEATURE_ACCOUNTING,
                status="active",
                stripe_subscription_item_id=stripe_subscription_item_id,
                stripe_checkout_session_id=checkout_session_id,
                granted_at=now,
            )
        )
    await _ensure_settings(db, tenant_id)
    await db.commit()


async def _ensure_settings(db: AsyncSession, tenant_id: uuid.UUID) -> TenantAccountingSettings:
    row = (
        await db.execute(
            select(TenantAccountingSettings).where(TenantAccountingSettings.tenant_id == tenant_id)
        )
    ).scalar_one_or_none()
    if not row:
        row = TenantAccountingSettings(tenant_id=tenant_id)
        db.add(row)
        await db.flush()
    return row


async def get_settings(db: AsyncSession, tenant_id: uuid.UUID) -> TenantAccountingSettings:
    return await _ensure_settings(db, tenant_id)


async def update_settings(
    db: AsyncSession, tenant_id: uuid.UUID, data: AccountingSettingsUpdate
) -> TenantAccountingSettings:
    row = await _ensure_settings(db, tenant_id)
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(row, field, value)
    await db.commit()
    await db.refresh(row)
    return row


def _vat_on_amount(amount_pence: int, vat_rate: int) -> int:
    return int(amount_pence * vat_rate / 100)


async def create_expense(db: AsyncSession, tenant_id: uuid.UUID, data: ExpenseCreate) -> Expense:
    vat_pence = _vat_on_amount(data.amount_pence, data.vat_rate)
    exp = Expense(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        description=data.description,
        amount_pence=data.amount_pence,
        vat_rate=data.vat_rate,
        vat_pence=vat_pence,
        category=data.category,
        expense_date=data.expense_date,
        customer_id=data.customer_id,
        deal_id=data.deal_id,
        booking_id=data.booking_id,
        receipt_url=data.receipt_url,
        notes=data.notes,
    )
    db.add(exp)
    await db.commit()
    await db.refresh(exp)
    return exp


async def list_expenses(db: AsyncSession, tenant_id: uuid.UUID, page: int = 1, page_size: int = 50) -> tuple[list[Expense], int]:
    q = select(Expense).where(Expense.tenant_id == tenant_id)
    total = (await db.execute(select(func.count()).select_from(q.subquery()))).scalar_one()
    items = (
        await db.execute(
            q.order_by(Expense.expense_date.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
    ).scalars().all()
    return list(items), int(total)


async def delete_expense(db: AsyncSession, tenant_id: uuid.UUID, expense_id: uuid.UUID) -> None:
    exp = (
        await db.execute(select(Expense).where(Expense.id == expense_id, Expense.tenant_id == tenant_id))
    ).scalar_one_or_none()
    if not exp:
        raise NotFoundException("Expense")
    await db.delete(exp)
    await db.commit()


async def create_recurring(
    db: AsyncSession, tenant_id: uuid.UUID, data: RecurringScheduleCreate
) -> RecurringInvoiceSchedule:
    sched = RecurringInvoiceSchedule(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        customer_id=data.customer_id,
        deal_id=data.deal_id,
        title=data.title,
        notes=data.notes,
        interval_unit=data.interval_unit,
        interval_count=data.interval_count,
        next_run_at=data.next_run_at,
        line_items=[i.model_dump() for i in data.line_items],
        auto_charge=data.auto_charge,
        auto_send=data.auto_send,
    )
    db.add(sched)
    await db.commit()
    await db.refresh(sched)
    return sched


async def list_recurring(db: AsyncSession, tenant_id: uuid.UUID) -> list[RecurringInvoiceSchedule]:
    return list(
        (
            await db.execute(
                select(RecurringInvoiceSchedule)
                .where(RecurringInvoiceSchedule.tenant_id == tenant_id)
                .order_by(RecurringInvoiceSchedule.next_run_at)
            )
        ).scalars().all()
    )


async def delete_recurring(db: AsyncSession, tenant_id: uuid.UUID, schedule_id: uuid.UUID) -> None:
    row = (
        await db.execute(
            select(RecurringInvoiceSchedule).where(
                RecurringInvoiceSchedule.id == schedule_id,
                RecurringInvoiceSchedule.tenant_id == tenant_id,
            )
        )
    ).scalar_one_or_none()
    if not row:
        raise NotFoundException("Recurring schedule")
    await db.delete(row)
    await db.commit()


def _next_run(d: date, unit: str, count: int) -> date:
    if unit == "weekly":
        return d + timedelta(weeks=count)
    if unit == "yearly":
        return d + relativedelta(years=count)
    return d + relativedelta(months=count)


async def send_invoice(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    invoice_id: uuid.UUID,
    *,
    actor_user_id: uuid.UUID | None = None,
) -> Invoice:
    await qi_service.send_invoice(db, tenant_id, invoice_id, actor_user_id=actor_user_id)
    await enqueue(
        "trigger_automation_for_event",
        tenant_id=str(tenant_id),
        event="invoice_sent",
        entity_id=str(invoice_id),
        entity_type="invoice",
    )
    return await qi_service.get_invoice(db, tenant_id, invoice_id)


async def mark_quote_viewed(db: AsyncSession, quote: Quote) -> None:
    if quote.viewed_at:
        return
    quote.viewed_at = datetime.now(timezone.utc)
    if quote.status == "sent":
        quote.status = "viewed"
    await db.commit()


async def mark_invoice_viewed(db: AsyncSession, inv: Invoice) -> None:
    if inv.viewed_at:
        return
    inv.viewed_at = datetime.now(timezone.utc)
    if inv.status == "sent":
        inv.status = "viewed"
    await db.commit()


async def get_public_invoice(db: AsyncSession, public_token: str) -> dict[str, Any]:
    inv = (
        await db.execute(
            select(Invoice).options(selectinload(Invoice.items)).where(Invoice.public_token == public_token)
        )
    ).scalar_one_or_none()
    if not inv:
        raise NotFoundException("Invoice")
    await mark_invoice_viewed(db, inv)
    tenant = (await db.execute(select(Tenant).where(Tenant.id == inv.tenant_id))).scalar_one()
    return {
        "id": str(inv.id),
        "invoice_number": inv.invoice_number,
        "title": inv.title,
        "status": inv.status,
        "subtotal_pence": inv.subtotal_pence,
        "vat_pence": inv.vat_pence,
        "total_pence": inv.total_pence,
        "paid_pence": inv.paid_pence,
        "due_date": inv.due_date,
        "currency": inv.currency,
        "items": inv.items,
        "business_name": tenant.name,
        "logo_url": tenant.logo_url,
        "primary_color": tenant.primary_color,
        "stripe_payment_link": inv.stripe_payment_link,
    }


async def create_invoice_payment_intent(db: AsyncSession, public_token: str) -> dict[str, str]:
    inv = (
        await db.execute(select(Invoice).where(Invoice.public_token == public_token))
    ).scalar_one_or_none()
    if not inv:
        raise NotFoundException("Invoice")
    if inv.status == "paid":
        raise BadRequestException("Invoice is already paid")

    amount_due = max(0, inv.total_pence - inv.paid_pence)
    if amount_due <= 0:
        raise BadRequestException("Nothing to pay on this invoice")

    customer = (
        await db.execute(select(Customer).where(Customer.id == inv.customer_id))
    ).scalar_one_or_none()

    from app.adapters import get_payment_adapter

    adapter = get_payment_adapter()
    result = await adapter.create_payment_intent(
        amount_pence=amount_due,
        currency="gbp",
        metadata={
            "tenant_id": str(inv.tenant_id),
            "invoice_id": str(inv.id),
            "purpose": "invoice_payment",
        },
        customer_email=customer.email if customer else None,
    )
    return result


async def apply_invoice_payment(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    invoice_id: uuid.UUID,
    amount_pence: int,
    method: str = "stripe",
    stripe_payment_intent_id: str | None = None,
) -> Invoice:
    inv = await qi_service.get_invoice(db, tenant_id, invoice_id)
    if inv.status == "paid":
        return inv

    inv.paid_pence = min(inv.total_pence, inv.paid_pence + amount_pence)
    if inv.paid_pence >= inv.total_pence:
        inv.status = "paid"
        inv.paid_at = datetime.now(timezone.utc)

    db.add(
        Payment(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            invoice_id=invoice_id,
            amount_pence=amount_pence,
            method=method,
            stripe_payment_intent_id=stripe_payment_intent_id,
            status="succeeded",
        )
    )
    await db.commit()
    await db.refresh(inv)

    return inv


async def auto_invoice_from_booking(db: AsyncSession, tenant_id: uuid.UUID, booking) -> Invoice | None:
    if not await tenant_has_accounting(db, tenant_id):
        return None
    settings_row = await _ensure_settings(db, tenant_id)
    if not settings_row.auto_invoice_on_booking_complete:
        return None

    existing = (
        await db.execute(
            select(Invoice).where(Invoice.tenant_id == tenant_id, Invoice.booking_id == booking.id)
        )
    ).scalar_one_or_none()
    if existing:
        return existing

    amount = booking.prepaid_pence or booking.deposit_paid_pence or booking.service_fee_pence
    if amount <= 0:
        amount = 0
        desc = booking.service_description or f"Booking on {booking.booking_date}"
    else:
        desc = booking.service_description or f"Service — {booking.booking_date}"

    customer_id = booking.customer_id
    if not customer_id and booking.customer_email:
        cust = (
            await db.execute(
                select(Customer).where(
                    Customer.tenant_id == tenant_id,
                    Customer.email == booking.customer_email,
                    Customer.deleted_at.is_(None),
                )
            )
        ).scalar_one_or_none()
        customer_id = cust.id if cust else None

    if not customer_id:
        cust = Customer(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            first_name=booking.customer_name.split()[0] if booking.customer_name else "Customer",
            last_name=" ".join(booking.customer_name.split()[1:]) if booking.customer_name else None,
            email=booking.customer_email,
            phone=booking.customer_phone,
        )
        db.add(cust)
        await db.flush()
        customer_id = cust.id

    items = [QuoteItemIn(description=desc, quantity=1, unit_price_pence=max(amount, 0), vat_rate=20)]
    if max(amount, 0) == 0:
        items = [QuoteItemIn(description=desc, quantity=1, unit_price_pence=0, vat_rate=0)]

    inv = await qi_service.create_invoice(
        db,
        tenant_id,
        InvoiceCreate(
            customer_id=customer_id,
            deal_id=booking.deal_id,
            title=desc[:255],
            items=items,
            due_date=date.today() + timedelta(days=14),
        ),
    )
    inv.booking_id = booking.id
    await db.commit()
    return await qi_service.get_invoice(db, tenant_id, inv.id)


async def move_deal_on_quote_accept(db: AsyncSession, tenant_id: uuid.UUID, quote: Quote) -> None:
    if not quote.deal_id:
        return
    deal = (
        await db.execute(select(Deal).where(Deal.id == quote.deal_id, Deal.tenant_id == tenant_id))
    ).scalar_one_or_none()
    if not deal:
        return
    if deal.stage in ("Completed", "Lost"):
        return
    deal.stage = "Quoted"
    await db.commit()


async def customer_financials(db: AsyncSession, tenant_id: uuid.UUID, customer_id: uuid.UUID) -> dict[str, Any]:
    cust = (
        await db.execute(
            select(Customer).where(Customer.id == customer_id, Customer.tenant_id == tenant_id)
        )
    ).scalar_one_or_none()
    if not cust:
        raise NotFoundException("Customer")

    invoices = list(
        (
            await db.execute(
                select(Invoice)
                .where(Invoice.tenant_id == tenant_id, Invoice.customer_id == customer_id)
                .order_by(Invoice.created_at.desc())
            )
        ).scalars().all()
    )
    payments = list(
        (
            await db.execute(
                select(Payment)
                .where(Payment.tenant_id == tenant_id)
                .join(Invoice, Invoice.id == Payment.invoice_id)
                .where(Invoice.customer_id == customer_id)
                .order_by(Payment.created_at.desc())
            )
        ).scalars().all()
    )
    outstanding = sum(max(0, i.total_pence - i.paid_pence) for i in invoices if i.status not in ("paid", "draft"))
    lifetime = sum(p.amount_pence for p in payments if p.status == "succeeded")

    return {
        "customer_id": customer_id,
        "outstanding_pence": outstanding,
        "lifetime_paid_pence": lifetime,
        "invoice_count": len(invoices),
        "invoices": [
            {
                "id": str(i.id),
                "invoice_number": i.invoice_number,
                "title": i.title,
                "status": i.status,
                "total_pence": i.total_pence,
                "paid_pence": i.paid_pence,
                "due_date": i.due_date.isoformat() if i.due_date else None,
            }
            for i in invoices
        ],
        "payments": [
            {
                "id": str(p.id),
                "amount_pence": p.amount_pence,
                "method": p.method,
                "created_at": p.created_at.isoformat(),
            }
            for p in payments
        ],
    }


async def tax_summary(db: AsyncSession, tenant_id: uuid.UUID, year: int) -> dict[str, Any]:
    settings_row = await _ensure_settings(db, tenant_id)
    start = date(year, 1, 1)
    end = date(year, 12, 31)

    income = int(
        (
            await db.execute(
                select(func.coalesce(func.sum(Payment.amount_pence), 0)).where(
                    Payment.tenant_id == tenant_id,
                    Payment.status == "succeeded",
                    func.date(Payment.created_at) >= start,
                    func.date(Payment.created_at) <= end,
                )
            )
        ).scalar_one()
    )
    expenses = int(
        (
            await db.execute(
                select(func.coalesce(func.sum(Expense.amount_pence), 0)).where(
                    Expense.tenant_id == tenant_id,
                    Expense.expense_date >= start,
                    Expense.expense_date <= end,
                )
            )
        ).scalar_one()
    )
    vat_collected = int(
        (
            await db.execute(
                select(func.coalesce(func.sum(Invoice.vat_pence), 0)).where(
                    Invoice.tenant_id == tenant_id,
                    Invoice.status == "paid",
                    func.date(Invoice.paid_at) >= start,
                    func.date(Invoice.paid_at) <= end,
                )
            )
        ).scalar_one()
    )
    vat_expenses = int(
        (
            await db.execute(
                select(func.coalesce(func.sum(Expense.vat_pence), 0)).where(
                    Expense.tenant_id == tenant_id,
                    Expense.expense_date >= start,
                    Expense.expense_date <= end,
                )
            )
        ).scalar_one()
    )

    return {
        "year": year,
        "income_pence": income,
        "expenses_pence": expenses,
        "vat_collected_pence": vat_collected,
        "vat_on_expenses_pence": vat_expenses,
        "net_pence": income - expenses,
        "vat_scheme": settings_row.vat_scheme,
    }


async def export_accountant_csv(db: AsyncSession, tenant_id: uuid.UUID, year: int) -> str:
    start = date(year, 1, 1)
    end = date(year, 12, 31)
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["type", "date", "reference", "description", "amount_gbp", "vat_gbp", "status"])

    invoices = (
        await db.execute(
            select(Invoice).where(
                Invoice.tenant_id == tenant_id,
                func.date(Invoice.created_at) >= start,
                func.date(Invoice.created_at) <= end,
            )
        )
    ).scalars().all()
    for inv in invoices:
        w.writerow(
            [
                "invoice",
                inv.created_at.date().isoformat(),
                inv.invoice_number,
                inv.title,
                f"{inv.total_pence / 100:.2f}",
                f"{inv.vat_pence / 100:.2f}",
                inv.status,
            ]
        )

    payments = (
        await db.execute(
            select(Payment).where(
                Payment.tenant_id == tenant_id,
                Payment.status == "succeeded",
                func.date(Payment.created_at) >= start,
                func.date(Payment.created_at) <= end,
            )
        )
    ).scalars().all()
    for p in payments:
        w.writerow(
            [
                "payment",
                p.created_at.date().isoformat(),
                str(p.id),
                p.method,
                f"{p.amount_pence / 100:.2f}",
                "",
                p.status,
            ]
        )

    exps = (
        await db.execute(
            select(Expense).where(
                Expense.tenant_id == tenant_id,
                Expense.expense_date >= start,
                Expense.expense_date <= end,
            )
        )
    ).scalars().all()
    for e in exps:
        w.writerow(
            [
                "expense",
                e.expense_date.isoformat(),
                str(e.id),
                e.description,
                f"{e.amount_pence / 100:.2f}",
                f"{e.vat_pence / 100:.2f}",
                e.category,
            ]
        )

    return buf.getvalue()


async def run_due_recurring(db: AsyncSession) -> int:
    today = date.today()
    due = (
        await db.execute(
            select(RecurringInvoiceSchedule).where(
                RecurringInvoiceSchedule.is_active == True,  # noqa: E712
                RecurringInvoiceSchedule.next_run_at <= today,
            )
        )
    ).scalars().all()
    count = 0
    for sched in due:
        if not await tenant_has_accounting(db, sched.tenant_id):
            continue
        items = [
            QuoteItemIn(
                description=line.get("description", "Service"),
                quantity=int(line.get("quantity", 1)),
                unit_price_pence=int(line.get("unit_price_pence", 0)),
                vat_rate=int(line.get("vat_rate", 20)),
            )
            for line in (sched.line_items or [])
        ]
        if not items:
            items = [QuoteItemIn(description=sched.title, quantity=1, unit_price_pence=0, vat_rate=20)]

        inv = await qi_service.create_invoice(
            db,
            sched.tenant_id,
            InvoiceCreate(
                customer_id=sched.customer_id,
                deal_id=sched.deal_id,
                title=sched.title,
                notes=sched.notes,
                items=items,
                due_date=today + timedelta(days=14),
            ),
        )
        if sched.auto_send:
            try:
                await send_invoice(db, sched.tenant_id, inv.id)
            except Exception:
                logger.exception("recurring send failed schedule=%s", sched.id)

        sched.next_run_at = _next_run(sched.next_run_at, sched.interval_unit, sched.interval_count)
        count += 1
    await db.commit()
    return count


async def sweep_overdue_and_reminders(db: AsyncSession) -> int:
    today = date.today()
    sent = 0
    rows = (
        await db.execute(
            select(Invoice, TenantAccountingSettings)
            .join(
                TenantAccountingSettings,
                TenantAccountingSettings.tenant_id == Invoice.tenant_id,
                isouter=True,
            )
            .where(
                Invoice.status.in_(("sent", "viewed", "partial", "overdue")),
                Invoice.due_date.is_not(None),
                Invoice.due_date < today,
            )
        )
    ).all()

    for inv, sett in rows:
        if not await tenant_has_accounting(db, inv.tenant_id):
            continue
        if inv.status != "overdue":
            inv.status = "overdue"
            sent += 1

        reminder_days = (sett.reminder_days if sett else None) or [7, 14]
        if not inv.due_date:
            continue
        days_overdue = (today - inv.due_date).days
        if days_overdue not in reminder_days:
            continue
        if inv.last_reminder_at and inv.last_reminder_at.date() == today:
            continue

        tenant = (await db.execute(select(Tenant).where(Tenant.id == inv.tenant_id))).scalar_one()
        customer = (
            await db.execute(select(Customer).where(Customer.id == inv.customer_id))
        ).scalar_one_or_none()
        if customer and customer.email:
            from app.templates.renderer import render_email
            from app.workers.queue import enqueue

            html = render_email(
                "emails/invoice_overdue.html",
                {
                    "subject": f"Reminder: invoice {inv.invoice_number}",
                    "customer_name": customer.first_name or "there",
                    "business_name": tenant.name,
                    "invoice_number": inv.invoice_number,
                    "total_pence": inv.total_pence,
                    "days_overdue": days_overdue,
                    "stripe_payment_link": inv.stripe_payment_link,
                },
            )
            await enqueue(
                "send_email_task",
                to=customer.email,
                subject=f"Reminder: invoice {inv.invoice_number}",
                html=html,
                tenant_id=str(inv.tenant_id),
            )
            inv.last_reminder_at = datetime.now(timezone.utc)
            sent += 1

    await db.commit()
    return sent
