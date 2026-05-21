"""Calendar sync — Google connection storage, iCal export."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from io import StringIO

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import NotFoundException
from app.modules.booking.enterprise_schemas import CalendarConnectionCreate, CalendarSyncResponse
from app.modules.booking.enterprise_models import BookingCalendarConnection
from app.modules.booking.models import Booking


async def create_connection(
    db: AsyncSession, tenant_id: uuid.UUID, data: CalendarConnectionCreate
) -> BookingCalendarConnection:
    row = BookingCalendarConnection(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        staff_id=data.staff_id,
        provider=data.provider,
        external_calendar_id=data.external_calendar_id,
        sync_enabled=data.sync_enabled,
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return row


async def list_connections(db: AsyncSession, tenant_id: uuid.UUID) -> list[BookingCalendarConnection]:
    return list(
        (
            await db.execute(
                select(BookingCalendarConnection).where(
                    BookingCalendarConnection.tenant_id == tenant_id
                )
            )
        ).scalars().all()
    )


async def sync_calendar(
    db: AsyncSession, tenant_id: uuid.UUID, connection_id: uuid.UUID
) -> CalendarSyncResponse:
    conn = (
        await db.execute(
            select(BookingCalendarConnection).where(
                BookingCalendarConnection.id == connection_id,
                BookingCalendarConnection.tenant_id == tenant_id,
            )
        )
    ).scalar_one_or_none()
    if not conn:
        raise NotFoundException("Calendar connection")

    bookings = (
        await db.execute(
            select(Booking).where(
                Booking.tenant_id == tenant_id,
                Booking.status.in_(("confirmed", "pending")),
            )
        )
    ).scalars().all()

    synced = len(bookings)
    conn.last_synced_at = datetime.now(timezone.utc)
    db.add(conn)
    await db.commit()

    ical_url = None
    if conn.provider == "ical":
        ical_url = f"{(settings.FRONTEND_URL or '').rstrip('/')}/api/v1/public/booking/{tenant_id}/ical.ics"

    return CalendarSyncResponse(synced=synced, provider=conn.provider, ical_feed_url=ical_url)


def build_ical_feed(bookings: list[Booking], business_name: str) -> str:
    """RFC5545 minimal feed for confirmed bookings."""
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//CustomerFlow AI//Booking//EN",
        f"X-WR-CALNAME:{business_name} Bookings",
    ]
    for b in bookings:
        if b.status not in ("confirmed", "pending"):
            continue
        start = f"{b.booking_date.strftime('%Y%m%d')}T{b.start_time.strftime('%H%M%S')}"
        end_time = b.end_time or b.start_time
        end = f"{b.booking_date.strftime('%Y%m%d')}T{end_time.strftime('%H%M%S')}"
        lines.extend([
            "BEGIN:VEVENT",
            f"UID:booking-{b.id}@customerflow.ai",
            f"DTSTART:{start}",
            f"DTEND:{end}",
            f"SUMMARY:{b.customer_name} — {b.service_description or 'Appointment'}",
            f"DESCRIPTION:Booking {b.id}",
            "END:VEVENT",
        ])
    lines.append("END:VCALENDAR")
    return "\r\n".join(lines) + "\r\n"
