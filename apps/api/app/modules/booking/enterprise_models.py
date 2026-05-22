"""Enterprise booking tables — settings, services, resources, packages, queue."""
from __future__ import annotations

import uuid
from datetime import date, datetime, time

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    Time,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.db_types import JSONBType, UUIDType


class BookingSettings(Base):
    __tablename__ = "booking_settings"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("tenants.id", ondelete="CASCADE"), primary_key=True
    )
    timezone: Mapped[str] = mapped_column(String(64), default="Europe/London")
    default_duration_minutes: Mapped[int] = mapped_column(Integer, default=60)
    deposit_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    default_deposit_pence: Mapped[int] = mapped_column(Integer, default=0)
    no_show_fee_pence: Mapped[int] = mapped_column(Integer, default=0)
    service_fee_percent: Mapped[float] = mapped_column(Numeric(5, 2), default=0)
    allow_self_reschedule: Mapped[bool] = mapped_column(Boolean, default=True)
    allow_self_cancel: Mapped[bool] = mapped_column(Boolean, default=True)
    min_notice_hours: Mapped[int] = mapped_column(Integer, default=24)
    overbooking_allowed: Mapped[bool] = mapped_column(Boolean, default=False)
    business_hours: Mapped[dict] = mapped_column(JSONBType, default=dict)
    automation_config: Mapped[dict] = mapped_column(JSONBType, default=dict)
    google_pixel_id: Mapped[str | None] = mapped_column(String(100))
    meta_pixel_id: Mapped[str | None] = mapped_column(String(100))
    widget_primary_color: Mapped[str | None] = mapped_column(String(20))
    intake_questions: Mapped[list] = mapped_column(JSONBType, default=list)
    booking_form_override: Mapped[dict] = mapped_column(JSONBType, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class BookingService(Base):
    __tablename__ = "booking_services"

    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUIDType, ForeignKey("tenants.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    duration_minutes: Mapped[int] = mapped_column(Integer, default=60)
    price_pence: Mapped[int] = mapped_column(Integer, default=0)
    deposit_pence: Mapped[int] = mapped_column(Integer, default=0)
    location_id: Mapped[uuid.UUID | None] = mapped_column(UUIDType, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class BookingResource(Base):
    __tablename__ = "booking_resources"

    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUIDType, ForeignKey("tenants.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    resource_type: Mapped[str] = mapped_column(String(30), default="room")
    location_id: Mapped[uuid.UUID | None] = mapped_column(UUIDType, nullable=True)
    capacity: Mapped[int] = mapped_column(Integer, default=1)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class StaffShift(Base):
    __tablename__ = "staff_shifts"

    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUIDType, ForeignKey("tenants.id"), nullable=False, index=True)
    staff_id: Mapped[uuid.UUID] = mapped_column(UUIDType, ForeignKey("staff.id", ondelete="CASCADE"), nullable=False, index=True)
    location_id: Mapped[uuid.UUID | None] = mapped_column(UUIDType, nullable=True)
    shift_date: Mapped[date] = mapped_column(Date, nullable=False)
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class StaffBlackout(Base):
    __tablename__ = "staff_blackouts"

    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUIDType, ForeignKey("tenants.id"), nullable=False, index=True)
    staff_id: Mapped[uuid.UUID | None] = mapped_column(UUIDType, ForeignKey("staff.id", ondelete="CASCADE"), nullable=True)
    location_id: Mapped[uuid.UUID | None] = mapped_column(UUIDType, nullable=True)
    start_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    reason: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class BookingPackage(Base):
    __tablename__ = "booking_packages"

    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUIDType, ForeignKey("tenants.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    sessions_included: Mapped[int] = mapped_column(Integer, default=1)
    price_pence: Mapped[int] = mapped_column(Integer, default=0)
    valid_days: Mapped[int] = mapped_column(Integer, default=365)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class BookingCustomerCredit(Base):
    __tablename__ = "booking_customer_credits"

    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUIDType, ForeignKey("tenants.id"), nullable=False, index=True)
    customer_id: Mapped[uuid.UUID | None] = mapped_column(UUIDType, nullable=True)
    customer_email: Mapped[str | None] = mapped_column(String(255))
    package_id: Mapped[uuid.UUID | None] = mapped_column(
        UUIDType, ForeignKey("booking_packages.id", ondelete="SET NULL"), nullable=True
    )
    sessions_remaining: Mapped[int] = mapped_column(Integer, default=0)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class BookingPromoCode(Base):
    __tablename__ = "booking_promo_codes"

    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUIDType, ForeignKey("tenants.id"), nullable=False, index=True)
    code: Mapped[str] = mapped_column(String(40), nullable=False)
    discount_percent: Mapped[int] = mapped_column(Integer, default=0)
    discount_pence: Mapped[int] = mapped_column(Integer, default=0)
    max_uses: Mapped[int | None] = mapped_column(Integer)
    uses_count: Mapped[int] = mapped_column(Integer, default=0)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class BookingCalendarConnection(Base):
    __tablename__ = "booking_calendar_connections"

    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUIDType, ForeignKey("tenants.id"), nullable=False, index=True)
    staff_id: Mapped[uuid.UUID | None] = mapped_column(UUIDType, ForeignKey("staff.id", ondelete="SET NULL"), nullable=True)
    provider: Mapped[str] = mapped_column(String(20), nullable=False)
    external_calendar_id: Mapped[str | None] = mapped_column(String(255))
    access_token_enc: Mapped[str | None] = mapped_column(Text)
    refresh_token_enc: Mapped[str | None] = mapped_column(Text)
    sync_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class BookingNotificationQueue(Base):
    __tablename__ = "booking_notification_queue"

    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUIDType, ForeignKey("tenants.id"), nullable=False, index=True)
    booking_id: Mapped[uuid.UUID | None] = mapped_column(
        UUIDType, ForeignKey("bookings.id", ondelete="CASCADE"), nullable=True
    )
    channel: Mapped[str] = mapped_column(String(20), nullable=False)
    notification_type: Mapped[str] = mapped_column(String(50), nullable=False)
    recipient: Mapped[str] = mapped_column(String(255), nullable=False)
    payload: Mapped[dict] = mapped_column(JSONBType, default=dict)
    scheduled_for: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    error_message: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class BookingAbandonedSession(Base):
    __tablename__ = "booking_abandoned_sessions"

    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUIDType, ForeignKey("tenants.id"), nullable=False, index=True)
    session_token: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    customer_email: Mapped[str | None] = mapped_column(String(255))
    payload: Mapped[dict] = mapped_column(JSONBType, default=dict)
    recovered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
