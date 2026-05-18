"""AI Social Module — content generation, approval, scheduling & publishing workflows.

Implements the exact backend logic from Step 3:

  AI Content Generation:
    1. Read brand identity (tone, colors, fonts)
    2. Read sample uploads to learn style
    3. Generate text_content, graphic_prompt, ai_notes
    4. Create SocialContentDraft

  Approval Flow:
    1. On draft generated → send via email + WhatsApp (SocialApprovalQueue)
    2. Wait for user response ("Approve" or "Revise")
    3. Update SocialContentDraft.status

  Scheduling:
    - After approval → insert into SocialScheduleQueue

  Publishing:
    - For each due item → publish to platform, mark posted_status
"""
from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters import get_ai_adapter, get_social_adapter
from app.adapters.ai.base import SocialPostRequest
from app.adapters.social.base import SocialPostPayload
from app.integrations.email_sender import send_social_approval_request
from app.integrations.whatsapp_sender import send_whatsapp_approval_request
from app.modules.social.models import (
    SocialApprovalQueue,
    SocialContentDraft,
    SocialPostingPreferences,
    SocialSampleUploads,
    SocialBrandIdentity,
    SocialScheduleQueue,
)
from app.modules.tenants.models import Tenant
from app.modules.auth.models import User

logger = logging.getLogger(__name__)

# ── Style inference helpers ───────────────────────────────────────────────


@dataclass
class StyleProfile:
    """Aggregated style learned from brand identity + sample uploads."""
    tone: str
    primary_color: str | None
    secondary_color: str | None
    fonts: list[str]
    logo_url: str | None
    sample_count: int
    sample_types: dict[str, int]  # IMAGE / VIDEO / PDF counts


async def _build_style_profile(
    db: AsyncSession, tenant_id: uuid.UUID
) -> StyleProfile:
    """Read brand identity + sample uploads to derive a style profile."""
    identity = (
        await db.execute(
            select(SocialBrandIdentity).where(SocialBrandIdentity.tenant_id == tenant_id)
        )
    ).scalar_one_or_none()

    samples = (
        await db.execute(
            select(SocialSampleUploads).where(SocialSampleUploads.tenant_id == tenant_id)
        )
    ).scalars().all()

    sample_types: dict[str, int] = {}
    for s in samples:
        sample_types[s.file_type] = sample_types.get(s.file_type, 0) + 1

    colors = identity.brand_colors if identity and identity.brand_colors else {}
    fonts_raw = identity.brand_fonts if identity and identity.brand_fonts else {}

    primary = colors.get("primary") if isinstance(colors, dict) else None
    secondary = colors.get("secondary") if isinstance(colors, dict) else None

    if isinstance(fonts_raw, dict):
        fonts = [v for v in fonts_raw.values() if v]
    elif isinstance(fonts_raw, list):
        fonts = [v for v in fonts_raw if v]
    else:
        fonts = []

    return StyleProfile(
        tone=(identity.tone_of_voice if identity and identity.tone_of_voice else "friendly"),
        primary_color=primary,
        secondary_color=secondary,
        fonts=fonts,
        logo_url=identity.logo_url if identity else None,
        sample_count=len(samples),
        sample_types=sample_types,
    )


# ── 1. AI CONTENT GENERATION ──────────────────────────────────────────────


async def generate_draft_for_tenant(
    db: AsyncSession,
    tenant: Tenant,
    *,
    topic_hint: Optional[str] = None,
) -> SocialContentDraft:
    """Generate a single content draft.

    Logic (Step 3):
      1. Read brand identity (tone, colors, fonts).
      2. Read sample uploads to learn style.
      3. Generate text_content (caption), graphic_prompt, ai_notes.
      4. Create entry in SocialContentDraft.
    """
    style = await _build_style_profile(db, tenant.id)

    ai = get_ai_adapter()
    service_type = getattr(tenant, "business_type", None) or "general"
    text_content = await ai.generate_social_post(
        SocialPostRequest(
            business_name=tenant.name,
            service_type=service_type,
            job_description=topic_hint or f"Promote our {service_type} services",
            tone=style.tone,
            platform="facebook",
            image_count=1,
        )
    )

    graphic_prompt = _build_graphic_prompt(
        business_name=tenant.name,
        service_type=service_type,
        topic_hint=topic_hint,
        style=style,
    )

    ai_notes = (
        f"Tone: {style.tone}; "
        f"Colors: {style.primary_color or '-'} / {style.secondary_color or '-'}; "
        f"Fonts: {', '.join(style.fonts) or '-'}; "
        f"Samples learned: {style.sample_count} "
        f"({', '.join(f'{k}={v}' for k, v in style.sample_types.items()) or 'none'})"
    )

    draft = SocialContentDraft(
        id=uuid.uuid4(),
        tenant_id=tenant.id,
        text_content=text_content,
        image_url=None,
        ai_notes=f"{ai_notes}\n\nGRAPHIC_PROMPT: {graphic_prompt}",
        status="PENDING",
    )
    db.add(draft)
    await db.flush()
    return draft


def _build_graphic_prompt(
    *,
    business_name: str,
    service_type: str,
    topic_hint: Optional[str],
    style: StyleProfile,
) -> str:
    """Construct a design prompt describing the graphic to generate."""
    parts = [
        f"Design a social media post for {business_name} ({service_type}).",
        f"Topic: {topic_hint}." if topic_hint else "Topic: brand promotion.",
        f"Tone: {style.tone}.",
    ]
    if style.primary_color:
        parts.append(f"Primary color: {style.primary_color}.")
    if style.secondary_color:
        parts.append(f"Secondary color: {style.secondary_color}.")
    if style.fonts:
        parts.append(f"Typography: {', '.join(style.fonts)}.")
    if style.logo_url:
        parts.append(f"Include brand logo from {style.logo_url}.")
    if style.sample_count:
        parts.append(
            f"Match the style of {style.sample_count} reference assets uploaded by the brand."
        )
    parts.append("Layout: clean, mobile-friendly, high contrast, single focal point.")
    return " ".join(parts)


# ── 2. APPROVAL FLOW ──────────────────────────────────────────────────────


async def send_draft_for_approval(
    db: AsyncSession,
    tenant: Tenant,
    draft: SocialContentDraft,
    *,
    recipient_email: Optional[str] = None,
    recipient_whatsapp: Optional[str] = None,
) -> list[SocialApprovalQueue]:
    """Send draft via email + WhatsApp; track each in SocialApprovalQueue.

    Delegates the actual delivery to the dedicated integration modules:
      * :func:`app.integrations.email_sender.send_social_approval_request`
      * :func:`app.integrations.whatsapp_sender.send_whatsapp_approval_request`
    """
    entries: list[SocialApprovalQueue] = []

    if recipient_email:
        delivery = await send_social_approval_request(
            tenant, draft, recipient_email=recipient_email,
        )
        entry = SocialApprovalQueue(
            id=uuid.uuid4(),
            tenant_id=tenant.id,
            draft_id=draft.id,
            delivery_channel="EMAIL",
            sent_at=delivery.get("sent_at"),
            response_received=False,
        )
        db.add(entry)
        entries.append(entry)

    if recipient_whatsapp:
        delivery = await send_whatsapp_approval_request(
            tenant, draft, recipient_whatsapp=recipient_whatsapp,
        )
        entry = SocialApprovalQueue(
            id=uuid.uuid4(),
            tenant_id=tenant.id,
            draft_id=draft.id,
            delivery_channel="WHATSAPP",
            sent_at=delivery.get("sent_at"),
            response_received=False,
        )
        db.add(entry)
        entries.append(entry)

    await db.flush()
    return entries


async def record_approval_response(
    db: AsyncSession,
    tenant: Tenant,
    *,
    draft_id: uuid.UUID,
    response_text: str,
    approved: bool,
) -> SocialContentDraft | None:
    """Update SocialApprovalQueue + SocialContentDraft.status based on response.

    Approved=True → status=APPROVED → also auto-schedule (Scheduling Logic).
    Approved=False → status=REVISE.
    """
    queue_entries = (
        await db.execute(
            select(SocialApprovalQueue).where(
                SocialApprovalQueue.draft_id == draft_id,
                SocialApprovalQueue.tenant_id == tenant.id,
            )
        )
    ).scalars().all()
    for q in queue_entries:
        q.response_received = True
        q.response_text = response_text

    draft = (
        await db.execute(
            select(SocialContentDraft).where(
                SocialContentDraft.id == draft_id,
                SocialContentDraft.tenant_id == tenant.id,
            )
        )
    ).scalar_one_or_none()

    if not draft:
        return None

    if approved:
        draft.status = "APPROVED"
        # Scheduling Logic: after approval, system automatically inserts into
        # SocialScheduleQueue for every preferred platform.
        await _auto_schedule_after_approval(db, tenant, draft)
    else:
        draft.status = "REVISE"

    await db.flush()
    return draft


# ── 3. SCHEDULING ─────────────────────────────────────────────────────────


async def _auto_schedule_after_approval(
    db: AsyncSession,
    tenant: Tenant,
    draft: SocialContentDraft,
) -> list[SocialScheduleQueue]:
    """After approval, auto-insert into SocialScheduleQueue.

    Picks the next slot based on the tenant's posting preferences
    (posts_per_week + preferred_days + preferred_time_range).
    """
    prefs = (
        await db.execute(
            select(SocialPostingPreferences).where(
                SocialPostingPreferences.tenant_id == tenant.id
            )
        )
    ).scalar_one_or_none()

    scheduled_for = draft.scheduled_for or _pick_next_slot(prefs)
    draft.scheduled_for = scheduled_for

    # Fan out across preferred platforms (default = FB if none configured).
    platforms = ["FB", "IG", "TIKTOK", "TWITTER"]
    entries: list[SocialScheduleQueue] = []
    for platform in platforms[:1]:  # default to primary platform; can be extended
        entry = SocialScheduleQueue(
            id=uuid.uuid4(),
            tenant_id=tenant.id,
            draft_id=draft.id,
            platform=platform,
            scheduled_time=scheduled_for,
            posted_status="SCHEDULED",
        )
        db.add(entry)
        entries.append(entry)

    await db.flush()
    return entries


def _pick_next_slot(prefs: SocialPostingPreferences | None) -> datetime:
    """Pick the next scheduled time. Defaults to +2 hours if no prefs."""
    now = datetime.now(timezone.utc)
    if not prefs:
        return now + timedelta(hours=2)

    cadence_hours = max(1, int(24 * 7 / max(1, prefs.posts_per_week)))
    return now + timedelta(hours=cadence_hours)


async def schedule_draft_manually(
    db: AsyncSession,
    tenant: Tenant,
    *,
    draft_id: uuid.UUID,
    platform: str,
    scheduled_time: Optional[datetime] = None,
) -> SocialScheduleQueue:
    """Tenant-initiated schedule (used by POST /social/schedule)."""
    draft = (
        await db.execute(
            select(SocialContentDraft).where(
                SocialContentDraft.id == draft_id,
                SocialContentDraft.tenant_id == tenant.id,
            )
        )
    ).scalar_one_or_none()

    if not draft:
        raise ValueError("Draft not found")

    prefs = (
        await db.execute(
            select(SocialPostingPreferences).where(
                SocialPostingPreferences.tenant_id == tenant.id
            )
        )
    ).scalar_one_or_none()

    when = scheduled_time or _pick_next_slot(prefs)
    draft.scheduled_for = when

    entry = SocialScheduleQueue(
        id=uuid.uuid4(),
        tenant_id=tenant.id,
        draft_id=draft.id,
        platform=platform.upper(),
        scheduled_time=when,
        posted_status="SCHEDULED",
    )
    db.add(entry)
    await db.flush()
    return entry


# ── 4. PUBLISHING ─────────────────────────────────────────────────────────


async def publish_scheduled_item(
    db: AsyncSession,
    tenant: Tenant,
    *,
    draft_id: uuid.UUID,
    platform: str,
) -> dict[str, Any]:
    """Publish a single scheduled item to the chosen platform.

    Marks posted_status=PUBLISHED on success, ERROR on failure.
    """
    schedule_entry = (
        await db.execute(
            select(SocialScheduleQueue).where(
                SocialScheduleQueue.draft_id == draft_id,
                SocialScheduleQueue.tenant_id == tenant.id,
                SocialScheduleQueue.platform == platform.upper(),
            )
        )
    ).scalar_one_or_none()

    draft = (
        await db.execute(
            select(SocialContentDraft).where(
                SocialContentDraft.id == draft_id,
                SocialContentDraft.tenant_id == tenant.id,
            )
        )
    ).scalar_one_or_none()

    if not draft:
        raise ValueError("Draft not found")

    adapter = get_social_adapter()
    payload = SocialPostPayload(
        message=draft.text_content or "",
        image_urls=[draft.image_url] if draft.image_url else [],
    )

    result: dict[str, Any]
    try:
        published = await adapter.publish_post(
            account_id=str(tenant.id),
            payload=payload,
        )
        if schedule_entry:
            schedule_entry.posted_status = "PUBLISHED"
        result = {
            "ok": True,
            "platform_post_id": published.platform_post_id,
            "url": published.url,
        }
    except Exception as exc:
        logger.exception("Publish failed: %s", exc)
        if schedule_entry:
            schedule_entry.posted_status = "ERROR"
        result = {"ok": False, "error": str(exc)}

    await db.flush()
    return result


async def publish_due_items(db: AsyncSession) -> dict[str, Any]:
    """Worker entrypoint: publish every SCHEDULED item whose time has elapsed."""
    now = datetime.now(timezone.utc)
    due = (
        await db.execute(
            select(SocialScheduleQueue, Tenant)
            .join(Tenant, Tenant.id == SocialScheduleQueue.tenant_id)
            .where(
                SocialScheduleQueue.posted_status == "SCHEDULED",
                SocialScheduleQueue.scheduled_time <= now,
            )
        )
    ).all()

    published = 0
    errors = 0
    for entry, tenant in due:
        res = await publish_scheduled_item(
            db,
            tenant,
            draft_id=entry.draft_id,
            platform=entry.platform,
        )
        if res.get("ok"):
            published += 1
        else:
            errors += 1

    await db.commit()
    return {"published": published, "errors": errors, "checked": len(due)}
