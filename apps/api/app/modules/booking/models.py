import uuid
from datetime import datetime, date, time

from sqlalchemy import DateTime, ForeignKey, String, Text, Boolean, Integer, Date, Time, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.db_types import UUIDType, JSONBType

# Enterprise tables (imported for Alembic metadata registration)
from app.modules.booking.enterprise_models import (  # noqa: F401
    BookingAbandonedSession,
    BookingCalendarConnection,
    BookingCustomerCredit,
    BookingNotificationQueue,
    BookingPackage,
    BookingPromoCode,
    BookingResource,
    BookingService,
    BookingSettings,
    StaffBlackout,
    StaffShift,
)


class Staff(Base):
    __tablename__ = "staff"
    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUIDType, ForeignKey("tenants.id"), nullable=False, index=True)
    user_id: Mapped[uuid.UUID | None] = mapped_column(UUIDType, ForeignKey("users.id"), nullable=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str | None] = mapped_column(String(255))
    phone: Mapped[str | None] = mapped_column(String(50))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    working_hours: Mapped[dict] = mapped_column(JSONBType, default=dict)
    role: Mapped[str] = mapped_column(String(30), default="staff")
    permissions: Mapped[dict] = mapped_column(JSONBType, default=dict)
    location_ids: Mapped[list] = mapped_column(JSONBType, default=list)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    joined_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class AvailabilitySlot(Base):
    __tablename__ = "availability_slots"
    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUIDType, ForeignKey("tenants.id"), nullable=False, index=True)
    staff_id: Mapped[uuid.UUID | None] = mapped_column(UUIDType, ForeignKey("staff.id"), nullable=True)
    location_id: Mapped[uuid.UUID | None] = mapped_column(UUIDType, nullable=True)
    resource_id: Mapped[uuid.UUID | None] = mapped_column(UUIDType, nullable=True)
    service_id: Mapped[uuid.UUID | None] = mapped_column(UUIDType, nullable=True)
    slot_date: Mapped[date] = mapped_column(Date, nullable=False)
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)
    duration_minutes: Mapped[int] = mapped_column(Integer, default=60)
    is_booked: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Booking(Base):
    __tablename__ = "bookings"
    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUIDType, ForeignKey("tenants.id"), nullable=False, index=True)
    deal_id: Mapped[uuid.UUID | None] = mapped_column(UUIDType, ForeignKey("deals.id"), nullable=True)
    customer_id: Mapped[uuid.UUID | None] = mapped_column(UUIDType, ForeignKey("customers.id"), nullable=True)
    slot_id: Mapped[uuid.UUID | None] = mapped_column(UUIDType, ForeignKey("availability_slots.id"), nullable=True)
    staff_id: Mapped[uuid.UUID | None] = mapped_column(UUIDType, ForeignKey("staff.id"), nullable=True)
    location_id: Mapped[uuid.UUID | None] = mapped_column(UUIDType, ForeignKey("locations.id"), nullable=True)
    service_id: Mapped[uuid.UUID | None] = mapped_column(UUIDType, nullable=True)
    resource_id: Mapped[uuid.UUID | None] = mapped_column(UUIDType, nullable=True)
    customer_name: Mapped[str] = mapped_column(String(255), nullable=False)
    customer_email: Mapped[str | None] = mapped_column(String(255))
    customer_phone: Mapped[str | None] = mapped_column(String(50))
    service_description: Mapped[str | None] = mapped_column(Text)
    booking_date: Mapped[date] = mapped_column(Date, nullable=False)
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time | None] = mapped_column(Time)
    timezone: Mapped[str] = mapped_column(String(64), default="Europe/London")
    duration_minutes: Mapped[int] = mapped_column(Integer, default=60)
    status: Mapped[str] = mapped_column(String(30), default="confirmed")
    lead_status: Mapped[str] = mapped_column(String(30), default="booked")
    deposit_required_pence: Mapped[int] = mapped_column(Integer, default=0)
    deposit_paid_pence: Mapped[int] = mapped_column(Integer, default=0)
    no_show_fee_pence: Mapped[int] = mapped_column(Integer, default=0)
    prepaid_pence: Mapped[int] = mapped_column(Integer, default=0)
    service_fee_pence: Mapped[int] = mapped_column(Integer, default=0)
    refund_pence: Mapped[int] = mapped_column(Integer, default=0)
    refunded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    stripe_payment_intent_id: Mapped[str | None] = mapped_column(String(255))
    stripe_setup_intent_id: Mapped[str | None] = mapped_column(String(255))
    package_id: Mapped[uuid.UUID | None] = mapped_column(UUIDType, nullable=True)
    promo_code: Mapped[str | None] = mapped_column(String(40))
    manage_token: Mapped[str | None] = mapped_column(String(64), unique=True, index=True)
    channel: Mapped[str | None] = mapped_column(String(50))
    utm_source: Mapped[str | None] = mapped_column(String(100))
    utm_medium: Mapped[str | None] = mapped_column(String(100))
    utm_campaign: Mapped[str | None] = mapped_column(String(100))
    custom_fields: Mapped[dict] = mapped_column(JSONBType, default=dict)
    intake_responses: Mapped[dict] = mapped_column(JSONBType, default=dict)
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
