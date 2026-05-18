"""
Scheduled email-sequence tasks.

Runs on a daily cron via ARQ:
  - onboarding reminders on days 3, 7, 10
  - trial-expiry warning 24 h before trial ends
  - subscription upsell for users with no active plan after day 10

Enqueue from the worker's cron list or trigger manually via the admin API.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.email import get_email_adapter
from app.core.database import AsyncSessionLocal
from app.modules.auth.models import User
from app.modules.billing.models import Subscription
from app.modules.tenants.models import Tenant, TenantMember
from app.templates.renderer import render_template

logger = logging.getLogger(__name__)

_NOW = lambda: datetime.now(timezone.utc)


def _days_since(dt: datetime) -> int:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return (_NOW() - dt).days


async def _get_owner_email(db: AsyncSession, tenant: Tenant) -> tuple[str, str] | None:
    """Return (email, first_name) for the tenant owner, or None."""
    owner_mem = (
        await db.execute(
            select(TenantMember)
            .where(TenantMember.tenant_id == tenant.id, TenantMember.role == "owner")
        )
    ).scalar_one_or_none()
    if not owner_mem:
        return None
    user = (
        await db.execute(select(User).where(User.id == owner_mem.user_id))
    ).scalar_one_or_none()
    if not user:
        return None
    first_name = (user.full_name or "").split()[0] if user.full_name else ""
    return user.email, first_name


async def send_onboarding_emails(ctx: dict) -> None:  # noqa: ARG001
    """Send day-3, day-7, day-10 onboarding reminders."""
    email_adapter = get_email_adapter()
    async with AsyncSessionLocal() as db:
        tenants = list((await db.execute(select(Tenant).where(Tenant.is_active == True))).scalars())
        for tenant in tenants:
            days = _days_since(tenant.created_at)
            if days not in (3, 7, 10):
                continue
            result = await _get_owner_email(db, tenant)
            if not result:
                continue
            email, first_name = result
            body = render_template(
                "emails/onboarding_reminder.html",
                {
                    "first_name": first_name,
                    "day": days,
                    "lead_quota": 3,
                    "dashboard_url": "https://app.customerflow.ai/dashboard",
                    "setup_url": "https://app.customerflow.ai/dashboard/messaging",
                    "upgrade_url": "https://app.customerflow.ai/dashboard/billing",
                },
            )
            subject_map = {
                3: f"Day 3: one thing that transforms your business, {first_name} 🚀",
                7: f"Halfway through your trial — here's what to do next, {first_name}",
                10: f"4 days left — the AI feature you haven't tried yet",
            }
            try:
                await email_adapter.send(
                    to=email,
                    subject=subject_map[days],
                    html=body,
                )
                logger.info("Sent day-%s onboarding email to %s", days, email)
            except Exception:
                logger.exception("Failed to send day-%s email to %s", days, email)


async def send_trial_expiry_emails(ctx: dict) -> None:  # noqa: ARG001
    """Send a trial-expiry warning email 1–2 days before the trial ends."""
    email_adapter = get_email_adapter()
    trial_days = 14
    async with AsyncSessionLocal() as db:
        tenants = list((await db.execute(select(Tenant).where(Tenant.is_active == True))).scalars())
        for tenant in tenants:
            days = _days_since(tenant.created_at)
            # send at day 12 (2 days left) and day 13 (1 day left)
            if days not in (12, 13):
                continue
            # skip if they have an active subscription
            sub = (
                await db.execute(
                    select(Subscription).where(
                        Subscription.tenant_id == tenant.id,
                        Subscription.status == "active",
                    )
                )
            ).scalar_one_or_none()
            if sub:
                continue
            result = await _get_owner_email(db, tenant)
            if not result:
                continue
            email, first_name = result
            hours_remaining = (trial_days - days) * 24
            body = render_template(
                "emails/trial_expiry.html",
                {
                    "first_name": first_name,
                    "hours_remaining": hours_remaining,
                    "upgrade_url": "https://app.customerflow.ai/dashboard/billing",
                },
            )
            try:
                await email_adapter.send(
                    to=email,
                    subject=f"Your CustomerFlow AI trial ends in {hours_remaining} hours",
                    html=body,
                )
                logger.info("Sent trial-expiry email (%sh) to %s", hours_remaining, email)
            except Exception:
                logger.exception("Failed to send trial-expiry email to %s", email)


async def send_subscription_upsell_emails(ctx: dict) -> None:  # noqa: ARG001
    """Send a subscription upsell email to users who have not subscribed after 10 days."""
    email_adapter = get_email_adapter()
    async with AsyncSessionLocal() as db:
        tenants = list((await db.execute(select(Tenant).where(Tenant.is_active == True))).scalars())
        for tenant in tenants:
            days = _days_since(tenant.created_at)
            if days != 10:
                continue
            sub = (
                await db.execute(
                    select(Subscription).where(
                        Subscription.tenant_id == tenant.id,
                        Subscription.status.in_(["active", "trialing"]),
                    )
                )
            ).scalar_one_or_none()
            if sub:
                continue
            result = await _get_owner_email(db, tenant)
            if not result:
                continue
            email, first_name = result
            body = render_template(
                "emails/subscription_upsell.html",
                {
                    "first_name": first_name,
                    "trial_days_used": 10,
                    "days_remaining": 4,
                    "upgrade_url": "https://app.customerflow.ai/dashboard/billing",
                },
            )
            try:
                await email_adapter.send(
                    to=email,
                    subject=f"{first_name}, your trial is 10 days old — here's why this is the best week to upgrade",
                    html=body,
                )
                logger.info("Sent upsell email to %s (day 10, no subscription)", email)
            except Exception:
                logger.exception("Failed to send upsell email to %s", email)
