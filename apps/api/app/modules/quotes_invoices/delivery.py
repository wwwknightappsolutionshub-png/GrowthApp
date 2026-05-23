"""Email delivery for quotes and invoices (available to all tenants)."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import log_action
from app.core.config import settings
from app.core.exceptions import NotFoundException
from app.modules.crm.models import Customer
from app.modules.quotes_invoices.models import Invoice, Quote
from app.modules.tenants.models import Tenant


def _quote_public_url(public_token: str) -> str:
    base = settings.FRONTEND_URL.rstrip("/")
    return f"{base}/quote/{public_token}"


async def deliver_quote_email(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    quote: Quote,
    *,
    actor_user_id: uuid.UUID | None = None,
) -> None:
    tenant = (await db.execute(select(Tenant).where(Tenant.id == tenant_id))).scalar_one()
    customer = (
        await db.execute(
            select(Customer).where(Customer.id == quote.customer_id, Customer.tenant_id == tenant_id)
        )
    ).scalar_one_or_none()
    if not customer or not customer.email:
        return

    from app.templates.renderer import render_quote_sent
    from app.workers.queue import enqueue

    line_items = [
        {
            "description": i.description,
            "quantity": i.quantity,
            "unit_price_pence": i.unit_price_pence,
            "line_total_pence": i.line_total_pence,
        }
        for i in quote.items
    ]
    html = render_quote_sent(
        customer_name=customer.first_name or "there",
        business_name=tenant.name,
        quote_number=quote.quote_number,
        quote_title=quote.title,
        quote_url=_quote_public_url(quote.public_token),
        subtotal_pence=quote.subtotal_pence,
        vat_pence=quote.vat_pence,
        total_pence=quote.total_pence,
        valid_until=quote.valid_until.isoformat() if quote.valid_until else None,
        notes=quote.notes,
        line_items=line_items,
        business_phone=tenant.phone,
    )
    await enqueue(
        "send_email_task",
        to=customer.email,
        subject=f"Quote {quote.quote_number} from {tenant.name}",
        html=html,
        tenant_id=str(tenant_id),
    )
    await log_action(
        db,
        action="quote.emailed",
        resource="quote",
        resource_id=quote.id,
        tenant_id=tenant_id,
        user_id=actor_user_id,
        metadata={"to": customer.email},
    )


async def deliver_invoice_email(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    inv: Invoice,
    *,
    actor_user_id: uuid.UUID | None = None,
) -> Invoice:
    tenant = (await db.execute(select(Tenant).where(Tenant.id == tenant_id))).scalar_one()
    customer = (
        await db.execute(
            select(Customer).where(Customer.id == inv.customer_id, Customer.tenant_id == tenant_id)
        )
    ).scalar_one_or_none()
    if not customer:
        raise NotFoundException("Customer")

    amount_due = max(0, inv.total_pence - inv.paid_pence)
    if amount_due > 0 and not inv.stripe_payment_link:
        from app.adapters import get_payment_adapter

        adapter = get_payment_adapter()
        link = await adapter.create_payment_link(
            amount_pence=amount_due,
            description=f"{inv.invoice_number} — {inv.title}",
            metadata={"tenant_id": str(tenant_id), "invoice_id": str(inv.id)},
        )
        inv.stripe_payment_link = link.url

    now = datetime.now(timezone.utc)
    inv.status = "sent" if inv.status == "draft" else inv.status
    inv.sent_at = inv.sent_at or now
    await db.flush()

    if customer.email:
        from app.templates.renderer import render_invoice_sent
        from app.workers.queue import enqueue

        html = render_invoice_sent(
            customer_name=customer.first_name or "there",
            business_name=tenant.name,
            invoice_number=inv.invoice_number,
            invoice_title=inv.title,
            subtotal_pence=inv.subtotal_pence,
            vat_pence=inv.vat_pence,
            total_pence=inv.total_pence,
            due_date=inv.due_date.isoformat() if inv.due_date else None,
            notes=inv.notes,
            stripe_payment_link=inv.stripe_payment_link,
            business_phone=tenant.phone,
            business_email=tenant.email,
        )
        await enqueue(
            "send_email_task",
            to=customer.email,
            subject=f"Invoice {inv.invoice_number} from {tenant.name}",
            html=html,
            tenant_id=str(tenant_id),
        )

    await log_action(
        db,
        action="invoice.sent",
        resource="invoice",
        resource_id=inv.id,
        tenant_id=tenant_id,
        user_id=actor_user_id,
        metadata={"invoice_number": inv.invoice_number},
    )
    await db.commit()
    return inv
