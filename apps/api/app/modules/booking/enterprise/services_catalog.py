"""Bookable services and resources CRUD."""
from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundException
from app.modules.booking.enterprise_schemas import (
    BookingResourceCreate,
    BookingServiceCreate,
    BookingServiceUpdate,
)
from app.modules.booking.enterprise_models import BookingResource, BookingService


async def list_services(db: AsyncSession, tenant_id: uuid.UUID, *, active_only: bool = True) -> list[BookingService]:
    q = select(BookingService).where(BookingService.tenant_id == tenant_id)
    if active_only:
        q = q.where(BookingService.is_active == True)  # noqa: E712
    return list((await db.execute(q.order_by(BookingService.sort_order, BookingService.name))).scalars().all())


async def create_service(db: AsyncSession, tenant_id: uuid.UUID, data: BookingServiceCreate) -> BookingService:
    row = BookingService(id=uuid.uuid4(), tenant_id=tenant_id, **data.model_dump())
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return row


async def update_service(
    db: AsyncSession, tenant_id: uuid.UUID, service_id: uuid.UUID, data: BookingServiceUpdate
) -> BookingService:
    row = await _get_service(db, tenant_id, service_id)
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(row, field, value)
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return row


async def _get_service(db: AsyncSession, tenant_id: uuid.UUID, service_id: uuid.UUID) -> BookingService:
    row = (
        await db.execute(
            select(BookingService).where(
                BookingService.id == service_id, BookingService.tenant_id == tenant_id
            )
        )
    ).scalar_one_or_none()
    if not row:
        raise NotFoundException("Service")
    return row


async def list_resources(db: AsyncSession, tenant_id: uuid.UUID) -> list[BookingResource]:
    return list(
        (
            await db.execute(
                select(BookingResource)
                .where(BookingResource.tenant_id == tenant_id, BookingResource.is_active == True)  # noqa: E712
            )
        ).scalars().all()
    )


async def create_resource(db: AsyncSession, tenant_id: uuid.UUID, data: BookingResourceCreate) -> BookingResource:
    row = BookingResource(id=uuid.uuid4(), tenant_id=tenant_id, **data.model_dump())
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return row
