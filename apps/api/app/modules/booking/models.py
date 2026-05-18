import uuid
from datetime import datetime, date, time
from sqlalchemy import DateTime, ForeignKey, String, Text, Boolean, Integer, Date, Time, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from app.core.db_types import UUIDType, JSONBType


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
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class AvailabilitySlot(Base):
    __tablename__ = "availability_slots"
    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUIDType, ForeignKey("tenants.id"), nullable=False, index=True)
    staff_id: Mapped[uuid.UUID | None] = mapped_column(UUIDType, ForeignKey("staff.id"), nullable=True)
    slot_date: Mapped[date] = mapped_column(Date, nullable=False)
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)
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
    customer_name: Mapped[str] = mapped_column(String(255), nullable=False)
    customer_email: Mapped[str | None] = mapped_column(String(255))
    customer_phone: Mapped[str | None] = mapped_column(String(50))
    service_description: Mapped[str | None] = mapped_column(Text)
    booking_date: Mapped[date] = mapped_column(Date, nullable=False)
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time | None] = mapped_column(Time)
    status: Mapped[str] = mapped_column(String(30), default="confirmed")
    deposit_required_pence: Mapped[int] = mapped_column(Integer, default=0)
    deposit_paid_pence: Mapped[int] = mapped_column(Integer, default=0)
    stripe_payment_intent_id: Mapped[str | None] = mapped_column(String(255))
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
