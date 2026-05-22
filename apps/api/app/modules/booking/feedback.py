"""Post-service feedback requests and public submission."""
from __future__ import annotations

import secrets
import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import BadRequestException, NotFoundException
from app.modules.booking.models import Booking
from app.modules.booking.service import get_booking
from app.modules.tenants.models import Tenant


def generate_feedback_token() -> str:
    return secrets.token_urlsafe(32)


def feedback_url_for_token(token: str) -> str:
    base = (settings.FRONTEND_URL or "http://localhost:3000").rstrip("/")
    return f"{base}/book/feedback/{token}"


def refer_url_for_slug(slug: str) -> str:
    base = (settings.FRONTEND_URL or "http://localhost:3000").rstrip("/")
    return f"{base}/book/{slug}/refer"


async def request_service_feedback(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    booking_id: uuid.UUID,
    *,
    channels: list[str],
    actor_user_id: uuid.UUID | None = None,
) -> dict:
    """After service is rendered (completed), send rate/feedback link to client."""
    booking = await get_booking(db, tenant_id, booking_id)
    if booking.status != "completed":
        raise BadRequestException("Feedback can only be requested after the booking is marked completed.")
    if booking.feedback_submitted_at:
        raise BadRequestException("Feedback has already been submitted for this booking.")

    if not booking.feedback_token:
        booking.feedback_token = generate_feedback_token()
    booking.feedback_requested_at = datetime.now(timezone.utc)
    db.add(booking)
    await db.commit()
    await db.refresh(booking)

    url = feedback_url_for_token(booking.feedback_token)
    tenant = (
        await db.execute(select(Tenant).where(Tenant.id == tenant_id))
    ).scalar_one_or_none()
    business_name = tenant.name if tenant else "Your provider"

    sent: list[str] = []
    if "email" in channels and booking.customer_email:
        from app.adapters import get_email_adapter
        from app.templates.renderer import render_review_request

        adapter = get_email_adapter()
        html = render_review_request(
            customer_name=booking.customer_name,
            business_name=business_name,
            review_url=url,
            service_description=booking.service_description,
        )
        await adapter.send(
            to=booking.customer_email,
            subject=f"Rate your experience with {business_name}",
            html=html,
        )
        sent.append("email")

    if "in_app" in channels:
        from app.modules.notifications.service import create_notification

        await create_notification(
            db,
            tenant_id=tenant_id,
            user_id=None,
            kind="booking.feedback_requested",
            title=f"Feedback request sent — {booking.customer_name}",
            body=f"Client notified to rate their visit ({', '.join(sent) or 'link ready'}).",
            link=f"/dashboard/bookings/{booking.id}",
            extra={"booking_id": str(booking.id), "feedback_url": url},
        )
        sent.append("in_app")

    from app.core.audit import log_action

    await log_action(
        db,
        action="booking.feedback_requested",
        resource="booking",
        resource_id=booking.id,
        tenant_id=tenant_id,
        user_id=actor_user_id,
        metadata={"channels": channels, "feedback_url": url},
    )

    return {
        "booking_id": str(booking.id),
        "feedback_url": url,
        "channels_sent": sent,
    }


async def get_feedback_form(db: AsyncSession, token: str) -> dict:
    booking = (
        await db.execute(select(Booking).where(Booking.feedback_token == token))
    ).scalar_one_or_none()
    if not booking:
        raise NotFoundException("Feedback link")
    tenant = (
        await db.execute(select(Tenant).where(Tenant.id == booking.tenant_id))
    ).scalar_one_or_none()
    return {
        "tenant_name": tenant.name if tenant else "Business",
        "customer_name": booking.customer_name,
        "booking_date": booking.booking_date.isoformat(),
        "already_submitted": booking.feedback_submitted_at is not None,
        "service_rating": booking.service_rating,
        "feedback_text": booking.feedback_text,
    }


async def submit_feedback(
    db: AsyncSession,
    token: str,
    *,
    rating: int,
    feedback_text: str | None,
) -> dict:
    if rating < 1 or rating > 5:
        raise BadRequestException("Rating must be between 1 and 5.")
    booking = (
        await db.execute(select(Booking).where(Booking.feedback_token == token))
    ).scalar_one_or_none()
    if not booking:
        raise NotFoundException("Feedback link")
    if booking.feedback_submitted_at:
        raise BadRequestException("Feedback already submitted.")

    booking.service_rating = rating
    booking.feedback_text = (feedback_text or "").strip() or None
    booking.feedback_submitted_at = datetime.now(timezone.utc)
    db.add(booking)
    await db.commit()

    from app.modules.notifications.service import create_notification

    await create_notification(
        db,
        tenant_id=booking.tenant_id,
        user_id=None,
        kind="booking.feedback_received",
        title=f"New rating ({rating}/5) — {booking.customer_name}",
        body=(booking.feedback_text or "No written feedback")[:200],
        link=f"/dashboard/bookings/{booking.id}",
        extra={"booking_id": str(booking.id), "rating": rating},
    )

    return {"message": "Thank you for your feedback.", "rating": rating}


# Re-export for tests
__all__ = ["generate_feedback_token", "feedback_url_for_token", "request_service_feedback"]
