import uuid
from datetime import date, datetime, timezone, timedelta
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.exceptions import NotFoundException, BadRequestException
from app.modules.booking.models import Booking, AvailabilitySlot
from app.modules.booking.schemas import BookingCreate, BookingUpdate, PublicBookingCreate
from app.modules.tenants.models import Tenant


async def get_available_slots(db: AsyncSession, tenant_id: uuid.UUID, from_date: date | None = None) -> dict:
    today = from_date or datetime.now(timezone.utc).date()
    result = await db.execute(
        select(AvailabilitySlot).where(
            AvailabilitySlot.tenant_id == tenant_id,
            AvailabilitySlot.slot_date >= today,
            AvailabilitySlot.is_booked == False,
        ).order_by(AvailabilitySlot.slot_date, AvailabilitySlot.start_time).limit(60)
    )
    slots = result.scalars().all()
    return {"slots": [{"id": str(s.id), "date": s.slot_date.isoformat(), "start": s.start_time.isoformat(), "end": s.end_time.isoformat()} for s in slots]}


async def create_booking(db: AsyncSession, tenant_id: uuid.UUID, data: BookingCreate) -> Booking:
    if data.slot_id:
        slot_result = await db.execute(select(AvailabilitySlot).where(AvailabilitySlot.id == data.slot_id, AvailabilitySlot.tenant_id == tenant_id))
        slot = slot_result.scalar_one_or_none()
        if not slot:
            raise NotFoundException("Slot")
        if slot.is_booked:
            raise BadRequestException("This slot is already booked")
        slot.is_booked = True
        db.add(slot)

    booking = Booking(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        **data.model_dump(exclude={"slot_id"}),
        slot_id=data.slot_id,
    )
    db.add(booking)
    await db.commit()
    await db.refresh(booking)

    from app.modules.referrals.service import on_booking_created

    await on_booking_created(db, tenant_id=tenant_id, booking=booking)

    # Trigger confirmation automation
    from app.workers.queue import enqueue
    await enqueue("trigger_automation_for_event", tenant_id=str(tenant_id), event="booking_confirmed", entity_id=str(booking.id), entity_type="booking")
    return booking


async def create_public_booking(db: AsyncSession, tenant: Tenant, data: PublicBookingCreate) -> dict:
    book_data = BookingCreate(**data.model_dump())
    booking = await create_booking(db, tenant.id, book_data)
    return {"booking_id": str(booking.id), "message": "Booking confirmed! We will be in touch shortly.", "status": booking.status}


async def list_bookings(db: AsyncSession, tenant_id: uuid.UUID, page: int = 1, page_size: int = 25) -> tuple[list[Booking], int]:
    from sqlalchemy import func
    q = select(Booking).where(Booking.tenant_id == tenant_id)
    total = (await db.execute(select(func.count()).select_from(q.subquery()))).scalar_one()
    items = (await db.execute(q.order_by(Booking.booking_date, Booking.start_time).offset((page-1)*page_size).limit(page_size))).scalars().all()
    return list(items), total


async def get_booking(db: AsyncSession, tenant_id: uuid.UUID, booking_id: uuid.UUID) -> Booking:
    result = await db.execute(select(Booking).where(Booking.id == booking_id, Booking.tenant_id == tenant_id))
    b = result.scalar_one_or_none()
    if not b:
        raise NotFoundException("Booking")
    return b


async def update_booking(db: AsyncSession, tenant_id: uuid.UUID, booking_id: uuid.UUID, data: BookingUpdate) -> Booking:
    b = await get_booking(db, tenant_id, booking_id)
    old_status = b.status
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(b, field, value)
    db.add(b)
    await db.commit()
    await db.refresh(b)
    if b.status == "completed" and old_status != "completed":
        from app.modules.referrals.service import on_booking_completed

        await on_booking_completed(db, tenant_id=tenant_id, booking=b)
    return b
