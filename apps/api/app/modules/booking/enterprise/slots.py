"""Availability slot generation and listing."""
from __future__ import annotations

import uuid
from datetime import date, datetime, time, timedelta, timezone

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequestException
from app.modules.booking.enterprise.settings import get_or_create_settings
from app.modules.booking.enterprise_schemas import SlotGenerateRequest
from app.modules.booking.enterprise_models import StaffBlackout
from app.modules.booking.models import AvailabilitySlot, Staff


async def list_slots(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    *,
    from_date: date | None = None,
    staff_id: uuid.UUID | None = None,
    location_id: uuid.UUID | None = None,
    only_available: bool = False,
) -> list[AvailabilitySlot]:
    today = from_date or datetime.now(timezone.utc).date()
    q = select(AvailabilitySlot).where(
        AvailabilitySlot.tenant_id == tenant_id,
        AvailabilitySlot.slot_date >= today,
    )
    if staff_id:
        q = q.where(AvailabilitySlot.staff_id == staff_id)
    if location_id:
        q = q.where(AvailabilitySlot.location_id == location_id)
    if only_available:
        q = q.where(AvailabilitySlot.is_booked == False)  # noqa: E712
    return list(
        (await db.execute(q.order_by(AvailabilitySlot.slot_date, AvailabilitySlot.start_time).limit(500)))
        .scalars()
        .all()
    )


async def generate_slots(db: AsyncSession, tenant_id: uuid.UUID, data: SlotGenerateRequest) -> int:
    if data.to_date < data.from_date:
        raise BadRequestException("to_date must be on or after from_date")
    if (data.to_date - data.from_date).days > 90:
        raise BadRequestException("Cannot generate more than 90 days at once")

    settings = await get_or_create_settings(db, tenant_id)
    if not settings.overbooking_allowed:
        existing = await list_slots(db, tenant_id, from_date=data.from_date)
        if len(existing) > 2000:
            raise BadRequestException("Too many existing slots; clear or book before bulk generate")

    blackouts = (
        await db.execute(select(StaffBlackout).where(StaffBlackout.tenant_id == tenant_id))
    ).scalars().all()

    created = 0
    current = data.from_date
    while current <= data.to_date:
        if data.exclude_weekends and current.weekday() >= 5:
            current += timedelta(days=1)
            continue
        if await _is_blackout_day(blackouts, data.staff_id, current):
            current += timedelta(days=1)
            continue

        slot_start = datetime.combine(current, data.daily_start)
        day_end = datetime.combine(current, data.daily_end)
        duration = timedelta(minutes=data.slot_duration_minutes)

        while slot_start + duration <= day_end:
            end_dt = slot_start + duration
            slot = AvailabilitySlot(
                id=uuid.uuid4(),
                tenant_id=tenant_id,
                staff_id=data.staff_id,
                location_id=data.location_id,
                resource_id=data.resource_id,
                service_id=data.service_id,
                slot_date=current,
                start_time=slot_start.time(),
                end_time=end_dt.time(),
                duration_minutes=data.slot_duration_minutes,
                is_booked=False,
            )
            dup = (
                await db.execute(
                    select(AvailabilitySlot.id).where(
                        AvailabilitySlot.tenant_id == tenant_id,
                        AvailabilitySlot.staff_id == data.staff_id,
                        AvailabilitySlot.slot_date == current,
                        AvailabilitySlot.start_time == slot.start_time,
                    )
                )
            ).scalar_one_or_none()
            if not dup:
                db.add(slot)
                created += 1
            slot_start = end_dt
        current += timedelta(days=1)

    await db.commit()
    return created


async def _is_blackout_day(
    blackouts: list[StaffBlackout],
    staff_id: uuid.UUID | None,
    day: date,
) -> bool:
    day_start = datetime.combine(day, time.min, tzinfo=timezone.utc)
    day_end = datetime.combine(day, time.max, tzinfo=timezone.utc)
    for b in blackouts:
        if b.staff_id and staff_id and b.staff_id != staff_id:
            continue
        if b.start_at <= day_end and b.end_at >= day_start:
            return True
    return False


async def count_staff_bookings_on_slot(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    staff_id: uuid.UUID | None,
    slot_date: date,
    start_time: time,
) -> int:
    from app.modules.booking.models import Booking

    q = select(Booking).where(
        Booking.tenant_id == tenant_id,
        Booking.booking_date == slot_date,
        Booking.start_time == start_time,
        Booking.status.in_(("pending", "confirmed")),
    )
    if staff_id:
        q = q.where(Booking.staff_id == staff_id)
    return len((await db.execute(q)).scalars().all())
