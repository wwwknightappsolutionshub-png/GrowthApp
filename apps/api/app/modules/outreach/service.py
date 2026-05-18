"""Outreach campaign service.

Public API used by router + worker:

  * `create_campaign`, `update_campaign`, `delete_campaign`
  * `launch_campaign`, `pause_campaign`, `resume_campaign`
  * `enrol_customers`            – called on launch
  * `process_due_enrolments`     – cron, picks active enrolments due now
  * `ai_draft_step`              – AI helper to write step copy
  * `mark_replied`               – inbound message hook can call this
  * `create_winback_preset`      – one-click "Re-engage inactive customers"
  * `campaign_stats`             – numeric rollup for the list/detail view
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters import get_email_adapter, get_sms_adapter, get_whatsapp_adapter
from app.adapters.email.base import EmailMessage
from app.adapters.sms.base import SMSMessage
from app.adapters.whatsapp.base import WhatsAppMessage
from app.core.audit import log_action
from app.core.exceptions import NotFoundException, ValidationException
from app.modules.crm.models import Customer
from app.modules.outreach.models import (
    OutreachCampaign,
    OutreachEnrolment,
    OutreachSend,
)
from app.modules.outreach.schemas import (
    AIStepDraftRequest,
    CampaignCreate,
    CampaignUpdate,
    CampaignStep,
    WinbackPresetRequest,
)
from app.modules.segments.service import list_segment_member_ids
from app.modules.tenants.models import Tenant
from app.services.ai.router import get_ai_router
from app.services.ai.types import AIRouterError

logger = logging.getLogger(__name__)

ALLOWED_TRANSITIONS = {
    "draft": {"scheduled", "running"},
    "scheduled": {"running", "draft"},
    "running": {"paused", "completed"},
    "paused": {"running", "completed"},
    "completed": set(),
}


def _channels_from_steps(steps: list[CampaignStep] | list[dict]) -> list[str]:
    out: list[str] = []
    for s in steps or []:
        ch = s.channel if isinstance(s, CampaignStep) else s.get("channel")
        if ch and ch not in out:
            out.append(ch)
    return out


async def create_campaign(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
    data: CampaignCreate,
) -> OutreachCampaign:
    campaign = OutreachCampaign(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        name=data.name,
        description=data.description,
        kind=data.kind,
        audience=data.audience.model_dump(mode="json", exclude_none=True),
        steps=[s.model_dump(mode="json") for s in data.steps],
        channels=_channels_from_steps(data.steps) or data.channels,
        status="draft",
        scheduled_at=data.scheduled_at,
        created_by_user_id=user_id,
    )
    db.add(campaign)
    await db.commit()
    await db.refresh(campaign)
    await log_action(
        db,
        action="outreach.campaign.create",
        resource="outreach_campaign",
        resource_id=campaign.id,
        user_id=user_id,
        tenant_id=tenant_id,
        metadata={"name": campaign.name, "kind": campaign.kind},
    )
    await db.commit()
    return campaign


async def update_campaign(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
    campaign_id: uuid.UUID,
    data: CampaignUpdate,
) -> OutreachCampaign:
    campaign = await _get(db, tenant_id, campaign_id)
    if campaign.status not in ("draft", "scheduled", "paused"):
        raise ValidationException("Cannot edit a running or completed campaign")
    if data.name is not None:
        campaign.name = data.name
    if data.description is not None:
        campaign.description = data.description
    if data.audience is not None:
        campaign.audience = data.audience.model_dump(mode="json", exclude_none=True)
    if data.steps is not None:
        campaign.steps = [s.model_dump(mode="json") for s in data.steps]
        campaign.channels = _channels_from_steps(data.steps)
    elif data.channels is not None:
        campaign.channels = data.channels
    if data.scheduled_at is not None:
        campaign.scheduled_at = data.scheduled_at
    db.add(campaign)
    await db.commit()
    await db.refresh(campaign)
    await log_action(
        db,
        action="outreach.campaign.update",
        resource="outreach_campaign",
        resource_id=campaign.id,
        user_id=user_id,
        tenant_id=tenant_id,
    )
    await db.commit()
    return campaign


async def delete_campaign(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
    campaign_id: uuid.UUID,
) -> None:
    campaign = await _get(db, tenant_id, campaign_id)
    await db.delete(campaign)
    await log_action(
        db,
        action="outreach.campaign.delete",
        resource="outreach_campaign",
        resource_id=campaign_id,
        user_id=user_id,
        tenant_id=tenant_id,
    )
    await db.commit()


async def launch_campaign(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
    campaign_id: uuid.UUID,
) -> OutreachCampaign:
    campaign = await _get(db, tenant_id, campaign_id)
    if not campaign.steps:
        raise ValidationException("Campaign has no steps")
    if "running" not in ALLOWED_TRANSITIONS.get(campaign.status, set()):
        raise ValidationException(f"Cannot launch a {campaign.status} campaign")

    enrolled = await enrol_customers(db, campaign)
    campaign.status = "running"
    campaign.started_at = campaign.started_at or datetime.now(timezone.utc)
    campaign.enrolled_count = enrolled
    db.add(campaign)
    await db.commit()
    await db.refresh(campaign)
    await log_action(
        db,
        action="outreach.campaign.launch",
        resource="outreach_campaign",
        resource_id=campaign.id,
        user_id=user_id,
        tenant_id=tenant_id,
        metadata={"enrolled": enrolled},
    )
    await db.commit()
    return campaign


async def pause_campaign(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
    campaign_id: uuid.UUID,
) -> OutreachCampaign:
    campaign = await _get(db, tenant_id, campaign_id)
    if "paused" not in ALLOWED_TRANSITIONS.get(campaign.status, set()):
        raise ValidationException(f"Cannot pause a {campaign.status} campaign")
    campaign.status = "paused"
    campaign.paused_at = datetime.now(timezone.utc)
    db.add(campaign)
    await db.commit()
    await db.refresh(campaign)
    await log_action(
        db,
        action="outreach.campaign.pause",
        resource="outreach_campaign",
        resource_id=campaign.id,
        user_id=user_id,
        tenant_id=tenant_id,
    )
    await db.commit()
    return campaign


async def resume_campaign(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
    campaign_id: uuid.UUID,
) -> OutreachCampaign:
    campaign = await _get(db, tenant_id, campaign_id)
    if "running" not in ALLOWED_TRANSITIONS.get(campaign.status, set()):
        raise ValidationException(f"Cannot resume a {campaign.status} campaign")
    campaign.status = "running"
    campaign.paused_at = None
    db.add(campaign)
    await db.commit()
    await db.refresh(campaign)
    return campaign


async def _get(db: AsyncSession, tenant_id: uuid.UUID, campaign_id: uuid.UUID) -> OutreachCampaign:
    row = (
        await db.execute(
            select(OutreachCampaign).where(
                OutreachCampaign.id == campaign_id, OutreachCampaign.tenant_id == tenant_id
            )
        )
    ).scalar_one_or_none()
    if not row:
        raise NotFoundException("OutreachCampaign")
    return row


# ── Audience resolution ──────────────────────────────────────────────────────

async def _resolve_audience(
    db: AsyncSession, tenant_id: uuid.UUID, audience: dict[str, Any]
) -> list[uuid.UUID]:
    if not audience:
        return []
    segment_id = audience.get("segment_id")
    rules = audience.get("filter")
    if segment_id:
        from app.modules.segments.models import CustomerSegment

        seg = (
            await db.execute(
                select(CustomerSegment).where(
                    CustomerSegment.id == segment_id,
                    CustomerSegment.tenant_id == tenant_id,
                )
            )
        ).scalar_one_or_none()
        if not seg:
            return []
        rules = seg.rules or {}
    if rules is None:
        return []
    return await list_segment_member_ids(db, tenant_id, rules, limit=10_000)


# ── Enrolment ────────────────────────────────────────────────────────────────

async def enrol_customers(
    db: AsyncSession,
    campaign: OutreachCampaign,
) -> int:
    customer_ids = await _resolve_audience(db, campaign.tenant_id, campaign.audience or {})
    if not customer_ids:
        return 0

    existing = set(
        (
            await db.execute(
                select(OutreachEnrolment.customer_id).where(
                    OutreachEnrolment.campaign_id == campaign.id,
                    OutreachEnrolment.customer_id.in_(customer_ids),
                )
            )
        ).scalars().all()
    )
    fresh = [cid for cid in customer_ids if cid not in existing]
    if not fresh:
        return 0

    now = datetime.now(timezone.utc)
    first_delay = (campaign.steps[0] or {}).get("delay_hours", 0) if campaign.steps else 0
    next_run = now + timedelta(hours=int(first_delay))
    for cid in fresh:
        db.add(
            OutreachEnrolment(
                id=uuid.uuid4(),
                tenant_id=campaign.tenant_id,
                campaign_id=campaign.id,
                customer_id=cid,
                current_step=0,
                status="active",
                next_run_at=next_run,
            )
        )
    await db.commit()
    return len(fresh)


# ── Worker dispatch loop ─────────────────────────────────────────────────────

async def process_due_enrolments(db: AsyncSession, limit: int = 100) -> int:
    """Send the next step for any active enrolment whose next_run_at <= now.

    Returns the number of sends attempted in this batch.
    """
    now = datetime.now(timezone.utc)
    enrolments = (
        await db.execute(
            select(OutreachEnrolment)
            .where(
                OutreachEnrolment.status == "active",
                OutreachEnrolment.next_run_at <= now,
            )
            .order_by(OutreachEnrolment.next_run_at.asc())
            .limit(limit)
        )
    ).scalars().all()

    if not enrolments:
        return 0

    sent = 0
    for enrol in enrolments:
        try:
            await _dispatch_one(db, enrol)
            sent += 1
        except Exception:
            logger.exception("outreach dispatch failed for enrolment %s", enrol.id)
            enrol.error_message = "dispatch failed"
            db.add(enrol)
            await db.commit()
    return sent


async def _dispatch_one(db: AsyncSession, enrol: OutreachEnrolment) -> None:
    campaign = (
        await db.execute(
            select(OutreachCampaign).where(OutreachCampaign.id == enrol.campaign_id)
        )
    ).scalar_one_or_none()
    if not campaign or campaign.status != "running":
        return

    steps: list[dict] = campaign.steps or []
    if enrol.current_step >= len(steps):
        enrol.status = "completed"
        enrol.completed_at = datetime.now(timezone.utc)
        db.add(enrol)
        await db.commit()
        return

    step = steps[enrol.current_step]
    cond = step.get("condition", "always")
    if cond == "no_reply" and enrol.replied_at is not None:
        enrol.status = "replied"
        enrol.completed_at = datetime.now(timezone.utc)
        db.add(enrol)
        await db.commit()
        return
    if cond == "replied" and enrol.replied_at is None:
        # Skip this step.
        return await _advance(db, campaign, enrol, sent=False)

    customer = (
        await db.execute(select(Customer).where(Customer.id == enrol.customer_id))
    ).scalar_one_or_none()
    if not customer:
        enrol.status = "failed"
        enrol.error_message = "customer missing"
        db.add(enrol)
        await db.commit()
        return

    tenant = (
        await db.execute(select(Tenant).where(Tenant.id == enrol.tenant_id))
    ).scalar_one()
    rendered_body = _render(step.get("body", ""), customer, tenant)
    rendered_subject = _render(step.get("subject") or "", customer, tenant)

    channel = step["channel"]
    status = "sent"
    error: str | None = None
    provider_id: str | None = None

    try:
        if channel == "sms":
            if not customer.phone:
                raise ValueError("customer has no phone")
            res = await get_sms_adapter().send(SMSMessage(to=customer.phone, body=rendered_body))
            provider_id = getattr(res, "provider_id", None)
            if getattr(res, "status", "sent") == "failed":
                raise ValueError(getattr(res, "error", "sms send failed"))
        elif channel == "whatsapp":
            if not customer.phone:
                raise ValueError("customer has no phone")
            res = await get_whatsapp_adapter().send(
                WhatsAppMessage(to=customer.phone, body=rendered_body)
            )
            provider_id = getattr(res, "provider_id", None)
            if getattr(res, "status", "sent") == "failed":
                raise ValueError(getattr(res, "error", "whatsapp send failed"))
        elif channel == "email":
            if not customer.email:
                raise ValueError("customer has no email")
            html = f"<p>{rendered_body.replace(chr(10), '<br/>')}</p>"
            provider_id = await get_email_adapter().send(
                EmailMessage(
                    to=customer.email,
                    subject=rendered_subject or f"A quick note from {tenant.name}",
                    html_body=html,
                    text_body=rendered_body,
                )
            )
        else:
            raise ValueError(f"unknown channel {channel}")
    except Exception as exc:
        status = "failed"
        error = str(exc)

    db.add(
        OutreachSend(
            id=uuid.uuid4(),
            tenant_id=enrol.tenant_id,
            campaign_id=campaign.id,
            enrolment_id=enrol.id,
            step_index=enrol.current_step,
            channel=channel,
            status=status,
            provider_message_id=provider_id,
            subject=rendered_subject or None,
            body=rendered_body,
            error_message=error,
        )
    )
    if status == "sent":
        campaign.sent_count = (campaign.sent_count or 0) + 1
        enrol.last_sent_at = datetime.now(timezone.utc)
    db.add(campaign)
    db.add(enrol)
    await db.commit()
    await _advance(db, campaign, enrol, sent=status == "sent")


async def _advance(
    db: AsyncSession,
    campaign: OutreachCampaign,
    enrol: OutreachEnrolment,
    *,
    sent: bool,
) -> None:
    """Move enrolment to the next step (or complete it)."""
    next_idx = enrol.current_step + 1
    steps = campaign.steps or []
    if next_idx >= len(steps):
        enrol.status = "completed"
        enrol.completed_at = datetime.now(timezone.utc)
        enrol.next_run_at = None
    else:
        next_step = steps[next_idx]
        enrol.current_step = next_idx
        delay = int(next_step.get("delay_hours", 0) or 0)
        enrol.next_run_at = datetime.now(timezone.utc) + timedelta(hours=delay)
    db.add(enrol)
    await db.commit()


def _render(template: str, customer: Customer, tenant: Tenant) -> str:
    """Tiny mustache-lite renderer for personalisation tokens."""
    if not template:
        return template
    replacements = {
        "{{first_name}}": customer.first_name or "",
        "{{last_name}}": customer.last_name or "",
        "{{full_name}}": " ".join(filter(None, [customer.first_name, customer.last_name])).strip(),
        "{{business_name}}": tenant.name or "",
        "{{business_phone}}": tenant.phone or "",
    }
    out = template
    for k, v in replacements.items():
        out = out.replace(k, v)
    return out


# ── Inbound reply hook ───────────────────────────────────────────────────────

async def mark_replied(
    db: AsyncSession, tenant_id: uuid.UUID, customer_id: uuid.UUID
) -> int:
    """Mark active enrolments for this customer as replied."""
    now = datetime.now(timezone.utc)
    enrolments = (
        await db.execute(
            select(OutreachEnrolment).where(
                OutreachEnrolment.tenant_id == tenant_id,
                OutreachEnrolment.customer_id == customer_id,
                OutreachEnrolment.status == "active",
            )
        )
    ).scalars().all()
    if not enrolments:
        return 0
    for e in enrolments:
        e.replied_at = now
        # Find campaign; only auto-complete if remaining steps are all 'no_reply'.
        campaign = (
            await db.execute(
                select(OutreachCampaign).where(OutreachCampaign.id == e.campaign_id)
            )
        ).scalar_one()
        remaining = campaign.steps[e.current_step :] if campaign.steps else []
        if all((s.get("condition") in ("no_reply", "always")) for s in remaining):
            e.status = "replied"
            e.completed_at = now
            e.next_run_at = None
        campaign.replied_count = (campaign.replied_count or 0) + 1
        db.add(campaign)
        db.add(e)
    await db.commit()
    return len(enrolments)


# ── AI step drafter ──────────────────────────────────────────────────────────

_DRAFT_SYSTEM = (
    "You are a senior copywriter for UK SMB outreach. Output ONLY JSON: "
    '{"subject": "...", "body": "..."}. '
    "Use British English. Keep SMS bodies ≤ 160 chars. Keep email subjects ≤ 65 chars. "
    "Personalisation tokens allowed: {{first_name}}, {{full_name}}, {{business_name}}, "
    "{{business_phone}}. Never invent statistics, prices, or facts. Be warm and concise."
)


async def ai_draft_step(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
    req: AIStepDraftRequest,
) -> dict:
    import json

    tenant = (
        await db.execute(select(Tenant).where(Tenant.id == tenant_id))
    ).scalar_one()
    user_prompt = (
        f"Business: {tenant.name} ({tenant.business_type})\n"
        f"Channel: {req.channel}\n"
        f"Goal of this step: {req.goal}\n"
        f"Audience hint: {req.audience_hint or 'general customers'}\n"
        f"Tone: {req.tone}\n"
        "Return JSON only."
    )
    router_svc = get_ai_router()
    try:
        response = await router_svc.chat(
            messages=[
                {"role": "system", "content": _DRAFT_SYSTEM},
                {"role": "user", "content": user_prompt},
            ],
            tenant_id=tenant_id,
            user_id=user_id,
            purpose="outreach_step_draft",
            max_tokens=400,
            temperature=0.5,
        )
    except AIRouterError as exc:
        raise ValidationException(f"AI router unavailable: {exc}") from exc

    raw = (response.content or "").strip()
    if raw.startswith("```"):
        raw = raw.strip("`")
        if raw.lower().startswith("json"):
            raw = raw[4:]
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        start = raw.find("{")
        end = raw.rfind("}")
        parsed = {}
        if start != -1 and end != -1:
            try:
                parsed = json.loads(raw[start : end + 1])
            except json.JSONDecodeError:
                pass

    body = str(parsed.get("body") or raw[:1000]).strip()
    subject = parsed.get("subject")
    if req.channel != "email":
        subject = None
    return {
        "subject": subject,
        "body": body,
        "provider": response.provider,
        "model": response.model,
    }


# ── Winback preset ───────────────────────────────────────────────────────────

async def create_winback_preset(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
    req: WinbackPresetRequest,
) -> OutreachCampaign:
    """One-click win-back campaign: target customers with no deal in N days."""
    rules: dict[str, Any] = {
        "all": [
            {
                "field": "last_deal_at",
                "op": "older_than_days",
                "value": req.inactive_days,
            }
        ]
    }
    if req.channel == "email":
        rules["all"].append({"field": "email", "op": "not_empty"})
    else:
        rules["all"].append({"field": "phone", "op": "not_empty"})

    intro = CampaignStep(
        channel=req.channel,
        label="Win-back outreach",
        delay_hours=0,
        body=(
            "Hi {{first_name}},\n\n"
            "We've not seen you in a while at {{business_name}}. "
            f"{req.offer.strip()}\n\nReply to this message to get started."
        ),
        subject=("We'd love to see you again" if req.channel == "email" else None),
    )
    nudge = CampaignStep(
        channel=req.channel,
        label="Nudge if no reply",
        delay_hours=72,
        condition="no_reply",
        body=(
            "Hi {{first_name}}, just a quick nudge. Our offer is still open — "
            "let us know if you'd like to take us up on it."
        ),
        subject=("A quick nudge" if req.channel == "email" else None),
    )

    return await create_campaign(
        db,
        tenant_id,
        user_id,
        CampaignCreate(
            name=req.name or f"Win-back: {req.inactive_days}-day inactive",
            description="Auto-generated win-back campaign",
            kind="winback",
            channels=[req.channel],
            audience={"filter": rules},  # type: ignore[arg-type]
            steps=[intro, nudge],
        ),
    )


# ── Stats ────────────────────────────────────────────────────────────────────

async def campaign_stats(
    db: AsyncSession, tenant_id: uuid.UUID, campaign_id: uuid.UUID
) -> dict:
    campaign = await _get(db, tenant_id, campaign_id)
    enrolled = campaign.enrolled_count or 0
    statuses = dict(
        (
            await db.execute(
                select(OutreachEnrolment.status, func.count(OutreachEnrolment.id))
                .where(OutreachEnrolment.campaign_id == campaign_id)
                .group_by(OutreachEnrolment.status)
            )
        ).all()
    )
    sent = campaign.sent_count or 0
    replied = campaign.replied_count or 0
    unsub = campaign.unsubscribed_count or 0
    return {
        "campaign_id": campaign_id,
        "enrolled": enrolled,
        "active": int(statuses.get("active", 0)),
        "sent": sent,
        "replied": replied,
        "unsubscribed": unsub,
        "completed": int(statuses.get("completed", 0)),
        "reply_rate_pct": round((replied / sent * 100.0) if sent else 0.0, 1),
        "unsub_rate_pct": round((unsub / sent * 100.0) if sent else 0.0, 1),
    }
