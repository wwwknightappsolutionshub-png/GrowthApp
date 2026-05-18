from uuid import UUID
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.dependencies import CurrentTenantContext
from app.modules.booking import service
from app.modules.booking.schemas import BookingCreate, BookingUpdate, BookingResponse, BookingListResponse
from app.modules.auth.schemas import MessageResponse

router = APIRouter(prefix="/bookings", tags=["Bookings"])


@router.get("", response_model=BookingListResponse)
async def list_bookings(ctx: CurrentTenantContext, db: AsyncSession = Depends(get_db), page: int = Query(1, ge=1), page_size: int = Query(25, ge=1, le=100)):
    _, tenant, _ = ctx
    items, total = await service.list_bookings(db, tenant.id, page, page_size)
    return {"items": items, "total": total, "page": page, "page_size": page_size}


@router.post("", response_model=BookingResponse, status_code=201)
async def create_booking(data: BookingCreate, ctx: CurrentTenantContext, db: AsyncSession = Depends(get_db)):
    _, tenant, _ = ctx
    return await service.create_booking(db, tenant.id, data)


@router.get("/{booking_id}", response_model=BookingResponse)
async def get_booking(booking_id: UUID, ctx: CurrentTenantContext, db: AsyncSession = Depends(get_db)):
    _, tenant, _ = ctx
    return await service.get_booking(db, tenant.id, booking_id)


@router.patch("/{booking_id}", response_model=BookingResponse)
async def update_booking(booking_id: UUID, data: BookingUpdate, ctx: CurrentTenantContext, db: AsyncSession = Depends(get_db)):
    _, tenant, _ = ctx
    return await service.update_booking(db, tenant.id, booking_id, data)
