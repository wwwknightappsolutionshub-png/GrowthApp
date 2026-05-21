"""Booking analytics aggregates."""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.booking.enterprise_schemas import BookingAnalyticsResponse
from app.modules.booking.models import Booking, Staff


async def get_booking_analytics(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    *,
    days: int = 30,
) -> BookingAnalyticsResponse:
    since = datetime.now(timezone.utc).date() - timedelta(days=days)

    rows = (
        await db.execute(
            select(Booking).where(
                Booking.tenant_id == tenant_id,
                Booking.booking_date >= since,
            )
        )
    ).scalars().all()

    total = len(rows)
    confirmed = sum(1 for b in rows if b.status == "confirmed")
    completed = sum(1 for b in rows if b.status == "completed")
    cancelled = sum(1 for b in rows if b.status == "cancelled")
    no_show = sum(1 for b in rows if b.status == "no_show")

    cancellation_rate = round((cancelled / total * 100) if total else 0.0, 2)
    no_show_rate = round((no_show / total * 100) if total else 0.0, 2)

    deposit_total = sum(b.deposit_paid_pence for b in rows)
    prepaid_total = sum(b.prepaid_pence for b in rows)

    by_staff: dict[str, dict] = {}
    for b in rows:
        key = str(b.staff_id) if b.staff_id else "unassigned"
        if key not in by_staff:
            by_staff[key] = {"staff_id": key, "bookings": 0, "completed": 0, "revenue_pence": 0}
        by_staff[key]["bookings"] += 1
        if b.status == "completed":
            by_staff[key]["completed"] += 1
        by_staff[key]["revenue_pence"] += b.deposit_paid_pence + b.prepaid_pence

    staff_names = {}
    if by_staff:
        staff_rows = (
            await db.execute(select(Staff).where(Staff.tenant_id == tenant_id))
        ).scalars().all()
        staff_names = {str(s.id): s.name for s in staff_rows}

    revenue_by_staff = []
    for k, v in by_staff.items():
        revenue_by_staff.append({**v, "staff_name": staff_names.get(k, "Unassigned")})

    channel_counts: dict[str, int] = {}
    for b in rows:
        ch = b.channel or "direct"
        channel_counts[ch] = channel_counts.get(ch, 0) + 1
    bookings_by_channel = [{"channel": k, "count": v} for k, v in sorted(channel_counts.items(), key=lambda x: -x[1])]

    booked_leads = sum(1 for b in rows if b.lead_status == "booked")
    lead_conversion_rate = round((booked_leads / total * 100) if total else 0.0, 2)

    from app.modules.booking.enterprise.slots import list_slots

    slots = await list_slots(db, tenant_id, from_date=since)
    booked_slots = sum(1 for s in slots if s.is_booked)
    utilization_rate = round((booked_slots / len(slots) * 100) if slots else 0.0, 2)

    return BookingAnalyticsResponse(
        total_bookings=total,
        confirmed=confirmed,
        completed=completed,
        cancelled=cancelled,
        no_show=no_show,
        cancellation_rate=cancellation_rate,
        no_show_rate=no_show_rate,
        total_deposit_pence=deposit_total,
        total_prepaid_pence=prepaid_total,
        revenue_by_staff=revenue_by_staff,
        bookings_by_channel=bookings_by_channel,
        utilization_rate=utilization_rate,
        lead_conversion_rate=lead_conversion_rate,
    )
