"""Pydantic schemas for enterprise booking endpoints."""
from __future__ import annotations

from datetime import date, datetime, time
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


# ── Settings ──────────────────────────────────────────────────────────────────

class ClientReminderRequest(BaseModel):
    channel: Literal["email", "sms"] = "email"


class FeedbackRequestBody(BaseModel):
    channels: list[Literal["email", "in_app"]] = Field(default_factory=lambda: ["email", "in_app"])


class BookingSettingsUpdate(BaseModel):
    timezone: str | None = None
    default_duration_minutes: int | None = Field(None, ge=15, le=480)
    deposit_enabled: bool | None = None
    default_deposit_pence: int | None = Field(None, ge=0)
    no_show_fee_pence: int | None = Field(None, ge=0)
    service_fee_percent: float | None = Field(None, ge=0, le=100)
    allow_self_reschedule: bool | None = None
    allow_self_cancel: bool | None = None
    min_notice_hours: int | None = Field(None, ge=0, le=168)
    overbooking_allowed: bool | None = None
    business_hours: dict[str, Any] | None = None
    automation_config: dict[str, Any] | None = None
    google_pixel_id: str | None = None
    meta_pixel_id: str | None = None
    widget_primary_color: str | None = None
    intake_questions: list[dict[str, Any]] | None = None
    booking_form_override: dict[str, Any] | None = None


class BookingSettingsResponse(BaseModel):
    model_config = {"from_attributes": True}
    tenant_id: UUID
    timezone: str
    default_duration_minutes: int
    deposit_enabled: bool
    default_deposit_pence: int
    no_show_fee_pence: int
    service_fee_percent: float
    allow_self_reschedule: bool
    allow_self_cancel: bool
    min_notice_hours: int
    overbooking_allowed: bool
    business_hours: dict[str, Any]
    automation_config: dict[str, Any]
    google_pixel_id: str | None
    meta_pixel_id: str | None
    widget_primary_color: str | None
    intake_questions: list[dict[str, Any]]
    booking_form_override: dict[str, Any] = Field(default_factory=dict)


class BookingFormSchemaResponse(BaseModel):
    category: str
    form_schema: dict[str, Any] = Field(serialization_alias="schema")
    is_tenant_override: bool = False

    model_config = {"populate_by_name": True}


class BookingFormTemplateResponse(BaseModel):
    category: str
    name: str
    form_schema: dict[str, Any] = Field(serialization_alias="schema")
    updated_at: datetime | None = None

    model_config = {"populate_by_name": True}


class BookingFormTemplateUpdate(BaseModel):
    name: str | None = None
    form_schema: dict[str, Any] = Field(serialization_alias="schema")

    model_config = {"populate_by_name": True}


# ── Services (bookable) ───────────────────────────────────────────────────────

class BookingServiceCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    duration_minutes: int = Field(60, ge=15, le=480)
    price_pence: int = Field(0, ge=0)
    deposit_pence: int = Field(0, ge=0)
    location_id: UUID | None = None
    sort_order: int = 0


class BookingServiceUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    duration_minutes: int | None = Field(None, ge=15, le=480)
    price_pence: int | None = Field(None, ge=0)
    deposit_pence: int | None = Field(None, ge=0)
    location_id: UUID | None = None
    is_active: bool | None = None
    sort_order: int | None = None


class BookingServiceResponse(BaseModel):
    model_config = {"from_attributes": True}
    id: UUID
    tenant_id: UUID
    name: str
    description: str | None
    duration_minutes: int
    price_pence: int
    deposit_pence: int
    location_id: UUID | None
    is_active: bool
    sort_order: int


# ── Resources ─────────────────────────────────────────────────────────────────

class BookingResourceCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    resource_type: Literal["room", "equipment", "vehicle", "other"] = "room"
    location_id: UUID | None = None
    capacity: int = Field(1, ge=1, le=100)


class BookingResourceResponse(BaseModel):
    model_config = {"from_attributes": True}
    id: UUID
    tenant_id: UUID
    name: str
    resource_type: str
    location_id: UUID | None
    capacity: int
    is_active: bool


# ── Staff ─────────────────────────────────────────────────────────────────────

class StaffCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    email: str | None = None
    phone: str | None = None
    address: str | None = None
    joined_at: datetime | None = None
    user_id: UUID | None = None
    role: str = "staff"
    permissions: dict[str, Any] = Field(default_factory=dict)
    location_ids: list[str] = Field(default_factory=list)
    working_hours: dict[str, Any] = Field(default_factory=dict)


class StaffUpdate(BaseModel):
    name: str | None = None
    email: str | None = None
    phone: str | None = None
    address: str | None = None
    joined_at: datetime | None = None
    is_active: bool | None = None
    role: str | None = None
    permissions: dict[str, Any] | None = None
    location_ids: list[str] | None = None
    working_hours: dict[str, Any] | None = None


class StaffResponse(BaseModel):
    model_config = {"from_attributes": True}
    id: UUID
    tenant_id: UUID
    name: str
    email: str | None
    phone: str | None
    address: str | None = None
    joined_at: datetime | None = None
    is_active: bool
    role: str
    permissions: dict[str, Any]
    location_ids: list
    working_hours: dict[str, Any]
    created_at: datetime | None = None


class StaffShiftCreate(BaseModel):
    staff_id: UUID
    shift_date: date
    start_time: time
    end_time: time
    location_id: UUID | None = None

    @field_validator("end_time")
    @classmethod
    def end_after_start(cls, v: time, info) -> time:
        start = info.data.get("start_time")
        if start and v <= start:
            raise ValueError("end_time must be after start_time")
        return v


class StaffBlackoutCreate(BaseModel):
    staff_id: UUID | None = None
    location_id: UUID | None = None
    start_at: datetime
    end_at: datetime
    reason: str | None = None


# ── Slots ─────────────────────────────────────────────────────────────────────

class SlotGenerateRequest(BaseModel):
    staff_id: UUID | None = None
    location_id: UUID | None = None
    resource_id: UUID | None = None
    service_id: UUID | None = None
    from_date: date
    to_date: date
    slot_duration_minutes: int = Field(60, ge=15, le=240)
    daily_start: time = time(9, 0)
    daily_end: time = time(17, 0)
    exclude_weekends: bool = True


class AvailabilitySlotResponse(BaseModel):
    model_config = {"from_attributes": True}
    id: UUID
    slot_date: date
    start_time: time
    end_time: time
    duration_minutes: int
    is_booked: bool
    staff_id: UUID | None
    location_id: UUID | None
    resource_id: UUID | None
    service_id: UUID | None


# ── Payments ──────────────────────────────────────────────────────────────────

class BookingPaymentIntentRequest(BaseModel):
    booking_id: UUID | None = None
    amount_pence: int = Field(..., ge=50)
    purpose: Literal["deposit", "prepaid", "no_show_fee", "full_payment"] = "deposit"
    customer_email: str | None = None


class BookingPaymentIntentResponse(BaseModel):
    client_secret: str
    payment_intent_id: str
    amount_pence: int


class BookingRefundRequest(BaseModel):
    amount_pence: int | None = Field(None, ge=1)
    reason: str | None = None


# ── Packages & promos ─────────────────────────────────────────────────────────

class BookingPackageCreate(BaseModel):
    name: str
    sessions_included: int = Field(1, ge=1)
    price_pence: int = Field(0, ge=0)
    valid_days: int = Field(365, ge=1)


class BookingPromoCreate(BaseModel):
    code: str = Field(..., min_length=3, max_length=40)
    discount_percent: int = Field(0, ge=0, le=100)
    discount_pence: int = Field(0, ge=0)
    max_uses: int | None = None
    expires_at: datetime | None = None


# ── Public / widget ───────────────────────────────────────────────────────────

class PublicWidgetConfigResponse(BaseModel):
    tenant_slug: str
    tenant_name: str
    timezone: str
    services: list[BookingServiceResponse]
    widget_primary_color: str | None
    google_pixel_id: str | None
    meta_pixel_id: str | None
    intake_questions: list[dict[str, Any]]
    booking_form: dict[str, Any] = Field(default_factory=dict)
    deposit_enabled: bool
    default_deposit_pence: int


class PublicManageBookingRequest(BaseModel):
    action: Literal["reschedule", "cancel"]
    booking_date: date | None = None
    start_time: time | None = None
    slot_id: UUID | None = None


class AbandonedSessionCreate(BaseModel):
    session_token: str
    customer_email: str | None = None
    payload: dict[str, Any] = Field(default_factory=dict)


# ── Analytics ─────────────────────────────────────────────────────────────────

class BookingAnalyticsResponse(BaseModel):
    total_bookings: int
    confirmed: int
    completed: int
    cancelled: int
    no_show: int
    cancellation_rate: float
    no_show_rate: float
    total_deposit_pence: int
    total_prepaid_pence: int
    revenue_by_staff: list[dict[str, Any]]
    bookings_by_channel: list[dict[str, Any]]
    utilization_rate: float
    lead_conversion_rate: float


# ── Calendar ──────────────────────────────────────────────────────────────────

class CalendarConnectionCreate(BaseModel):
    provider: Literal["google", "ical", "outlook"]
    staff_id: UUID | None = None
    external_calendar_id: str | None = None
    sync_enabled: bool = True


class CalendarSyncResponse(BaseModel):
    synced: int
    provider: str
    ical_feed_url: str | None = None
