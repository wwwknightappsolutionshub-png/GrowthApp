"""PWA engagement emails, branding, and white-label addon helpers."""

from __future__ import annotations

import logging
import os
import uuid
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.email import get_email_adapter
from app.adapters.email.base import EmailMessage
from app.core.exceptions import NotFoundException
from app.modules.accounting.models import TenantAddon
from app.modules.auth.models import User
from app.modules.booking.models import Booking
from app.modules.leads.models import Lead
from app.modules.notifications.models import PushSubscription
from app.modules.pwa.constants import FEATURE_PWA_WHITE_LABEL, PWA_ENGAGEMENT_KINDS
from app.modules.pwa.entitlement import tenant_has_pwa_white_label
from app.modules.pwa.models import PwaEngagementEmail
from app.modules.tenants.models import Tenant, TenantMember
from app.templates.renderer import render_email

logger = logging.getLogger(__name__)

COPY = {
    "exit_intent": {
        "subject": "Install CustomerFlow on your phone before you go",
        "headline": "Don't miss your next lead or booking",
        "intro": (
            "You were working in CustomerFlow — install the app and turn on alerts so you get "
            "pinged when a new lead arrives or a booking is due."
        ),
    },
    "first_lead": {
        "subject": "Your first lead is in — install the app for instant alerts",
        "headline": "Congratulations on your first lead",
        "intro": (
            "A new lead just landed in your workspace. Install the mobile app and enable "
            "notifications so you never miss the next one."
        ),
    },
    "first_booking": {
        "subject": "First booking confirmed — install the app to stay on top",
        "headline": "Your first booking is live",
        "intro": (
            "Your calendar is working. Install the app for booking reminders and give customers "
            "a rewards wallet they can add to their home screen."
        ),
    },
}


def _frontend() -> str:
    return os.getenv("FRONTEND_URL", "https://app.customerflow.ai").rstrip("/")


def tenant_install_url() -> str:
    return f"{_frontend()}/dashboard?install=1"


async def _owner_for_tenant(db: AsyncSession, tenant_id: uuid.UUID) -> User | None:
    row = (
        await db.execute(
            select(User)
            .join(TenantMember, TenantMember.user_id == User.id)
            .where(TenantMember.tenant_id == tenant_id, TenantMember.role == "owner")
            .limit(1)
        )
    ).scalar_one_or_none()
    return row


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


async def _already_sent(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
    kind: str,
) -> bool:
    row = (
        await db.execute(
            select(PwaEngagementEmail.id).where(
                PwaEngagementEmail.tenant_id == tenant_id,
                PwaEngagementEmail.user_id == user_id,
                PwaEngagementEmail.kind == kind,
            )
        )
    ).scalar_one_or_none()
    return row is not None


async def send_engagement_email(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
    kind: str,
) -> bool:
    if kind not in PWA_ENGAGEMENT_KINDS:
        return False
    if await _already_sent(db, tenant_id=tenant_id, user_id=user_id, kind=kind):
        return False
    if await _tenant_has_push(db, tenant_id, user_id):
        return False

    user = await db.get(User, user_id)
    tenant = await db.get(Tenant, tenant_id)
    if not user or not user.email or not tenant:
        return False

    copy = COPY[kind]
    install_url = tenant_install_url()
    html = render_email(
        "emails/pwa_install_reminder.html",
        {
            "headline": copy["headline"],
            "intro": copy["intro"],
            "recipient_name": user.full_name or user.email.split("@")[0],
            "install_url": install_url,
            "alert_examples": "new leads, bookings, and customer wallet updates",
        },
    )
    try:
        await get_email_adapter().send(
            EmailMessage(
                to=user.email,
                to_name=user.full_name or "",
                subject=copy["subject"],
                html_body=html,
            )
        )
    except Exception:  # noqa: BLE001
        logger.exception("PWA engagement email failed kind=%s tenant=%s", kind, tenant_id)
        return False

    db.add(
        PwaEngagementEmail(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            user_id=user_id,
            kind=kind,
        )
    )
    await db.commit()
    return True


async def record_exit_intent(db: AsyncSession, *, tenant_id: uuid.UUID, user_id: uuid.UUID) -> bool:
    return await send_engagement_email(db, tenant_id=tenant_id, user_id=user_id, kind="exit_intent")


async def maybe_send_first_lead_email(db: AsyncSession, *, tenant_id: uuid.UUID) -> None:
    count = (
        await db.execute(
            select(func.count())
            .select_from(Lead)
            .where(Lead.tenant_id == tenant_id, Lead.deleted_at.is_(None))
        )
    ).scalar_one()
    if count != 1:
        return
    owner = await _owner_for_tenant(db, tenant_id)
    if not owner:
        return
    await send_engagement_email(db, tenant_id=tenant_id, user_id=owner.id, kind="first_lead")


async def maybe_send_first_booking_email(db: AsyncSession, *, tenant_id: uuid.UUID) -> None:
    count = (
        await db.execute(select(func.count()).select_from(Booking).where(Booking.tenant_id == tenant_id))
    ).scalar_one()
    if count != 1:
        return
    owner = await _owner_for_tenant(db, tenant_id)
    if not owner:
        return
    await send_engagement_email(db, tenant_id=tenant_id, user_id=owner.id, kind="first_booking")


async def get_branding_payload(db: AsyncSession, *, tenant_id: uuid.UUID) -> dict:
    tenant = await db.get(Tenant, tenant_id)
    if not tenant:
        raise NotFoundException("Tenant")
    enabled = await tenant_has_pwa_white_label(db, tenant_id)
    return {
        "enabled": enabled,
        "name": tenant.name if enabled else "CustomerFlowai",
        "short_name": (tenant.name or "CustomerFlow")[:12] if enabled else "CustomerFlowai",
        "theme_color": tenant.primary_color or "#025422",
        "icon_url": tenant.logo_url if enabled else None,
    }


async def grant_white_label_addon(db: AsyncSession, tenant_id: uuid.UUID) -> TenantAddon:
    existing = (
        await db.execute(
            select(TenantAddon).where(
                TenantAddon.tenant_id == tenant_id,
                TenantAddon.feature_code == FEATURE_PWA_WHITE_LABEL,
            )
        )
    ).scalar_one_or_none()
    if existing:
        existing.status = "active"
        existing.expires_at = None
        db.add(existing)
        await db.commit()
        await db.refresh(existing)
        return existing
    row = TenantAddon(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        feature_code=FEATURE_PWA_WHITE_LABEL,
        status="active",
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return row
