"""PWA install reminder emails — 30 min, 1 hour, and 3 hours after M&R registration."""

from __future__ import annotations

import logging
import os
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.email import get_email_adapter
from app.adapters.email.base import EmailMessage
from app.modules.auth.models import User
from app.modules.crm.models import Customer
from app.modules.membership_rewards.landing import rewards_portal_url
from app.modules.membership_rewards.models import MrCustomerPushSubscription, MrPwaInstallReminder
from app.modules.notifications.models import PushSubscription
from app.modules.tenants.models import Tenant, TenantMember
from app.templates.renderer import render_email

logger = logging.getLogger(__name__)

REMINDER_STAGES = (
    ("30m", timedelta(minutes=30), "reminder_30m_sent_at"),
    ("1h", timedelta(hours=1), "reminder_1h_sent_at"),
    ("3h", timedelta(hours=3), "reminder_3h_sent_at"),
)

STAGE_COPY = {
    "30m": {
        "headline": "Give customers a wallet app on their phone",
        "intro": (
            "You enabled Membership & Rewards — share a installable wallet your customers can "
            "add to their home screen for points, offers, and booking reminders."
        ),
    },
    "1h": {
        "headline": "Quick reminder: launch your customer wallet app",
        "intro": (
            "Businesses that give customers a wallet app see stronger repeat bookings. Install "
            "your workspace app too — get pinged when a new lead arrives or a booking is due."
        ),
    },
    "3h": {
        "headline": "Last reminder — wallet app + mobile alerts",
        "intro": (
            "Set up your customer rewards wallet and turn on push alerts in one minute. "
            "Your team gets lead and booking pings; customers get points and offers on their phone."
        ),
    },
}


def _frontend() -> str:
    return os.getenv("FRONTEND_URL", "https://app.customerflow.ai").rstrip("/")


def _utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def tenant_install_url() -> str:
    return f"{_frontend()}/dashboard?install=1"


def customer_install_url(tenant_slug: str) -> str:
    return f"{rewards_portal_url(tenant_slug)}?install=1"


async def schedule_tenant_pwa_reminders(db: AsyncSession, tenant_id: uuid.UUID) -> None:
    owner = (
        await db.execute(
            select(User.id)
            .join(TenantMember, TenantMember.user_id == User.id)
            .where(TenantMember.tenant_id == tenant_id, TenantMember.role == "owner")
            .limit(1)
        )
    ).scalar_one_or_none()
    if not owner:
        return

    existing = (
        await db.execute(
            select(MrPwaInstallReminder.id).where(
                MrPwaInstallReminder.audience == "tenant",
                MrPwaInstallReminder.tenant_id == tenant_id,
                MrPwaInstallReminder.completed_at.is_(None),
            )
        )
    ).scalar_one_or_none()
    if existing:
        return

    db.add(
        MrPwaInstallReminder(
            id=uuid.uuid4(),
            audience="tenant",
            tenant_id=tenant_id,
            user_id=owner,
            registered_at=datetime.now(timezone.utc),
        )
    )
    await db.commit()


async def schedule_customer_pwa_reminders(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    customer_id: uuid.UUID,
) -> None:
    existing = (
        await db.execute(
            select(MrPwaInstallReminder.id).where(
                MrPwaInstallReminder.audience == "customer",
                MrPwaInstallReminder.tenant_id == tenant_id,
                MrPwaInstallReminder.customer_id == customer_id,
                MrPwaInstallReminder.completed_at.is_(None),
            )
        )
    ).scalar_one_or_none()
    if existing:
        return

    db.add(
        MrPwaInstallReminder(
            id=uuid.uuid4(),
            audience="customer",
            tenant_id=tenant_id,
            customer_id=customer_id,
            registered_at=datetime.now(timezone.utc),
        )
    )
    await db.commit()


async def _tenant_has_push(db: AsyncSession, tenant_id: uuid.UUID, user_id: uuid.UUID) -> bool:
    row = (
        await db.execute(
            select(PushSubscription.id).where(
                PushSubscription.tenant_id == tenant_id,
                PushSubscription.user_id == user_id,
                PushSubscription.is_active == True,  # noqa: E712
            )
        )
    ).scalar_one_or_none()
    return row is not None


async def _customer_has_push(db: AsyncSession, tenant_id: uuid.UUID, customer_id: uuid.UUID) -> bool:
    row = (
        await db.execute(
            select(MrCustomerPushSubscription.id).where(
                MrCustomerPushSubscription.tenant_id == tenant_id,
                MrCustomerPushSubscription.customer_id == customer_id,
            )
        )
    ).scalar_one_or_none()
    return row is not None


async def _send_reminder_email(
    *,
    to: str,
    to_name: str,
    subject: str,
    stage: str,
    install_url: str,
    alert_examples: str,
) -> None:
    copy = STAGE_COPY[stage]
    html = render_email(
        "emails/pwa_install_reminder.html",
        {
            "headline": copy["headline"],
            "intro": copy["intro"],
            "recipient_name": to_name,
            "install_url": install_url,
            "alert_examples": alert_examples,
        },
    )
    await get_email_adapter().send(
        EmailMessage(to=to, to_name=to_name, subject=subject, html_body=html)
    )


async def _process_row(db: AsyncSession, row: MrPwaInstallReminder, now: datetime) -> int:
    if row.completed_at:
        return 0

    sent = 0
    registered = _utc(row.registered_at)

    if row.audience == "tenant" and row.user_id:
        if await _tenant_has_push(db, row.tenant_id, row.user_id):
            row.completed_at = now
            db.add(row)
            return 0
        user = await db.get(User, row.user_id)
        tenant = await db.get(Tenant, row.tenant_id)
        if not user or not user.email or not tenant:
            row.completed_at = now
            db.add(row)
            return 0
        recipient_name = user.full_name or user.email.split("@")[0]
        recipient_email = user.email
        install_url = tenant_install_url()
        alert_examples = "new leads, bookings, and customer wallet activity"
    elif row.audience == "customer" and row.customer_id:
        if await _customer_has_push(db, row.tenant_id, row.customer_id):
            row.completed_at = now
            db.add(row)
            return 0
        customer = await db.get(Customer, row.customer_id)
        tenant = await db.get(Tenant, row.tenant_id)
        if not customer or not customer.email or not tenant:
            row.completed_at = now
            db.add(row)
            return 0
        recipient_name = customer.first_name or customer.email.split("@")[0]
        recipient_email = customer.email
        install_url = customer_install_url(tenant.slug)
        alert_examples = "points, rewards, and exclusive offers"
    else:
        row.completed_at = now
        db.add(row)
        return 0

    for stage_key, delta, attr in REMINDER_STAGES:
        if getattr(row, attr):
            continue
        if registered + delta > now:
            continue
        try:
            subject = {
                "30m": "Install your CustomerFlow app (30-minute reminder)",
                "1h": "Enable mobile alerts for Membership & Rewards",
                "3h": "Final reminder: install the app & turn on notifications",
            }[stage_key]
            await _send_reminder_email(
                to=recipient_email,
                to_name=recipient_name,
                subject=subject,
                stage=stage_key,
                install_url=install_url,
                alert_examples=alert_examples,
            )
            setattr(row, attr, now)
            sent += 1
        except Exception:  # noqa: BLE001
            logger.exception(
                "PWA install reminder failed audience=%s tenant=%s stage=%s",
                row.audience,
                row.tenant_id,
                stage_key,
            )

    if row.reminder_30m_sent_at and row.reminder_1h_sent_at and row.reminder_3h_sent_at:
        row.completed_at = now

    db.add(row)
    return sent


async def sweep_pwa_install_reminders(db: AsyncSession) -> int:
    """Send due PWA install reminder emails."""
    now = datetime.now(timezone.utc)
    rows = (
        await db.execute(
            select(MrPwaInstallReminder).where(MrPwaInstallReminder.completed_at.is_(None)).limit(200)
        )
    ).scalars().all()

    total = 0
    changed = False
    for row in rows:
        n = await _process_row(db, row, now)
        if n:
            total += n
            changed = True
        elif row.completed_at or row.reminder_30m_sent_at or row.reminder_1h_sent_at or row.reminder_3h_sent_at:
            changed = True
    if changed:
        await db.commit()
    return total
