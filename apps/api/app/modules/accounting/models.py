from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.db_types import JSONBType, UUIDType

FEATURE_ACCOUNTING = "accounting"


class TenantAddon(Base):
    __tablename__ = "tenant_addons"
    __table_args__ = (UniqueConstraint("tenant_id", "feature_code", name="uq_tenant_addons_tenant_feature"),)

    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUIDType, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    feature_code: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="active")
    stripe_subscription_item_id: Mapped[str | None] = mapped_column(String(255))
    stripe_checkout_session_id: Mapped[str | None] = mapped_column(String(255))
    granted_by: Mapped[uuid.UUID | None] = mapped_column(UUIDType, ForeignKey("users.id", ondelete="SET NULL"))
    granted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class TenantAccountingSettings(Base):
    __tablename__ = "tenant_accounting_settings"

    tenant_id: Mapped[uuid.UUID] = mapped_column(UUIDType, ForeignKey("tenants.id", ondelete="CASCADE"), primary_key=True)
    vat_scheme: Mapped[str] = mapped_column(String(30), default="standard")
    flat_rate_percent: Mapped[int | None] = mapped_column(Integer)
    late_fee_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    late_fee_percent: Mapped[int] = mapped_column(Integer, default=0)
    auto_invoice_on_booking_complete: Mapped[bool] = mapped_column(Boolean, default=True)
    reminder_days: Mapped[list] = mapped_column(JSONBType, default=lambda: [7, 14])
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class Expense(Base):
    __tablename__ = "expenses"

    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUIDType, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    customer_id: Mapped[uuid.UUID | None] = mapped_column(UUIDType, ForeignKey("customers.id", ondelete="SET NULL"))
    deal_id: Mapped[uuid.UUID | None] = mapped_column(UUIDType, ForeignKey("deals.id", ondelete="SET NULL"))
    booking_id: Mapped[uuid.UUID | None] = mapped_column(UUIDType, ForeignKey("bookings.id", ondelete="SET NULL"))
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    amount_pence: Mapped[int] = mapped_column(Integer, nullable=False)
    vat_rate: Mapped[int] = mapped_column(Integer, default=20)
    vat_pence: Mapped[int] = mapped_column(Integer, default=0)
    category: Mapped[str] = mapped_column(String(80), default="general")
    expense_date: Mapped[date] = mapped_column(Date, nullable=False)
    receipt_url: Mapped[str | None] = mapped_column(Text)
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class RecurringInvoiceSchedule(Base):
    __tablename__ = "recurring_invoice_schedules"

    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUIDType, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    customer_id: Mapped[uuid.UUID] = mapped_column(UUIDType, ForeignKey("customers.id", ondelete="CASCADE"), nullable=False)
    deal_id: Mapped[uuid.UUID | None] = mapped_column(UUIDType, ForeignKey("deals.id", ondelete="SET NULL"))
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)
    interval_unit: Mapped[str] = mapped_column(String(20), default="monthly")
    interval_count: Mapped[int] = mapped_column(Integer, default=1)
    next_run_at: Mapped[date] = mapped_column(Date, nullable=False)
    line_items: Mapped[list] = mapped_column(JSONBType, default=list)
    auto_charge: Mapped[bool] = mapped_column(Boolean, default=False)
    auto_send: Mapped[bool] = mapped_column(Boolean, default=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
