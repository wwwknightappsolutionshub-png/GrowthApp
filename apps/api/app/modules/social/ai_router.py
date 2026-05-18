"""AI Social Module — tenant-facing endpoints.

POST /social/brand-identity/set
POST /social/samples/upload
POST /social/prefs/set
POST /social/generate-drafts
POST /social/send-for-approval
POST /social/approval/webhook
POST /social/schedule
POST /social/publish
"""
from __future__ import annotations

import uuid
from typing import Any, Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import CurrentTenantContext
from app.modules.social import ai_service
from app.modules.social.models import (
    SocialBrandIdentity,
    SocialSampleUploads,
    SocialPostingPreferences,
    SocialContentDraft,
    SocialApprovalQueue,
    SocialScheduleQueue,
)

ai_router = APIRouter(prefix="/social", tags=["AI Social"])


# ── Schemas ────────────────────────────────────────────────────────────────

class BrandIdentityIn(BaseModel):
    brand_colors: dict = {}
    brand_fonts: dict = {}
    tone_of_voice: Optional[str] = None
    logo_url: Optional[str] = None


class SampleUploadIn(BaseModel):
    file_url: str
    file_type: str  # IMAGE, VIDEO, PDF


class PostingPrefsIn(BaseModel):
    posts_per_week: int = 3
    preferred_days: list = []
    preferred_time_range: Optional[str] = None


class GenerateDraftsIn(BaseModel):
    count: int = 3
    topic_hints: Optional[list[str]] = None


class SendForApprovalIn(BaseModel):
    draft_id: str
    delivery_channel: str  # EMAIL, WHATSAPP
    recipient_email: Optional[str] = None
    recipient_whatsapp: Optional[str] = None


class ApprovalWebhookIn(BaseModel):
    draft_id: str
    response_text: str
    approved: bool


class ScheduleIn(BaseModel):
    draft_id: str
    platform: str  # FB, IG, TIKTOK, TWITTER
    scheduled_time: Optional[str] = None


class PublishIn(BaseModel):
    draft_id: str
    platform: str


# ── Endpoints ──────────────────────────────────────────────────────────────

@ai_router.post("/brand-identity/set")
async def set_brand_identity(
    body: BrandIdentityIn,
    ctx: CurrentTenantContext,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    _, tenant, _ = ctx
    existing = (
        await db.execute(
            select(SocialBrandIdentity).where(SocialBrandIdentity.tenant_id == tenant.id)
        )
    ).scalar_one_or_none()

    if existing:
        existing.brand_colors = body.brand_colors
        existing.brand_fonts = body.brand_fonts
        existing.tone_of_voice = body.tone_of_voice
        existing.logo_url = body.logo_url
    else:
        existing = SocialBrandIdentity(
            id=uuid.uuid4(),
            tenant_id=tenant.id,
            brand_colors=body.brand_colors,
            brand_fonts=body.brand_fonts,
            tone_of_voice=body.tone_of_voice,
            logo_url=body.logo_url,
        )
        db.add(existing)

    await db.commit()
    return {"ok": True, "message": "Brand identity saved"}


@ai_router.post("/samples/upload")
async def upload_sample(
    body: SampleUploadIn,
    ctx: CurrentTenantContext,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    _, tenant, _ = ctx
    upload = SocialSampleUploads(
        id=uuid.uuid4(),
        tenant_id=tenant.id,
        file_url=body.file_url,
        file_type=body.file_type.upper(),
    )
    db.add(upload)
    await db.commit()
    return {"ok": True, "id": str(upload.id)}


@ai_router.post("/prefs/set")
async def set_posting_prefs(
    body: PostingPrefsIn,
    ctx: CurrentTenantContext,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    _, tenant, _ = ctx
    existing = (
        await db.execute(
            select(SocialPostingPreferences).where(
                SocialPostingPreferences.tenant_id == tenant.id
            )
        )
    ).scalar_one_or_none()

    if existing:
        existing.posts_per_week = body.posts_per_week
        existing.preferred_days = body.preferred_days
        existing.preferred_time_range = body.preferred_time_range
    else:
        existing = SocialPostingPreferences(
            id=uuid.uuid4(),
            tenant_id=tenant.id,
            posts_per_week=body.posts_per_week,
            preferred_days=body.preferred_days,
            preferred_time_range=body.preferred_time_range,
        )
        db.add(existing)

    await db.commit()
    return {"ok": True, "message": "Posting preferences saved"}


@ai_router.post("/generate-drafts")
async def generate_drafts(
    body: GenerateDraftsIn,
    ctx: CurrentTenantContext,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    _, tenant, _ = ctx
    drafts = []
    for i in range(body.count):
        topic = (body.topic_hints[i] if body.topic_hints and i < len(body.topic_hints) else None)
        draft = await ai_service.generate_draft_for_tenant(db, tenant, topic_hint=topic)
        drafts.append(str(draft.id))
    await db.commit()
    return {"ok": True, "draft_ids": drafts, "count": len(drafts)}


@ai_router.post("/send-for-approval")
async def send_for_approval(
    body: SendForApprovalIn,
    ctx: CurrentTenantContext,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    user, tenant, _ = ctx
    draft = (
        await db.execute(
            select(SocialContentDraft).where(
                SocialContentDraft.id == uuid.UUID(body.draft_id),
                SocialContentDraft.tenant_id == tenant.id,
            )
        )
    ).scalar_one_or_none()
    if not draft:
        return {"ok": False, "error": "Draft not found"}

    email_to = body.recipient_email or (user.email if body.delivery_channel.upper() == "EMAIL" else None)
    whatsapp_to = body.recipient_whatsapp or (None if body.delivery_channel.upper() == "EMAIL" else None)

    entries = await ai_service.send_draft_for_approval(
        db, tenant, draft,
        recipient_email=email_to,
        recipient_whatsapp=whatsapp_to,
    )
    await db.commit()
    return {
        "ok": True,
        "approval_ids": [str(e.id) for e in entries],
        "channels": [e.delivery_channel for e in entries],
    }


@ai_router.post("/approval/webhook")
async def approval_webhook(
    body: ApprovalWebhookIn,
    ctx: CurrentTenantContext,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    _, tenant, _ = ctx
    draft = await ai_service.record_approval_response(
        db, tenant,
        draft_id=uuid.UUID(body.draft_id),
        response_text=body.response_text,
        approved=body.approved,
    )
    await db.commit()
    if not draft:
        return {"ok": False, "error": "Draft not found"}
    return {"ok": True, "status": draft.status}


@ai_router.post("/schedule")
async def schedule_post(
    body: ScheduleIn,
    ctx: CurrentTenantContext,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    from datetime import datetime
    _, tenant, _ = ctx
    when = None
    if body.scheduled_time:
        try:
            when = datetime.fromisoformat(body.scheduled_time.replace("Z", "+00:00"))
        except ValueError:
            when = None

    try:
        entry = await ai_service.schedule_draft_manually(
            db, tenant,
            draft_id=uuid.UUID(body.draft_id),
            platform=body.platform,
            scheduled_time=when,
        )
    except ValueError as exc:
        return {"ok": False, "error": str(exc)}

    await db.commit()
    return {
        "ok": True,
        "schedule_id": str(entry.id),
        "scheduled_time": entry.scheduled_time.isoformat() if entry.scheduled_time else None,
    }


@ai_router.post("/publish")
async def publish_post(
    body: PublishIn,
    ctx: CurrentTenantContext,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    _, tenant, _ = ctx
    try:
        result = await ai_service.publish_scheduled_item(
            db, tenant,
            draft_id=uuid.UUID(body.draft_id),
            platform=body.platform,
        )
    except ValueError as exc:
        return {"ok": False, "error": str(exc)}
    await db.commit()
    return {"platform": body.platform.upper(), **result}
