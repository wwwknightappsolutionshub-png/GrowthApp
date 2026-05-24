"""Tenant → loyalty wallet customer broadcasts (push + email)."""

from __future__ import annotations

import logging
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.email import get_email_adapter
from app.adapters.email.base import EmailMessage
from app.modules.crm.models import Customer
from app.modules.membership_rewards.landing import rewards_portal_url
from app.core.exceptions import BadRequestException
from app.modules.membership_rewards.models import (
    MrCustomerLoyalty,
    MrCustomerPreferences,
    MrCustomerPushSubscription,
)
from app.modules.notifications.service import push_is_configured
from app.modules.membership_rewards.services.customer_push_service import send_loyalty_push
from app.modules.tenants.models import Tenant

logger = logging.getLogger(__name__)


async def count_broadcast_recipients(db: AsyncSession, tenant_id: uuid.UUID) -> dict[str, int]:
    accounts = (
        await db.execute(
            select(MrCustomerLoyalty.customer_id).where(MrCustomerLoyalty.tenant_id == tenant_id)
        )
    ).scalars().all()
    customer_ids = list(accounts)
    if not customer_ids:
        return {"customers": 0, "push_subscribers": 0, "email_opted_in": 0}

    push_count = len(
        (
            await db.execute(
                select(MrCustomerPushSubscription.customer_id)
                .where(
                    MrCustomerPushSubscription.tenant_id == tenant_id,
                    MrCustomerPushSubscription.customer_id.in_(customer_ids),
                )
                .distinct()
            )
        ).scalars().all()
    )

    email_count = len(
        (
            await db.execute(
                select(MrCustomerPreferences.customer_id).where(
                    MrCustomerPreferences.tenant_id == tenant_id,
                    MrCustomerPreferences.customer_id.in_(customer_ids),
                    MrCustomerPreferences.marketing_email == True,  # noqa: E712
                )
            )
        ).scalars().all()
    )

    return {
        "customers": len(customer_ids),
        "push_subscribers": push_count,
        "email_opted_in": email_count,
    }


async def broadcast_to_loyalty_customers(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    title: str,
    body: str,
    send_push: bool = True,
    send_email: bool = False,
    path: str = "dashboard",
) -> dict[str, int]:
    if send_push and not push_is_configured():
        raise BadRequestException(
            "Push notifications are not configured on this server. Enable VAPID keys or send via email."
        )

    tenant = await db.get(Tenant, tenant_id)
    slug = tenant.slug if tenant else str(tenant_id)

    customer_ids = list(
        (
            await db.execute(
                select(MrCustomerLoyalty.customer_id).where(MrCustomerLoyalty.tenant_id == tenant_id)
            )
        ).scalars().all()
    )

    if not customer_ids:
        raise BadRequestException(
            "No enrolled loyalty customers yet. Customers must join your rewards program before you can message them."
        )

    push_sent = 0
    email_sent = 0

    for customer_id in customer_ids:
        if send_push:
            try:
                n = await send_loyalty_push(
                    db,
                    tenant_id=tenant_id,
                    customer_id=customer_id,
                    title=title,
                    body=body,
                    path=path,
                )
                if n > 0:
                    push_sent += 1
            except Exception:
                logger.exception("customer push broadcast failed customer=%s", customer_id)

        if send_email:
            prefs = await db.get(MrCustomerPreferences, (tenant_id, customer_id))
            if prefs and not prefs.marketing_email:
                continue
            customer = await db.get(Customer, customer_id)
            if not customer or not customer.email:
                continue
            try:
                wallet_url = rewards_portal_url(slug, subpath=path)
                await get_email_adapter().send(
                    EmailMessage(
                        to=customer.email,
                        to_name=customer.first_name or customer.email,
                        subject=title,
                        html_body=(
                            f"<p>Hi {customer.first_name or 'there'},</p>"
                            f"<p>{body}</p>"
                            f'<p><a href="{wallet_url}">Open your rewards wallet</a></p>'
                        ),
                    )
                )
                email_sent += 1
            except Exception:
                logger.exception("customer email broadcast failed customer=%s", customer_id)

    return {
        "customers": len(customer_ids),
        "push_sent": push_sent,
        "email_sent": email_sent,
    }
