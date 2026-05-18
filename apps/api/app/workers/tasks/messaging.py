import logging
import uuid
from datetime import datetime, timezone

from sqlalchemy import select, update

from app.adapters import get_email_adapter, get_sms_adapter, get_whatsapp_adapter
from app.adapters.email.base import EmailMessage
from app.adapters.sms.base import SMSMessage
from app.adapters.whatsapp.base import WhatsAppMessage
from app.core.config import settings
from app.core.database import get_db_context
from app.modules.messaging.models import Conversation, Message

logger = logging.getLogger(__name__)


async def send_sms_task(ctx: dict, *, to: str, body: str, tenant_id: str, message_id: str) -> None:
    """Send an SMS via the configured provider and update the message status."""
    async with get_db_context() as db:
        msg_uuid = uuid.UUID(message_id)
        try:
            result = await get_sms_adapter().send(SMSMessage(to=to, body=body))
            if result.status != "sent":
                raise RuntimeError(result.error or "SMS provider returned non-sent status")

            await db.execute(
                update(Message)
                .where(Message.id == msg_uuid)
                .values(status="sent", provider_message_id=result.provider_id)
            )
            await db.commit()
            logger.info("SMS sent to=%s provider_id=%s", to, result.provider_id)

        except Exception as exc:
            await db.execute(
                update(Message).where(Message.id == msg_uuid).values(status="failed")
            )
            await db.commit()
            logger.error("send_sms_task failed to=%s error=%s", to, exc, exc_info=True)
            raise


async def send_email_task(
    ctx: dict,
    *,
    to: str,
    to_name: str | None = None,
    subject: str,
    html: str,
    tenant_id: str,
    message_id: str,
) -> None:
    """Send an email via the configured provider and update the message status."""
    async with get_db_context() as db:
        msg_uuid = uuid.UUID(message_id)
        try:
            provider_id = await get_email_adapter().send(EmailMessage(
                to=to, to_name=to_name, subject=subject, html_body=html,
            ))
            await db.execute(
                update(Message)
                .where(Message.id == msg_uuid)
                .values(status="sent", provider_message_id=provider_id)
            )
            await db.commit()
            logger.info("Email sent to=%s provider_id=%s", to, provider_id)

        except Exception as exc:
            await db.execute(
                update(Message).where(Message.id == msg_uuid).values(status="failed")
            )
            await db.commit()
            logger.error("send_email_task failed to=%s error=%s", to, exc, exc_info=True)
            raise


async def send_whatsapp_task(
    ctx: dict,
    *,
    to: str,
    body: str,
    tenant_id: str,
    message_id: str,
    template: str | None = None,
    media_url: str | None = None,
) -> None:
    """Send a WhatsApp message via the configured provider and update status."""
    async with get_db_context() as db:
        msg_uuid = uuid.UUID(message_id)
        try:
            result = await get_whatsapp_adapter().send(
                WhatsAppMessage(to=to, body=body, template=template, media_url=media_url)
            )
            if result.status not in ("sent", "queued"):
                raise RuntimeError(result.error or "WhatsApp provider returned non-sent status")

            await db.execute(
                update(Message)
                .where(Message.id == msg_uuid)
                .values(status=result.status, provider_message_id=result.provider_id)
            )
            await db.commit()
            logger.info("WhatsApp sent to=%s provider_id=%s", to, result.provider_id)

        except Exception as exc:
            await db.execute(
                update(Message).where(Message.id == msg_uuid).values(status="failed")
            )
            await db.commit()
            logger.error("send_whatsapp_task failed to=%s error=%s", to, exc, exc_info=True)
            raise


async def process_inbound_whatsapp(
    ctx: dict,
    *,
    from_number: str,
    body: str,
    tenant_id: str,
    provider_id: str,
) -> None:
    """Handle an inbound WhatsApp message from the Twilio webhook."""
    async with get_db_context() as db:
        try:
            tenant_uuid = uuid.UUID(tenant_id)

            result = await db.execute(
                select(Conversation).where(
                    Conversation.tenant_id == tenant_uuid,
                    Conversation.channel == "whatsapp",
                    Conversation.customer_phone == from_number,
                )
            )
            conv = result.scalar_one_or_none()

            if not conv:
                conv = Conversation(
                    id=uuid.uuid4(),
                    tenant_id=tenant_uuid,
                    channel="whatsapp",
                    customer_phone=from_number,
                )
                db.add(conv)
                await db.flush()

            msg = Message(
                id=uuid.uuid4(),
                tenant_id=tenant_uuid,
                conversation_id=conv.id,
                direction="inbound",
                channel="whatsapp",
                from_address=from_number,
                body=body,
                status="received",
                provider_message_id=provider_id,
            )
            conv.last_message_at = datetime.now(timezone.utc)
            db.add(msg)
            db.add(conv)
            await db.commit()
            await db.refresh(msg)
            logger.info("Inbound WhatsApp stored from=%s tenant=%s", from_number, tenant_id)

            # Best-effort AI auto-reply draft (reuses the email/SMS pipeline).
            try:
                from app.modules.auto_replies.service import draft_reply_for_inbound

                await draft_reply_for_inbound(db, tenant_uuid, inbound_message=msg)
            except Exception as exc:
                logger.warning("auto-reply draft (whatsapp) failed: %s", exc)

        except Exception as exc:
            logger.error("process_inbound_whatsapp failed from=%s error=%s", from_number, exc, exc_info=True)
            await db.rollback()
            raise


async def process_inbound_sms(
    ctx: dict,
    *,
    from_number: str,
    body: str,
    tenant_id: str,
    twilio_sid: str,
) -> None:
    """Handle an inbound SMS from Twilio webhook."""
    async with get_db_context() as db:
        try:
            tenant_uuid = uuid.UUID(tenant_id)

            result = await db.execute(
                select(Conversation).where(
                    Conversation.tenant_id == tenant_uuid,
                    Conversation.channel == "sms",
                    Conversation.customer_phone == from_number,
                )
            )
            conv = result.scalar_one_or_none()

            if not conv:
                conv = Conversation(
                    id=uuid.uuid4(),
                    tenant_id=tenant_uuid,
                    channel="sms",
                    customer_phone=from_number,
                )
                db.add(conv)
                await db.flush()

            msg = Message(
                id=uuid.uuid4(),
                tenant_id=tenant_uuid,
                conversation_id=conv.id,
                direction="inbound",
                channel="sms",
                from_address=from_number,
                body=body,
                status="received",
                provider_message_id=twilio_sid,
            )
            conv.last_message_at = datetime.now(timezone.utc)
            db.add(msg)
            db.add(conv)
            await db.commit()
            await db.refresh(msg)
            logger.info("Inbound SMS stored from=%s tenant=%s", from_number, tenant_id)

            # Best-effort: mark outreach enrolments for this customer as replied.
            try:
                if conv.customer_id is not None:
                    from app.modules.outreach.service import mark_replied as outreach_mark_replied

                    await outreach_mark_replied(db, tenant_uuid, conv.customer_id)
            except Exception as exc:
                logger.warning("outreach mark_replied failed: %s", exc)

            # Best-effort AI auto-reply draft.
            try:
                from app.modules.auto_replies.service import draft_reply_for_inbound

                await draft_reply_for_inbound(db, tenant_uuid, inbound_message=msg)
            except Exception as exc:
                logger.warning("auto-reply draft failed: %s", exc)

        except Exception as exc:
            logger.error("process_inbound_sms failed from=%s error=%s", from_number, exc, exc_info=True)
            await db.rollback()
            raise


async def handle_missed_call(ctx: dict, *, from_number: str, tenant_id: str, to_number: str) -> None:
    """Auto-respond to a missed call with an SMS and create a lead."""
    async with get_db_context() as db:
        try:
            tenant_uuid = uuid.UUID(tenant_id)
            from app.modules.tenants.models import Tenant
            from app.modules.leads.models import Lead

            tenant = (await db.execute(select(Tenant).where(Tenant.id == tenant_uuid))).scalar_one_or_none()
            if not tenant:
                logger.warning("handle_missed_call: tenant %s not found", tenant_id)
                return

            # Auto-create a lead so the missed call appears in the pipeline.
            db.add(Lead(
                id=uuid.uuid4(),
                tenant_id=tenant_uuid,
                first_name="Missed",
                last_name="Call",
                phone=from_number,
                source="missed_call",
                status="new",
            ))

            body = (
                f"Hi! Sorry we missed your call to {tenant.name}. "
                f"Get a free quote in 60 seconds: {settings.FRONTEND_URL}/{tenant.slug}"
            )
            result = await get_sms_adapter().send(SMSMessage(to=from_number, body=body))
            await db.commit()
            logger.info(
                "Missed-call SMS sent to=%s tenant=%s provider_id=%s status=%s",
                from_number, tenant_id, result.provider_id, result.status,
            )

        except Exception as exc:
            logger.error("handle_missed_call failed from=%s error=%s", from_number, exc, exc_info=True)
            raise
