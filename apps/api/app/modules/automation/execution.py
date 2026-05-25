"""Resolve automation entities to contacts and execute send steps."""
from __future__ import annotations

import logging
import os
import uuid
from dataclasses import dataclass, field

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters import get_email_adapter, get_sms_adapter
from app.adapters.email.base import EmailMessage
from app.adapters.sms.base import SMSMessage
from app.core.config import settings
from app.modules.automation.models import MessageTemplate
from app.modules.booking.models import Booking
from app.modules.crm.models import Customer, Deal
from app.modules.leads.models import Lead
from app.modules.quotes_invoices.models import Invoice, Quote
from app.modules.reputation.models import ReviewRequest
from app.modules.tenants.models import Tenant

logger = logging.getLogger(__name__)


@dataclass
class AutomationContext:
    first_name: str
    last_name: str | None = None
    email: str | None = None
    phone: str | None = None
    tokens: dict[str, str] = field(default_factory=dict)


def render_template(text: str, ctx: AutomationContext, tenant: Tenant) -> str:
    if not text:
        return text
    replacements = {
        "{{first_name}}": ctx.first_name or "",
        "{{last_name}}": ctx.last_name or "",
        "{{full_name}}": " ".join(filter(None, [ctx.first_name, ctx.last_name])).strip(),
        "{{business_name}}": tenant.name or "",
        "{{business_phone}}": tenant.phone or "",
        **ctx.tokens,
    }
    out = text
    for key, value in replacements.items():
        out = out.replace(key, value)
    return out


async def resolve_automation_context(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    entity_type: str,
    entity_id: uuid.UUID,
) -> tuple[Tenant, AutomationContext] | None:
    tenant = (
        await db.execute(select(Tenant).where(Tenant.id == tenant_id))
    ).scalar_one_or_none()
    if not tenant:
        return None

    frontend = settings.FRONTEND_URL.rstrip("/")
    tokens: dict[str, str] = {
        "{{booking_url}}": f"{frontend}/book/{tenant.slug}",
    }

    if entity_type == "lead":
        lead = (
            await db.execute(
                select(Lead).where(Lead.id == entity_id, Lead.tenant_id == tenant_id, Lead.deleted_at.is_(None))
            )
        ).scalar_one_or_none()
        if not lead:
            return None
        return tenant, AutomationContext(
            first_name=lead.first_name,
            last_name=lead.last_name,
            email=lead.email,
            phone=lead.phone,
            tokens=tokens,
        )

    if entity_type == "deal":
        deal = (
            await db.execute(
                select(Deal).where(Deal.id == entity_id, Deal.tenant_id == tenant_id, Deal.deleted_at.is_(None))
            )
        ).scalar_one_or_none()
        if not deal:
            return None
        customer = (
            await db.execute(select(Customer).where(Customer.id == deal.customer_id))
        ).scalar_one_or_none()
        if not customer:
            return None
        review_url = await _review_url_for_deal(db, tenant, deal, create=False)
        if review_url:
            tokens["{{review_url}}"] = review_url
        return tenant, AutomationContext(
            first_name=customer.first_name,
            last_name=customer.last_name,
            email=customer.email,
            phone=customer.phone,
            tokens={**tokens, "{{service_type}}": deal.service_type or ""},
        )

    if entity_type == "quote":
        quote = (
            await db.execute(select(Quote).where(Quote.id == entity_id, Quote.tenant_id == tenant_id))
        ).scalar_one_or_none()
        if not quote:
            return None
        customer = (
            await db.execute(select(Customer).where(Customer.id == quote.customer_id))
        ).scalar_one_or_none()
        if not customer:
            return None
        tokens["{{quote_number}}"] = quote.quote_number
        tokens["{{quote_url}}"] = f"{frontend}/quote/{quote.public_token}"
        return tenant, AutomationContext(
            first_name=customer.first_name,
            last_name=customer.last_name,
            email=customer.email,
            phone=customer.phone,
            tokens=tokens,
        )

    if entity_type == "booking":
        booking = (
            await db.execute(select(Booking).where(Booking.id == entity_id, Booking.tenant_id == tenant_id))
        ).scalar_one_or_none()
        if not booking:
            return None
        first, *rest = (booking.customer_name or "Customer").split(" ", 1)
        return tenant, AutomationContext(
            first_name=first,
            last_name=rest[0] if rest else None,
            email=booking.customer_email,
            phone=booking.customer_phone,
            tokens=tokens,
        )

    if entity_type == "invoice":
        invoice = (
            await db.execute(select(Invoice).where(Invoice.id == entity_id, Invoice.tenant_id == tenant_id))
        ).scalar_one_or_none()
        if not invoice:
            return None
        customer = (
            await db.execute(select(Customer).where(Customer.id == invoice.customer_id))
        ).scalar_one_or_none()
        if not customer:
            return None
        tokens["{{invoice_number}}"] = invoice.invoice_number
        tokens["{{invoice_url}}"] = f"{frontend}/invoice/{invoice.public_token}"
        return tenant, AutomationContext(
            first_name=customer.first_name,
            last_name=customer.last_name,
            email=customer.email,
            phone=customer.phone,
            tokens=tokens,
        )

    logger.warning("Unknown automation entity_type=%s", entity_type)
    return None


async def _review_url_for_deal(
    db: AsyncSession,
    tenant: Tenant,
    deal: Deal,
    *,
    create: bool,
) -> str | None:
    existing = (
        await db.execute(
            select(ReviewRequest)
            .where(ReviewRequest.deal_id == deal.id, ReviewRequest.tenant_id == tenant.id)
            .order_by(ReviewRequest.created_at.desc())
            .limit(1)
        )
    ).scalar_one_or_none()
    if existing:
        frontend = os.getenv("FRONTEND_URL", settings.FRONTEND_URL).rstrip("/")
        return f"{frontend}/{tenant.slug}/review/{existing.token}"
    if not create:
        return None
    rr = ReviewRequest(
        id=uuid.uuid4(),
        tenant_id=tenant.id,
        deal_id=deal.id,
        customer_id=deal.customer_id,
    )
    db.add(rr)
    await db.flush()
    frontend = os.getenv("FRONTEND_URL", settings.FRONTEND_URL).rstrip("/")
    return f"{frontend}/{tenant.slug}/review/{rr.token}"


async def load_step_message(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    config: dict,
) -> tuple[str | None, str]:
    template_id = config.get("template_id")
    if template_id:
        template = (
            await db.execute(
                select(MessageTemplate).where(
                    MessageTemplate.id == uuid.UUID(str(template_id)),
                    MessageTemplate.tenant_id == tenant_id,
                )
            )
        ).scalar_one_or_none()
        if template:
            return template.subject, template.body
    return config.get("subject"), config.get("body") or ""


async def execute_send_step(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    entity_type: str,
    entity_id: uuid.UUID,
    action: str,
    config: dict,
) -> None:
    resolved = await resolve_automation_context(
        db, tenant_id=tenant_id, entity_type=entity_type, entity_id=entity_id
    )
    if not resolved:
        logger.warning("Automation send skipped: entity not found type=%s id=%s", entity_type, entity_id)
        return

    tenant, ctx = resolved

    if config.get("create_review_request") and entity_type == "deal":
        deal = (
            await db.execute(select(Deal).where(Deal.id == entity_id, Deal.tenant_id == tenant_id))
        ).scalar_one_or_none()
        if deal:
            review_url = await _review_url_for_deal(db, tenant, deal, create=True)
            if review_url:
                ctx.tokens["{{review_url}}"] = review_url

    subject, body = await load_step_message(db, tenant_id, config)
    rendered_body = render_template(body, ctx, tenant)
    rendered_subject = render_template(subject or "", ctx, tenant)

    if action == "send_sms":
        if not ctx.phone:
            raise ValueError("No phone number for automation recipient")
        res = await get_sms_adapter().send(SMSMessage(to=ctx.phone, body=rendered_body))
        if getattr(res, "status", "sent") == "failed":
            raise ValueError(getattr(res, "error", "SMS send failed"))

    elif action == "send_email":
        if not ctx.email:
            raise ValueError("No email address for automation recipient")
        html = rendered_body if "<" in rendered_body else f"<p>{rendered_body.replace(chr(10), '<br/>')}</p>"
        res = await get_email_adapter().send(
            EmailMessage(
                to=ctx.email,
                to_name=" ".join(filter(None, [ctx.first_name, ctx.last_name])).strip() or None,
                subject=rendered_subject or f"Message from {tenant.name}",
                html_body=html,
            )
        )
        if getattr(res, "status", "sent") == "failed":
            raise ValueError(getattr(res, "error", "Email send failed"))
    else:
        raise ValueError(f"Unsupported send action: {action}")
