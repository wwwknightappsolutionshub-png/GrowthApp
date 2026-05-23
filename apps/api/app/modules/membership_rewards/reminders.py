"""Trial reminder sweeps — day 3 email + in-app, day 6 email + modal, day 15 win-back."""

from __future__ import annotations

import logging
import os
import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.email import get_email_adapter
from app.adapters.email.base import EmailMessage
from app.modules.accounting.models import TenantAddon
from app.modules.membership_rewards.constants import (
    FEATURE_MEMBERSHIP_REWARDS,
    TRIAL_DAYS,
    WINBACK_DAY,
)
from app.modules.membership_rewards.entitlement import tenant_has_membership_rewards
from app.modules.membership_rewards.models import MrTrialReminders
from app.modules.auth.models import User
from app.modules.tenants.models import Tenant, TenantMember
from app.templates.renderer import (
    render_membership_trial_day3,
    render_membership_trial_day6,
    render_membership_winback_day15,
)

logger = logging.getLogger(__name__)


def _utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def _frontend() -> str:
    return os.getenv("FRONTEND_URL", "https://app.customerflow.ai").rstrip("/")


async def _owner_for_tenant(db: AsyncSession, tenant_id: uuid.UUID) -> tuple[User | None, Tenant | None]:
    row = (
        await db.execute(
            select(Tenant, User)
            .join(TenantMember, TenantMember.tenant_id == Tenant.id)
            .join(User, User.id == TenantMember.user_id)
            .where(Tenant.id == tenant_id, TenantMember.role == "owner")
            .limit(1)
        )
    ).first()
    if not row:
        return None, await db.get(Tenant, tenant_id)
    tenant, user = row
    return user, tenant


async def get_trial_status(db: AsyncSession, tenant_id: uuid.UUID) -> dict:
    """Trial state for dashboard banner, urgency modal, and win-back CTA."""
    now = _utc(datetime.now(timezone.utc))
    trial = (
        await db.execute(select(MrTrialReminders).where(MrTrialReminders.tenant_id == tenant_id))
    ).scalar_one_or_none()
    addon = (
        await db.execute(
            select(TenantAddon).where(
                TenantAddon.tenant_id == tenant_id,
                TenantAddon.feature_code == FEATURE_MEMBERSHIP_REWARDS,
            )
        )
    ).scalar_one_or_none()

    base = _frontend()
    upgrade_url = f"{base}/dashboard/membership-rewards/upgrade"
    setup_url = f"{base}/dashboard/membership-rewards"

    if not trial:
        return {
            "on_trial": False,
            "trial_expired": False,
            "converted": False,
            "days_remaining": 0,
            "trial_ends_at": None,
            "trial_started_at": None,
            "show_urgency_modal": False,
            "show_winback_banner": False,
            "winback_discount_percent": 50,
            "upgrade_url": upgrade_url,
            "setup_url": setup_url,
            "reminders": {},
        }

    converted = trial.converted_at is not None
    expires = _utc(addon.expires_at) if addon and addon.expires_at else _utc(trial.trial_ends_at)
    started = _utc(trial.trial_started_at)
    ends = _utc(trial.trial_ends_at)

    active = await tenant_has_membership_rewards(db, tenant_id)
    paid_no_expiry = bool(addon and addon.status == "active" and addon.expires_at is None)
    on_trial = active and not converted and not paid_no_expiry and expires > now
    trial_expired = not converted and not paid_no_expiry and expires <= now
    days_remaining = max(0, (expires - now).days) if expires > now else 0

    # Last day of trial (day 6+ of 7-day trial, or ≤1 day left)
    days_elapsed = (now - started).days
    show_urgency_modal = on_trial and (days_remaining <= 1 or days_elapsed >= TRIAL_DAYS - 1)

    show_winback = trial_expired and not active

    return {
        "on_trial": on_trial,
        "trial_expired": trial_expired,
        "converted": converted,
        "days_remaining": days_remaining,
        "trial_ends_at": ends.isoformat(),
        "trial_started_at": started.isoformat(),
        "show_urgency_modal": show_urgency_modal,
        "show_winback_banner": show_winback,
        "winback_discount_percent": trial.winback_discount_percent,
        "upgrade_url": upgrade_url,
        "setup_url": setup_url,
        "reminders": {
            "day3_email_at": trial.day3_email_at.isoformat() if trial.day3_email_at else None,
            "day6_email_at": trial.day6_email_at.isoformat() if trial.day6_email_at else None,
            "day6_modal_at": trial.day6_modal_at.isoformat() if trial.day6_modal_at else None,
            "day15_winback_at": trial.day15_winback_at.isoformat() if trial.day15_winback_at else None,
        },
    }


async def sweep_membership_trial_reminders(db: AsyncSession) -> int:
    """Process due trial emails/notifications. Returns count of actions taken."""
    now = _utc(datetime.now(timezone.utc))
    rows = list((await db.execute(select(MrTrialReminders))).scalars().all())
    sent = 0
    frontend = _frontend()

    for trial in rows:
        if trial.converted_at:
            continue

        owner, tenant = await _owner_for_tenant(db, trial.tenant_id)
        if not owner or not tenant:
            continue

        addon = (
            await db.execute(
                select(TenantAddon).where(
                    TenantAddon.tenant_id == trial.tenant_id,
                    TenantAddon.feature_code == FEATURE_MEMBERSHIP_REWARDS,
                )
            )
        ).scalar_one_or_none()

        started = _utc(trial.trial_started_at)
        ends = _utc(trial.trial_ends_at)
        days_elapsed = (now - started).days
        days_remaining = max(0, (ends - now).days)

        first_name = (owner.full_name or "").split()[0] if owner.full_name else "there"
        upgrade_url = f"{frontend}/dashboard/membership-rewards/upgrade"
        setup_url = f"{frontend}/dashboard/membership-rewards"
        trial_ends_label = ends.strftime("%d %B %Y")

        active = addon and addon.status == "active" and await tenant_has_membership_rewards(
            db, trial.tenant_id
        )

        # ── Active trial: day 3 & 6 ──────────────────────────────────────────
        if active:
            if days_elapsed >= 3 and trial.day3_email_at is None:
                await _send_email(
                    owner.email,
                    owner.full_name,
                    "Your Membership & Rewards trial — day 3 check-in",
                    render_membership_trial_day3(
                        first_name=first_name,
                        business_name=tenant.name,
                        dashboard_url=setup_url,
                    ),
                )
                trial.day3_email_at = now
                await _create_trial_notification(
                    db,
                    trial.tenant_id,
                    owner.id,
                    day=3,
                    title="Day 3 — set up your membership page",
                    body="Create a plan and publish /memberships so customers can join your loyalty program.",
                    link="/dashboard/membership-rewards?section=plans",
                )
                sent += 1

            if days_elapsed >= TRIAL_DAYS - 1 and trial.day6_email_at is None:
                await _send_email(
                    owner.email,
                    owner.full_name,
                    f"Your Membership & Rewards trial ends {trial_ends_label}",
                    render_membership_trial_day6(
                        first_name=first_name,
                        business_name=tenant.name,
                        trial_ends_at=trial_ends_label,
                        upgrade_url=upgrade_url,
                        days_remaining=max(1, days_remaining),
                    ),
                )
                trial.day6_email_at = now
                sent += 1

            if days_remaining <= 1 and trial.day6_modal_at is None:
                await _create_trial_notification(
                    db,
                    trial.tenant_id,
                    owner.id,
                    day=6,
                    title="Trial ends tomorrow — Membership & Rewards",
                    body=(
                        "Publish your memberships page and subscribe to keep points, tiers, "
                        "and customer subscriptions active."
                    ),
                    link="/dashboard/membership-rewards/upgrade",
                    extra={"urgency": True, "days_remaining": days_remaining},
                )
                trial.day6_modal_at = now
                sent += 1

        # ── Expired trial: day 15 win-back ───────────────────────────────────
        expired = addon and addon.expires_at and _utc(addon.expires_at) < now
        if not expired and days_elapsed < WINBACK_DAY:
            await db.commit()
            continue

        if days_elapsed >= WINBACK_DAY and trial.day15_winback_at is None:
            discount = trial.winback_discount_percent
            await _send_email(
                owner.email,
                owner.full_name,
                f"{discount}% off Membership & Rewards — welcome back",
                render_membership_winback_day15(
                    first_name=first_name,
                    business_name=tenant.name,
                    discount_percent=discount,
                    upgrade_url=upgrade_url,
                ),
            )
            await _create_trial_notification(
                db,
                trial.tenant_id,
                owner.id,
                day=15,
                title=f"{discount}% off — Membership & Rewards",
                body=f"Your trial ended. Resubscribe now and save {discount}% on your first month.",
                link="/dashboard/membership-rewards/upgrade",
                extra={"winback": True, "discount_percent": discount},
            )
            trial.day15_winback_at = now
            sent += 1

        await db.commit()

    return sent


async def _send_email(to: str, to_name: str | None, subject: str, html: str) -> None:
    try:
        adapter = get_email_adapter()
        await adapter.send(
            EmailMessage(to=to, to_name=to_name, subject=subject, html_body=html)
        )
    except Exception:  # noqa: BLE001
        logger.exception("Failed to send membership trial email to %s", to)


async def _create_trial_notification(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
    *,
    day: int,
    title: str,
    body: str,
    link: str,
    extra: dict | None = None,
) -> None:
    from app.modules.notifications.service import create_notification

    payload = {"day": day, "trial_type": "membership_rewards", **(extra or {})}
    try:
        await create_notification(
            db,
            tenant_id=tenant_id,
            user_id=user_id,
            kind="membership.trial_reminder",
            title=title,
            body=body,
            link=link,
            extra=payload,
        )
    except Exception:  # noqa: BLE001
        logger.exception("Failed to create membership trial notification for tenant %s", tenant_id)
