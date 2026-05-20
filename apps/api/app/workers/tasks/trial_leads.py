"""Trial lead auto-delivery and day-6 reminder emails."""
from __future__ import annotations

import logging
import os
from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from app.adapters import get_email_adapter
from app.adapters.email.base import EmailMessage
from app.core.config import settings
from app.core.database import get_db_context
from app.modules.auth.models import User
from app.modules.lead_marketplace.trial_assignment import run_daily_trial_assignments
from app.modules.tenants.models import Tenant, TenantMember

logger = logging.getLogger(__name__)


async def assign_daily_trial_leads(ctx: dict) -> dict:
    """Cron: 2 leads/day for tenants in first 7 days after signup."""
    async with get_db_context() as db:
        return await run_daily_trial_assignments(db)


async def send_trial_lead_ending_reminders(ctx: dict) -> dict:
    """Day 6 of trial: email owners that free auto-leads end after day 7."""
    sent = 0
    now = datetime.now(timezone.utc)
    day_start = now - timedelta(days=6)
    day_end = now - timedelta(days=5)

    async with get_db_context() as db:
        tenants = (
            await db.execute(
                select(Tenant).where(
                    Tenant.is_active == True,  # noqa: E712
                    Tenant.is_managed_client == False,
                    Tenant.trial_reminder_sent_at.is_(None),
                    Tenant.created_at >= day_start,
                    Tenant.created_at < day_end,
                )
            )
        ).scalars().all()

        frontend = settings.FRONTEND_URL.rstrip("/")
        adapter = get_email_adapter()

        for tenant in tenants:
            owner = (
                await db.execute(
                    select(User)
                    .join(TenantMember, TenantMember.user_id == User.id)
                    .where(
                        TenantMember.tenant_id == tenant.id,
                        TenantMember.role == "owner",
                    )
                    .limit(1)
                )
            ).scalar_one_or_none()
            if not owner or not owner.email:
                continue

            try:
                from app.templates.renderer import render_trial_auto_leads_ending

                html = render_trial_auto_leads_ending(
                    full_name=owner.full_name,
                    business_name=tenant.name,
                    days_left=1,
                    leads_per_day=settings.TRIAL_LEADS_PER_DAY,
                    upgrade_url=f"{frontend}/dashboard/billing",
                    leads_url=f"{frontend}/dashboard/leads",
                )
                await adapter.send(
                    EmailMessage(
                        to=owner.email,
                        to_name=owner.full_name,
                        subject="Your free daily leads end tomorrow — upgrade to keep them coming",
                        html_body=html,
                    )
                )
                tenant.trial_reminder_sent_at = now
                db.add(tenant)
                sent += 1
            except Exception:  # noqa: BLE001
                logger.exception("trial reminder email failed tenant=%s", tenant.id)

        await db.commit()

    logger.info("send_trial_lead_ending_reminders: sent=%s", sent)
    return {"sent": sent}
