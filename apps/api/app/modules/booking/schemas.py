from datetime import datetime, date, time
from uuid import UUID
from typing import Any

from pydantic import BaseModel, Field


class PublicBookingCreate(BaseModel):
    customer_name: str
    customer_email: str | None = None
    customer_phone: str | None = None
    service_description: str | None = None
    booking_date: date
    start_time: time
    notes: str | None = None
    slot_id: UUID | None = None
    staff_id: UUID | None = None
    location_id: UUID | None = None
    service_id: UUID | None = None
    resource_id: UUID | None = None
    duration_minutes: int | None = None
    timezone: str | None = None
    channel: str | None = "widget"
    utm_source: str | None = None
    utm_medium: str | None = None
    utm_campaign: str | None = None
    promo_code: str | None = None
    intake_responses: dict[str, Any] = Field(default_factory=dict)
    custom_fields: dict[str, Any] = Field(default_factory=dict)
    prepaid_pence: int = 0


class BookingCreate(PublicBookingCreate):
    deal_id: UUID | None = None
    customer_id: UUID | None = None
    deposit_required_pence: int = 0
    lead_status: str = "booked"


class BookingUpdate(BaseModel):
    status: str | None = None
    notes: str | None = None
    booking_date: date | None = None
    start_time: time | None = None
    lead_status: str | None = None
    custom_fields: dict[str, Any] | None = None


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
    end_time: time | None = None
    status: str
    lead_status: str = "booked"
    deposit_required_pence: int
    deposit_paid_pence: int
    prepaid_pence: int = 0
    no_show_fee_pence: int = 0
    service_fee_pence: int = 0
    refund_pence: int = 0
    duration_minutes: int = 60
    timezone: str = "Europe/London"
    staff_id: UUID | None = None
    location_id: UUID | None = None
    service_id: UUID | None = None
    resource_id: UUID | None = None
    manage_token: str | None = None
    channel: str | None = None
    notes: str | None
    created_at: datetime


class BookingListResponse(BaseModel):
    items: list[BookingResponse]
    total: int
    page: int
    page_size: int


class BookingTimelineResponse(BaseModel):
    booking_id: UUID
    customer_name: str
    lead_status: str
    events: list[dict[str, Any]]
