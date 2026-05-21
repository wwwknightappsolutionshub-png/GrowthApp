"""Tenant booking settings."""
from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import log_action
from app.modules.booking.enterprise_models import BookingSettings
from app.modules.booking.enterprise_schemas import BookingSettingsUpdate


async def get_or_create_settings(db: AsyncSession, tenant_id: uuid.UUID) -> BookingSettings:
    row = (
        await db.execute(select(BookingSettings).where(BookingSettings.tenant_id == tenant_id))
    ).scalar_one_or_none()
    if row:
        return row
    row = BookingSettings(tenant_id=tenant_id)
    db.add(row)
    await db.flush()
    return row


async def update_settings(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    data: BookingSettingsUpdate,
    *,
    user_id: uuid.UUID | None = None,
) -> BookingSettings:
    row = await get_or_create_settings(db, tenant_id)
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(row, field, value)
    db.add(row)
    await db.flush()
    await log_action(
        db,
        action="booking.settings.update",
        resource="booking_settings",
        resource_id=tenant_id,
        tenant_id=tenant_id,
        user_id=user_id,
        metadata=data.model_dump(exclude_none=True),
    )
    await db.commit()
    await db.refresh(row)
    return row
