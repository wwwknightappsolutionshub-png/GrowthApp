"""Stripe deposits, prepaid, refunds for bookings."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters import get_payment_adapter
from app.core.exceptions import BadRequestException, NotFoundException
from app.modules.booking.enterprise_schemas import (
    BookingPaymentIntentRequest,
    BookingRefundRequest,
)
from app.modules.booking.models import Booking
from app.modules.booking.service import get_booking


async def create_booking_payment_intent(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    data: BookingPaymentIntentRequest,
) -> dict:
    booking: Booking | None = None
    if data.booking_id:
        booking = await get_booking(db, tenant_id, data.booking_id)

    adapter = get_payment_adapter()
    if not hasattr(adapter, "create_payment_intent"):
        raise BadRequestException("Payment provider does not support PaymentIntent")

    metadata = {
        "tenant_id": str(tenant_id),
        "purpose": data.purpose,
    }
    if booking:
        metadata["booking_id"] = str(booking.id)

    result = await adapter.create_payment_intent(  # type: ignore[attr-defined]
        amount_pence=data.amount_pence,
        currency="gbp",
        metadata=metadata,
        customer_email=data.customer_email or (booking.customer_email if booking else None),
        setup_future_usage="off_session" if data.purpose == "no_show_fee" else None,
    )

    if booking:
        booking.stripe_payment_intent_id = result["payment_intent_id"]
        if data.purpose == "no_show_fee":
            booking.stripe_setup_intent_id = result.get("setup_intent_id")
        db.add(booking)
        await db.commit()

    return result


async def apply_deposit_paid(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    booking_id: uuid.UUID,
    amount_pence: int,
    payment_intent_id: str,
) -> Booking:
    booking = await get_booking(db, tenant_id, booking_id)
    booking.deposit_paid_pence = amount_pence
    booking.stripe_payment_intent_id = payment_intent_id
    if booking.status == "pending":
        booking.status = "confirmed"
    db.add(booking)
    await db.commit()
    await db.refresh(booking)
    return booking


async def refund_booking(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    booking_id: uuid.UUID,
    data: BookingRefundRequest,
) -> Booking:
    booking = await get_booking(db, tenant_id, booking_id)
    amount = data.amount_pence or booking.deposit_paid_pence or booking.prepaid_pence
    if amount <= 0:
        raise BadRequestException("No refundable amount")

    adapter = get_payment_adapter()
    if booking.stripe_payment_intent_id and hasattr(adapter, "create_refund"):
        await adapter.create_refund(booking.stripe_payment_intent_id, amount)  # type: ignore[attr-defined]

    booking.refund_pence = amount
    booking.refunded_at = datetime.now(timezone.utc)
    db.add(booking)
    await db.commit()
    await db.refresh(booking)
    return booking
