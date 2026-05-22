"""Booking notification queue and automation scheduling."""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.modules.booking.enterprise.settings import get_or_create_settings
from app.modules.booking.enterprise_models import BookingNotificationQueue
from app.modules.booking.models import Booking
from app.modules.tenants.models import Tenant

logger = logging.getLogger(__name__)


async def schedule_booking_notifications(db: AsyncSession, booking: Booking) -> None:
    """Queue confirmation + reminders per tenant automation_config."""
    tenant = (
        await db.execute(select(Tenant).where(Tenant.id == booking.tenant_id))
    ).scalar_one_or_none()
    if not tenant:
        return

    cfg = (await get_or_create_settings(db, booking.tenant_id)).automation_config or {}
    reminders = cfg.get("reminders") or {
        "email": [48, 24],
        "sms": [24],
    }

    booking_dt = datetime.combine(
        booking.booking_date,
        booking.start_time,
        tzinfo=timezone.utc,
    )

    if booking.customer_email:
        await _queue(
            db,
            booking,
            channel="email",
            notification_type="booking.confirmation",
            recipient=booking.customer_email,
            scheduled_for=datetime.now(timezone.utc),
            payload={"template": "confirmation"},
        )
        for hours_before in reminders.get("email") or []:
            scheduled = booking_dt - timedelta(hours=int(hours_before))
            if scheduled > datetime.now(timezone.utc):
                await _queue(
                    db,
                    booking,
                    channel="email",
                    notification_type="booking.reminder",
                    recipient=booking.customer_email,
                    scheduled_for=scheduled,
                    payload={"hours_before": hours_before},
                )

    if booking.customer_phone:
        for hours_before in reminders.get("sms") or []:
            scheduled = booking_dt - timedelta(hours=int(hours_before))
            if scheduled > datetime.now(timezone.utc):
                await _queue(
                    db,
                    booking,
                    channel="sms",
                    notification_type="booking.reminder",
                    recipient=booking.customer_phone,
                    scheduled_for=scheduled,
                    payload={"hours_before": hours_before},
                )

    if cfg.get("whatsapp_reminders") and booking.customer_phone:
        await _queue(
            db,
            booking,
            channel="whatsapp",
            notification_type="booking.reminder",
            recipient=booking.customer_phone,
            scheduled_for=booking_dt - timedelta(hours=2),
            payload={},
        )

    await db.commit()


async def schedule_abandoned_recovery(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    session_token: str,
    customer_email: str | None,
    delay_hours: int = 2,
) -> None:
    if not customer_email:
        return
    cfg = (await get_or_create_settings(db, tenant_id)).automation_config or {}
    if not cfg.get("abandoned_recovery", True):
        return
    await _queue(
        db,
        None,
        tenant_id=tenant_id,
        channel="email",
        notification_type="booking.abandoned",
        recipient=customer_email,
        scheduled_for=datetime.now(timezone.utc) + timedelta(hours=delay_hours),
        payload={"session_token": session_token},
    )
    await db.commit()


async def schedule_no_show_recovery(db: AsyncSession, booking: Booking) -> None:
    cfg = (await get_or_create_settings(db, booking.tenant_id)).automation_config or {}
    if not cfg.get("no_show_recovery", True) or not booking.customer_email:
        return
    await _queue(
        db,
        booking,
        channel="email",
        notification_type="booking.no_show_recovery",
        recipient=booking.customer_email,
        scheduled_for=datetime.now(timezone.utc) + timedelta(hours=4),
        payload={},
    )
    await db.commit()


async def _queue(
    db: AsyncSession,
    booking: Booking | None,
    *,
    channel: str,
    notification_type: str,
    recipient: str,
    scheduled_for: datetime,
    payload: dict,
    tenant_id: uuid.UUID | None = None,
) -> None:
    row = BookingNotificationQueue(
        id=uuid.uuid4(),
        tenant_id=tenant_id or (booking.tenant_id if booking else None),
        booking_id=booking.id if booking else None,
        channel=channel,
        notification_type=notification_type,
        recipient=recipient,
        payload=payload,
        scheduled_for=scheduled_for,
        status="pending",
    )
    if row.tenant_id is None:
        return
    db.add(row)


async def send_immediate_client_reminder(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    booking_id: uuid.UUID,
    *,
    channel: str,
) -> dict:
    """Send a one-off SMS or email reminder to the customer for an upcoming booking."""
    from app.core.exceptions import BadRequestException, NotFoundException

    booking = (
        await db.execute(
            select(Booking).where(Booking.id == booking_id, Booking.tenant_id == tenant_id)
        )
    ).scalar_one_or_none()
    if not booking:
        raise NotFoundException("Booking")
    if channel == "email":
        if not booking.customer_email:
            raise BadRequestException("Booking has no customer email")
        recipient = booking.customer_email
    elif channel == "sms":
        if not booking.customer_phone:
            raise BadRequestException("Booking has no customer phone")
        recipient = booking.customer_phone
    else:
        raise BadRequestException("channel must be email or sms")

    row = BookingNotificationQueue(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        booking_id=booking.id,
        channel=channel,
        notification_type="booking.reminder",
        recipient=recipient,
        payload={"manual": True},
        scheduled_for=datetime.now(timezone.utc),
        status="pending",
    )
    db.add(row)
    await db.flush()
    await _deliver_notification(db, row)
    row.status = "sent"
    row.sent_at = datetime.now(timezone.utc)
    await db.commit()
    return {"sent": True, "channel": channel, "booking_id": str(booking_id)}


async def process_due_notifications(db: AsyncSession, *, limit: int = 50) -> dict:
    """Worker: send due queued notifications."""
    now = datetime.now(timezone.utc)
    rows = (
        await db.execute(
            select(BookingNotificationQueue)
            .where(
                BookingNotificationQueue.status == "pending",
                BookingNotificationQueue.scheduled_for <= now,
            )
            .order_by(BookingNotificationQueue.scheduled_for)
            .limit(limit)
        )
    ).scalars().all()

    sent = failed = 0
    for row in rows:
        try:
            await _deliver_notification(db, row)
            row.status = "sent"
            row.sent_at = now
            sent += 1
        except Exception as exc:  # noqa: BLE001
            row.status = "failed"
            row.error_message = str(exc)[:500]
            failed += 1
            logger.exception("booking notification failed id=%s", row.id)
        db.add(row)

    await db.commit()
    return {"processed": len(rows), "sent": sent, "failed": failed}


async def _deliver_notification(db: AsyncSession, row: BookingNotificationQueue) -> None:
    from app.workers.queue import enqueue

    booking = None
    if row.booking_id:
        booking = (
            await db.execute(select(Booking).where(Booking.id == row.booking_id))
        ).scalar_one_or_none()

    tenant = (
        await db.execute(select(Tenant).where(Tenant.id == row.tenant_id))
    ).scalar_one_or_none()
    business_name = tenant.name if tenant else "CustomerFlow"

    if row.channel == "email":
        from app.templates.renderer import render_booking_confirmation, render_booking_reminder

        if booking and row.notification_type == "booking.confirmation":
            html = render_booking_confirmation(
                customer_name=booking.customer_name,
                business_name=business_name,
                booking_date=str(booking.booking_date),
                start_time=str(booking.start_time),
                service_description=booking.service_description,
                deposit_required_pence=booking.deposit_required_pence,
                deposit_paid=booking.deposit_paid_pence >= booking.deposit_required_pence,
            )
            subject = f"Booking confirmed — {business_name}"
        elif booking and row.notification_type == "booking.reminder":
            manage_url = _manage_url(booking.manage_token)
            html = render_booking_reminder(
                customer_name=booking.customer_name,
                business_name=business_name,
                booking_date=str(booking.booking_date),
                start_time=str(booking.start_time),
                location=None,
                reschedule_url=manage_url,
            )
            subject = f"Reminder: appointment with {business_name}"
        else:
            html = f"<p>We noticed you did not finish your booking. Continue here: {_frontend()}/book</p>"
            subject = f"Complete your booking — {business_name}"

        await enqueue(
            "send_email_task",
            to=row.recipient,
            subject=subject,
            html=html,
            tenant_id=str(row.tenant_id),
        )
    elif row.channel in ("sms", "whatsapp"):
        body = "Appointment reminder"
        if booking:
            body = (
                f"Reminder: {business_name} on {booking.booking_date} at {booking.start_time}. "
                f"Manage: {_manage_url(booking.manage_token)}"
            )
        await enqueue(
            "send_sms_task",
            to=row.recipient,
            body=body,
            tenant_id=str(row.tenant_id),
        )


def _frontend() -> str:
    return (settings.FRONTEND_URL or "http://localhost:3000").rstrip("/")


def _manage_url(token: str | None) -> str:
    if not token:
        return _frontend()
    return f"{_frontend()}/book/manage/{token}"


async def ai_booking_recommendations(
    db: AsyncSession, tenant_id: uuid.UUID, booking_id: uuid.UUID
) -> dict:
    """Suggest upsell services using AI module when available."""
    booking = (
        await db.execute(
            select(Booking).where(Booking.id == booking_id, Booking.tenant_id == tenant_id)
        )
    ).scalar_one_or_none()
    if not booking:
        return {"recommendations": []}

    try:
        from app.adapters.ai import get_ai_adapter

        adapter = get_ai_adapter()
        prompt = (
            f"Customer booked: {booking.service_description or 'general service'}. "
            "Suggest up to 3 complementary upsell services for a UK trades business. "
            "Return JSON list of objects with name and reason."
        )
        if hasattr(adapter, "complete"):
            raw = await adapter.complete(prompt=prompt, max_tokens=400)  # type: ignore[attr-defined]
            return {"recommendations": raw if isinstance(raw, list) else [{"name": str(raw), "reason": ""}]}
    except Exception as exc:  # noqa: BLE001
        logger.debug("AI booking recommend unavailable: %s", exc)

    return {
        "recommendations": [
            {"name": "Annual service plan", "reason": "Recurring revenue and customer retention"},
            {"name": "Priority call-out cover", "reason": "Higher margin add-on"},
        ]
    }
