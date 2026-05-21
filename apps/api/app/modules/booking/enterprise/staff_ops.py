"""Staff, shifts, and blackouts."""
from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import log_action
from app.core.exceptions import NotFoundException
from app.modules.booking.enterprise_models import StaffBlackout, StaffShift
from app.modules.booking.enterprise_schemas import (
    StaffBlackoutCreate,
    StaffCreate,
    StaffShiftCreate,
    StaffUpdate,
)
from app.modules.booking.models import Staff


async def list_staff(db: AsyncSession, tenant_id: uuid.UUID) -> list[Staff]:
    return list(
        (
            await db.execute(
                select(Staff)
                .where(Staff.tenant_id == tenant_id)
                .order_by(Staff.name)
            )
        ).scalars().all()
    )


async def create_staff(
    db: AsyncSession, tenant_id: uuid.UUID, data: StaffCreate, *, user_id: uuid.UUID | None = None
) -> Staff:
    row = Staff(id=uuid.uuid4(), tenant_id=tenant_id, **data.model_dump())
    db.add(row)
    await db.flush()
    await log_action(db, "booking.staff.create", "staff", row.id, tenant_id=tenant_id, user_id=user_id)
    await db.commit()
    await db.refresh(row)
    return row


async def update_staff(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    staff_id: uuid.UUID,
    data: StaffUpdate,
    *,
    user_id: uuid.UUID | None = None,
) -> Staff:
    row = await _get_staff(db, tenant_id, staff_id)
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(row, field, value)
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return row


async def _get_staff(db: AsyncSession, tenant_id: uuid.UUID, staff_id: uuid.UUID) -> Staff:
    row = (
        await db.execute(select(Staff).where(Staff.id == staff_id, Staff.tenant_id == tenant_id))
    ).scalar_one_or_none()
    if not row:
        raise NotFoundException("Staff")
    return row


async def create_shift(db: AsyncSession, tenant_id: uuid.UUID, data: StaffShiftCreate) -> StaffShift:
    await _get_staff(db, tenant_id, data.staff_id)
    row = StaffShift(id=uuid.uuid4(), tenant_id=tenant_id, **data.model_dump())
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return row


async def list_shifts(
    db: AsyncSession, tenant_id: uuid.UUID, staff_id: uuid.UUID | None = None
) -> list[StaffShift]:
    q = select(StaffShift).where(StaffShift.tenant_id == tenant_id)
    if staff_id:
        q = q.where(StaffShift.staff_id == staff_id)
    return list((await db.execute(q.order_by(StaffShift.shift_date, StaffShift.start_time))).scalars().all())


async def create_blackout(db: AsyncSession, tenant_id: uuid.UUID, data: StaffBlackoutCreate) -> StaffBlackout:
    if data.staff_id:
        await _get_staff(db, tenant_id, data.staff_id)
    row = StaffBlackout(id=uuid.uuid4(), tenant_id=tenant_id, **data.model_dump())
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return row


async def list_blackouts(db: AsyncSession, tenant_id: uuid.UUID) -> list[StaffBlackout]:
    return list(
        (
            await db.execute(
                select(StaffBlackout)
                .where(StaffBlackout.tenant_id == tenant_id)
                .order_by(StaffBlackout.start_at.desc())
            )
        ).scalars().all()
    )
