"""Auto-reply service.

Two entry points:

  * `draft_reply_for_inbound` — called from the inbound-message handler.
    Picks a rule (or AI fallback) and persists a pending AutoReply row.
  * `approve_and_send` — staff approves a pending row; we send through the
    channel adapter and mark sent.

Rules can be tenant-specific JSON in the future. For now we ship one
"AI draft" path that always runs.
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters import get_email_adapter, get_sms_adapter, get_whatsapp_adapter
from app.adapters.email.base import EmailMessage
from app.adapters.sms.base import SMSMessage
from app.adapters.whatsapp.base import WhatsAppMessage
from app.core.audit import log_action
from app.core.exceptions import NotFoundException, ValidationException
from app.modules.auto_replies.models import AutoReply
from app.modules.messaging.models import Conversation, Message
from app.modules.tenants.models import Tenant
from app.services.ai.prompts import AUTO_REPLY_SYSTEM
from app.services.ai.router import get_ai_router
from app.services.ai.types import AIRouterError

logger = logging.getLogger(__name__)


async def draft_reply_for_inbound(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    *,
    inbound_message: Message,
) -> AutoReply | None:
    """Generate an AI draft reply for an inbound message.

    Returns None if AI is unavailable or the inbound looks like opt-out / spam.
    """
    body = (inbound_message.body or "").strip()
    if not body:
        return None
    lower = body.lower()
    # Respect opt-out keywords — never auto-reply.
    if any(k in lower for k in ("stop", "unsubscribe", "opt out", "do not contact")):
        return None

    conversation = (
        await db.execute(select(Conversation).where(Conversation.id == inbound_message.conversation_id))
    ).scalar_one_or_none()
    if not conversation:
        return None

    tenant = (
        await db.execute(select(Tenant).where(Tenant.id == tenant_id))
    ).scalar_one_or_none()
    biz_name = tenant.name if tenant else "the business"
    biz_type = tenant.business_type if tenant else "SMB"

    router = get_ai_router()
    try:
        response = await router.chat(
            messages=[
                {"role": "system", "content": AUTO_REPLY_SYSTEM},
                {
                    "role": "user",
                    "content": (
                        f"Business: {biz_name} ({biz_type})\n"
                        f"Channel: {inbound_message.channel}\n"
                        f"Customer message:\n{body}\n\n"
                        "Draft a reply to send. Output ONLY the reply text."
                    ),
                },
            ],
            tenant_id=tenant_id,
            purpose="auto_reply_draft",
            max_tokens=200,
            temperature=0.5,
        )
    except AIRouterError as exc:
        logger.warning("Auto-reply draft failed for tenant %s: %s", tenant_id, exc)
        return None

    draft = response.content.strip()
    if not draft:
        return None

    row = AutoReply(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        conversation_id=conversation.id,
        inbound_message_id=inbound_message.id,
        channel=inbound_message.channel,
        draft=draft,
        status="pending",
        provider=response.provider,
        model=response.model,
        rule="ai_default",
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)

    # Notify the team (best-effort).
    try:
        from app.modules.notifications import service as notif_svc

        await notif_svc.create_notification(
            db,
            tenant_id=tenant_id,
            user_id=None,
            kind="message.inbound",
            title="AI reply ready for review",
            body=draft[:140],
            link=f"/messages?auto_reply={row.id}",
            extra={"auto_reply_id": str(row.id), "channel": inbound_message.channel},
        )
    except Exception:
        logger.exception("Auto-reply notification failed")

    return row


async def approve_and_send(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    reply_id: uuid.UUID,
    *,
    user_id: uuid.UUID,
    override_text: str | None = None,
) -> AutoReply:
    row = (
        await db.execute(
            select(AutoReply).where(AutoReply.id == reply_id, AutoReply.tenant_id == tenant_id)
        )
    ).scalar_one_or_none()
    if not row:
        raise NotFoundException("AutoReply")
    if row.status not in ("pending", "approved"):
        raise ValidationException("Reply already actioned")

    text = (override_text or row.draft).strip()
    if not text:
        raise ValidationException("Reply text is empty")

    # Send via the right channel adapter.
    conversation = (
        await db.execute(select(Conversation).where(Conversation.id == row.conversation_id))
    ).scalar_one()
    recipient = conversation.customer_phone or conversation.customer_email or ""
    if not recipient:
        raise ValidationException("Conversation has no contact details")

    try:
        if row.channel == "sms":
            await get_sms_adapter().send(SMSMessage(to=recipient, body=text))
        elif row.channel == "whatsapp":
            await get_whatsapp_adapter().send(WhatsAppMessage(to=recipient, body=text))
        elif row.channel == "email":
            await get_email_adapter().send(EmailMessage(
                to=recipient, subject="Re: your enquiry", html_body=f"<p>{text}</p>"
            ))
        else:
            raise ValidationException(f"Unknown channel '{row.channel}'")
    except Exception as exc:
        logger.error("Auto-reply send failed: %s", exc)
        row.status = "pending"
        db.add(row)
        await db.commit()
        raise ValidationException(f"Send failed: {exc}") from exc

    now = datetime.now(timezone.utc)
    row.draft = text
    row.status = "sent"
    row.reviewed_by_user_id = user_id
    row.reviewed_at = now
    row.sent_at = now
    db.add(row)

    # Persist as an outbound Message so conversation history stays accurate.
    outbound = Message(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        conversation_id=conversation.id,
        direction="outbound",
        channel=row.channel,
        to_address=recipient,
        body=text,
        status="sent",
    )
    conversation.last_message_at = now
    db.add(outbound)
    db.add(conversation)
    await log_action(
        db,
        action="auto_reply.approved",
        resource="auto_reply",
        resource_id=row.id,
        tenant_id=tenant_id,
        user_id=user_id,
        metadata={"channel": row.channel, "message_id": str(outbound.id)},
    )
    await db.commit()
    await db.refresh(row)
    return row


async def reject(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    reply_id: uuid.UUID,
    *,
    user_id: uuid.UUID,
) -> AutoReply:
    row = (
        await db.execute(
            select(AutoReply).where(AutoReply.id == reply_id, AutoReply.tenant_id == tenant_id)
        )
    ).scalar_one_or_none()
    if not row:
        raise NotFoundException("AutoReply")
    row.status = "rejected"
    row.reviewed_by_user_id = user_id
    row.reviewed_at = datetime.now(timezone.utc)
    db.add(row)
    await log_action(
        db,
        action="auto_reply.rejected",
        resource="auto_reply",
        resource_id=row.id,
        tenant_id=tenant_id,
        user_id=user_id,
        metadata={"channel": row.channel},
    )
    await db.commit()
    await db.refresh(row)
    return row
