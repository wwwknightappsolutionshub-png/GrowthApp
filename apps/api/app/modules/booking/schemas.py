from datetime import datetime, date, time
from uuid import UUID
from pydantic import BaseModel


class PublicBookingCreate(BaseModel):
    customer_name: str
    customer_email: str | None = None
    customer_phone: str | None = None
    service_description: str | None = None
    booking_date: date
    start_time: time
    notes: str | None = None
    slot_id: UUID | None = None


class BookingCreate(PublicBookingCreate):
    deal_id: UUID | None = None
    customer_id: UUID | None = None
    staff_id: UUID | None = None
    deposit_required_pence: int = 0


class BookingUpdate(BaseModel):
    status: str | None = None
    notes: str | None = None
    booking_date: date | None = None
    start_time: time | None = None


class BookingResponse(BaseModel):
    model_config = {"from_attributes": True}
    id: UUID
    tenant_id: UUID
    customer_name: str
    customer_email: str | None
    customer_phone: str | None
    service_description: str | None
    booking_date: date
    start_time: time
    status: str
    deposit_required_pence: int
    deposit_paid_pence: int
    notes: str | None
    created_at: datetime


class BookingListResponse(BaseModel):
    items: list[BookingResponse]
    total: int
    page: int
    page_size: int
