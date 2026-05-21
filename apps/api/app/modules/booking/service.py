import secrets
import uuid
from datetime import date, datetime, time, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import log_action
from app.core.exceptions import BadRequestException, NotFoundException
from app.modules.booking.models import Booking, AvailabilitySlot
from app.modules.booking.schemas import BookingCreate, BookingUpdate, PublicBookingCreate
from app.modules.tenants.models import Tenant


async def get_available_slots(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    from_date: date | None = None,
    *,
    staff_id: uuid.UUID | None = None,
    location_id: uuid.UUID | None = None,
    service_id: uuid.UUID | None = None,
) -> dict:
    from app.modules.booking.enterprise.settings import get_or_create_settings
    from app.modules.booking.enterprise.slots import list_slots

    settings = await get_or_create_settings(db, tenant_id)
    slots = await list_slots(
        db,
        tenant_id,
        from_date=from_date,
        staff_id=staff_id,
        only_available=True,
    )
    if location_id:
        slots = [s for s in slots if s.location_id == location_id or s.location_id is None]
    if service_id:
        slots = [s for s in slots if s.service_id == service_id or s.service_id is None]

    return {
        "timezone": settings.timezone,
        "slots": [
            {
                "id": str(s.id),
                "date": s.slot_date.isoformat(),
                "start": s.start_time.isoformat(),
                "end": s.end_time.isoformat(),
                "staff_id": str(s.staff_id) if s.staff_id else None,
                "duration_minutes": s.duration_minutes,
            }
            for s in slots[:60]
        ],
    }


async def create_booking(db: AsyncSession, tenant_id: uuid.UUID, data: BookingCreate) -> Booking:
    from app.modules.booking.enterprise.settings import get_or_create_settings
    from app.modules.booking.enterprise.slots import count_staff_bookings_on_slot
    from app.modules.booking.enterprise.marketing import apply_promo, generate_manage_token
    from app.modules.booking.enterprise.automation import schedule_booking_notifications

    settings = await get_or_create_settings(db, tenant_id)

    if data.slot_id:
        slot_result = await db.execute(
            select(AvailabilitySlot).where(
                AvailabilitySlot.id == data.slot_id, AvailabilitySlot.tenant_id == tenant_id
            )
        )
        slot = slot_result.scalar_one_or_none()
        if not slot:
            raise NotFoundException("Slot")
        if slot.is_booked:
            raise BadRequestException("This slot is already booked")
        if not settings.overbooking_allowed and data.staff_id:
            count = await count_staff_bookings_on_slot(
                db, tenant_id, data.staff_id, slot.slot_date, slot.start_time
            )
            if count > 0:
                raise BadRequestException("Staff member is already booked for this time")
        slot.is_booked = True
        db.add(slot)

    dump = data.model_dump(exclude={"slot_id", "promo_code"})
    duration = dump.pop("duration_minutes", None) or settings.default_duration_minutes
    end_time = _calc_end_time(dump.get("start_time"), duration)

    deposit_required = dump.get("deposit_required_pence") or 0
    if settings.deposit_enabled and deposit_required == 0:
        deposit_required = settings.default_deposit_pence

    amount_for_promo = deposit_required + (dump.get("prepaid_pence") or 0)
    promo_code = getattr(data, "promo_code", None)
    if promo_code:
        amount_for_promo, applied = await apply_promo(db, tenant_id, promo_code, amount_for_promo)
        dump["promo_code"] = applied

    service_fee = int(amount_for_promo * float(settings.service_fee_percent or 0) / 100)

    booking = Booking(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        **dump,
        slot_id=data.slot_id,
        duration_minutes=duration,
        end_time=end_time,
        timezone=dump.get("timezone") or settings.timezone,
        deposit_required_pence=deposit_required,
        service_fee_pence=service_fee,
        no_show_fee_pence=settings.no_show_fee_pence,
        manage_token=generate_manage_token(),
        status="pending" if deposit_required > 0 else "confirmed",
    )
    db.add(booking)
    await db.commit()
    await db.refresh(booking)

    from app.modules.referrals.service import on_booking_created

    await on_booking_created(db, tenant_id=tenant_id, booking=booking)

    await schedule_booking_notifications(db, booking)

    from app.workers.queue import enqueue

    await enqueue(
        "trigger_automation_for_event",
        tenant_id=str(tenant_id),
        event="booking_confirmed",
        entity_id=str(booking.id),
        entity_type="booking",
    )
    return booking


async def create_public_booking(db: AsyncSession, tenant: Tenant, data: PublicBookingCreate) -> dict:
    book_data = BookingCreate(**data.model_dump())
    booking = await create_booking(db, tenant.id, book_data)
    manage_url = None
    if booking.manage_token:
        from app.core.config import settings

        base = (settings.FRONTEND_URL or "http://localhost:3000").rstrip("/")
        manage_url = f"{base}/book/manage/{booking.manage_token}"

    result = {
        "booking_id": str(booking.id),
        "message": "Booking confirmed! We will be in touch shortly.",
        "status": booking.status,
        "manage_url": manage_url,
    }
    if booking.deposit_required_pence > booking.deposit_paid_pence:
        from app.modules.booking.enterprise.payments import create_booking_payment_intent
        from app.modules.booking.enterprise_schemas import BookingPaymentIntentRequest

        pi = await create_booking_payment_intent(
            db,
            tenant.id,
            BookingPaymentIntentRequest(
                booking_id=booking.id,
                amount_pence=booking.deposit_required_pence - booking.deposit_paid_pence,
                purpose="deposit",
                customer_email=booking.customer_email,
            ),
        )
        result["payment"] = pi
    return result


async def list_bookings(
    db: AsyncSession, tenant_id: uuid.UUID, page: int = 1, page_size: int = 25, status: str | None = None
) -> tuple[list[Booking], int]:
    from sqlalchemy import func

    q = select(Booking).where(Booking.tenant_id == tenant_id)
    if status:
        q = q.where(Booking.status == status)
    total = (await db.execute(select(func.count()).select_from(q.subquery()))).scalar_one()
    items = (
        await db.execute(
            q.order_by(Booking.booking_date.desc(), Booking.start_time).offset((page - 1) * page_size).limit(page_size)
        )
    ).scalars().all()
    return list(items), total


async def get_booking(db: AsyncSession, tenant_id: uuid.UUID, booking_id: uuid.UUID) -> Booking:
    result = await db.execute(select(Booking).where(Booking.id == booking_id, Booking.tenant_id == tenant_id))
    b = result.scalar_one_or_none()
    if not b:
        raise NotFoundException("Booking")
    return b


async def update_booking(
    db: AsyncSession, tenant_id: uuid.UUID, booking_id: uuid.UUID, data: BookingUpdate
) -> Booking:
    from app.modules.booking.enterprise.automation import schedule_no_show_recovery

    b = await get_booking(db, tenant_id, booking_id)
    old_status = b.status
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(b, field, value)

    if b.status == "cancelled" and old_status != "cancelled":
        await _release_slot(db, tenant_id, b.slot_id)

    if b.status == "no_show" and old_status != "no_show":
        await schedule_no_show_recovery(db, b)

    db.add(b)
    await db.commit()
    await db.refresh(b)

    if b.status == "completed" and old_status != "completed":
        from app.modules.referrals.service import on_booking_completed

        await on_booking_completed(db, tenant_id=tenant_id, booking=b)
    return b


async def public_manage_booking(
    db: AsyncSession,
    manage_token: str,
    *,
    action: str,
    booking_date: date | None = None,
    start_time: time | None = None,
    slot_id: uuid.UUID | None = None,
) -> Booking:
    from app.modules.booking.enterprise.settings import get_or_create_settings

    result = await db.execute(select(Booking).where(Booking.manage_token == manage_token))
    booking = result.scalar_one_or_none()
    if not booking:
        raise NotFoundException("Booking")

    settings = await get_or_create_settings(db, booking.tenant_id)

    if action == "cancel":
        if not settings.allow_self_cancel:
            raise BadRequestException("Self-service cancellation is not enabled")
        booking.status = "cancelled"
        await _release_slot(db, booking.tenant_id, booking.slot_id)
    elif action == "reschedule":
        if not settings.allow_self_reschedule:
            raise BadRequestException("Self-service rescheduling is not enabled")
        if not booking_date or not start_time:
            raise BadRequestException("booking_date and start_time required for reschedule")
        booking.booking_date = booking_date
        booking.start_time = start_time
        if slot_id:
            await _reserve_slot(db, booking.tenant_id, slot_id, booking)
            booking.slot_id = slot_id
        booking.end_time = _calc_end_time(start_time, booking.duration_minutes)
    else:
        raise BadRequestException("Invalid action")

    db.add(booking)
    await db.commit()
    await db.refresh(booking)
    return booking


async def get_booking_timeline(db: AsyncSession, tenant_id: uuid.UUID, booking_id: uuid.UUID) -> dict:
    from app.modules.audit.models import AuditLog

    booking = await get_booking(db, tenant_id, booking_id)
    logs = (
        await db.execute(
            select(AuditLog)
            .where(
                AuditLog.tenant_id == tenant_id,
                AuditLog.resource_id == str(booking_id),
            )
            .order_by(AuditLog.created_at.desc())
            .limit(50)
        )
    ).scalars().all()

    events = [
        {
            "type": "booking.created",
            "at": booking.created_at.isoformat(),
            "detail": f"Booking created — {booking.status}",
        }
    ]
    if booking.deposit_paid_pence > 0:
        events.append({
            "type": "booking.deposit_paid",
            "at": booking.updated_at.isoformat(),
            "detail": f"Deposit £{booking.deposit_paid_pence / 100:.2f}",
        })
    for log in logs:
        events.append({
            "type": log.action,
            "at": log.created_at.isoformat() if log.created_at else None,
            "detail": log.extra_metadata,
        })

    return {
        "booking_id": booking_id,
        "customer_name": booking.customer_name,
        "lead_status": booking.lead_status,
        "events": events,
    }


async def _release_slot(db: AsyncSession, tenant_id: uuid.UUID, slot_id: uuid.UUID | None) -> None:
    if not slot_id:
        return
    slot = (
        await db.execute(
            select(AvailabilitySlot).where(
                AvailabilitySlot.id == slot_id, AvailabilitySlot.tenant_id == tenant_id
            )
        )
    ).scalar_one_or_none()
    if slot:
        slot.is_booked = False
        db.add(slot)
        await db.flush()


async def _reserve_slot(
    db: AsyncSession, tenant_id: uuid.UUID, slot_id: uuid.UUID, booking: Booking
) -> None:
    if booking.slot_id:
        await _release_slot(db, tenant_id, booking.slot_id)
    slot = (
        await db.execute(
            select(AvailabilitySlot).where(
                AvailabilitySlot.id == slot_id, AvailabilitySlot.tenant_id == tenant_id
            )
        )
    ).scalar_one_or_none()
    if not slot or slot.is_booked:
        raise BadRequestException("Slot unavailable")
    slot.is_booked = True
    db.add(slot)


def _calc_end_time(start: time | None, duration_minutes: int) -> time | None:
    if not start:
        return None
    dt = datetime.combine(date.today(), start) + timedelta(minutes=duration_minutes)
    return dt.time()
