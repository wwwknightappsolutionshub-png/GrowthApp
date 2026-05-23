"""Salon + Garage industry add-on SQLAlchemy models (no realtor tables).

InvoiceItem.line_kind is added by migration 036 (not declared on the core model).
"""
from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.db_types import JSONBType, UUIDType

# ---------------------------------------------------------------------------
# Booking — salon & garage
# ---------------------------------------------------------------------------


class BookingSessionService(Base):
    __tablename__ = "booking_session_services"
    __table_args__ = (
        UniqueConstraint("booking_id", "service_id", name="uq_booking_session_services_booking_service"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True
    )
    booking_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("bookings.id", ondelete="CASCADE"), nullable=False, index=True
    )
    service_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("booking_services.id", ondelete="CASCADE"), nullable=False
    )
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    duration_minutes: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class StaffSkill(Base):
    __tablename__ = "staff_skills"
    __table_args__ = (
        UniqueConstraint("tenant_id", "staff_id", "skill_code", name="uq_staff_skills_tenant_staff_code"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True
    )
    staff_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("staff.id", ondelete="CASCADE"), nullable=False, index=True
    )
    skill_code: Mapped[str] = mapped_column(String(80), nullable=False)
    proficiency_level: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ServiceRequiredSkill(Base):
    __tablename__ = "service_required_skills"
    __table_args__ = (
        UniqueConstraint("service_id", "skill_code", name="uq_service_required_skills_service_code"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True
    )
    service_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("booking_services.id", ondelete="CASCADE"), nullable=False, index=True
    )
    skill_code: Mapped[str] = mapped_column(String(80), nullable=False)
    min_proficiency: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class BookingResourceAllocation(Base):
    __tablename__ = "booking_resource_allocations"

    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True
    )
    booking_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("bookings.id", ondelete="CASCADE"), nullable=False, index=True
    )
    resource_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("booking_resources.id", ondelete="CASCADE"), nullable=False
    )
    allocated_from: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    allocated_to: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class BookingProductCatalog(Base):
    __tablename__ = "booking_product_catalog"
    __table_args__ = (UniqueConstraint("tenant_id", "sku", name="uq_booking_product_catalog_tenant_sku"),)

    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True
    )
    sku: Mapped[str] = mapped_column(String(80), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    unit_price_pence: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class BookingUpsellLine(Base):
    __tablename__ = "booking_upsell_lines"

    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True
    )
    booking_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("bookings.id", ondelete="CASCADE"), nullable=False, index=True
    )
    product_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("booking_product_catalog.id", ondelete="RESTRICT"), nullable=False
    )
    quantity: Mapped[int] = mapped_column(Integer, default=1)
    unit_price_pence: Mapped[int] = mapped_column(Integer, nullable=False)
    line_total_pence: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class MechanicSkill(Base):
    __tablename__ = "mechanic_skills"
    __table_args__ = (
        UniqueConstraint("tenant_id", "staff_id", "skill_code", name="uq_mechanic_skills_tenant_staff_code"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True
    )
    staff_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("staff.id", ondelete="CASCADE"), nullable=False, index=True
    )
    skill_code: Mapped[str] = mapped_column(String(80), nullable=False)
    certification_level: Mapped[str | None] = mapped_column(String(50))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class VehicleServiceEstimate(Base):
    __tablename__ = "vehicle_service_estimates"

    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True
    )
    make: Mapped[str] = mapped_column(String(80), nullable=False)
    model: Mapped[str] = mapped_column(String(80), nullable=False)
    model_year: Mapped[int | None] = mapped_column(Integer)
    service_id: Mapped[uuid.UUID | None] = mapped_column(
        UUIDType, ForeignKey("booking_services.id", ondelete="SET NULL")
    )
    service_name: Mapped[str | None] = mapped_column(String(255))
    estimated_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class PartsInventory(Base):
    __tablename__ = "parts_inventory"
    __table_args__ = (UniqueConstraint("tenant_id", "sku", name="uq_parts_inventory_tenant_sku"),)

    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True
    )
    sku: Mapped[str] = mapped_column(String(80), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str] = mapped_column(String(80), default="general")
    qty_on_hand: Mapped[int] = mapped_column(Integer, default=0)
    unit_cost_pence: Mapped[int] = mapped_column(Integer, default=0)
    reorder_level: Mapped[int | None] = mapped_column(Integer)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class BookingPartsReservation(Base):
    __tablename__ = "booking_parts_reservations"

    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True
    )
    booking_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("bookings.id", ondelete="CASCADE"), nullable=False, index=True
    )
    part_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("parts_inventory.id", ondelete="RESTRICT"), nullable=False
    )
    quantity_reserved: Mapped[int] = mapped_column(Integer, default=1)
    status: Mapped[str] = mapped_column(String(30), default="reserved")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


# ---------------------------------------------------------------------------
# Billing — salon & garage
# ---------------------------------------------------------------------------


class InvoiceTip(Base):
    __tablename__ = "invoice_tips"

    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True
    )
    invoice_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False, index=True
    )
    staff_id: Mapped[uuid.UUID | None] = mapped_column(
        UUIDType, ForeignKey("staff.id", ondelete="SET NULL")
    )
    amount_pence: Mapped[int] = mapped_column(Integer, nullable=False)
    method: Mapped[str] = mapped_column(String(50), default="card")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Membership(Base):
    __tablename__ = "memberships"

    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True
    )
    customer_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("customers.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="active")
    price_pence: Mapped[int] = mapped_column(Integer, default=0)
    billing_interval: Mapped[str] = mapped_column(String(20), default="monthly")
    stripe_subscription_id: Mapped[str | None] = mapped_column(String(255))
    started_at: Mapped[date | None] = mapped_column(Date)
    ends_at: Mapped[date | None] = mapped_column(Date)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class MembershipBenefit(Base):
    __tablename__ = "membership_benefits"

    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)
    membership_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("memberships.id", ondelete="CASCADE"), nullable=False, index=True
    )
    benefit_type: Mapped[str] = mapped_column(String(50), nullable=False)
    config: Mapped[dict] = mapped_column(JSONBType, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class IndustryServicePackage(Base):
    __tablename__ = "industry_service_packages"

    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    sessions_included: Mapped[int] = mapped_column(Integer, default=1)
    price_pence: Mapped[int] = mapped_column(Integer, default=0)
    valid_days: Mapped[int] = mapped_column(Integer, default=365)
    service_ids: Mapped[list] = mapped_column(JSONBType, default=list)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class PackageRedemption(Base):
    __tablename__ = "package_redemptions"

    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True
    )
    package_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("industry_service_packages.id", ondelete="CASCADE"), nullable=False
    )
    customer_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("customers.id", ondelete="CASCADE"), nullable=False, index=True
    )
    booking_id: Mapped[uuid.UUID | None] = mapped_column(
        UUIDType, ForeignKey("bookings.id", ondelete="SET NULL")
    )
    invoice_id: Mapped[uuid.UUID | None] = mapped_column(
        UUIDType, ForeignKey("invoices.id", ondelete="SET NULL")
    )
    redeemed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class IndustryInvoiceTemplate(Base):
    __tablename__ = "industry_invoice_templates"

    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True
    )
    vertical: Mapped[str] = mapped_column(String(30), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    template_body: Mapped[dict] = mapped_column(JSONBType, default=dict)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class PartsMarkupRule(Base):
    __tablename__ = "parts_markup_rules"
    __table_args__ = (UniqueConstraint("tenant_id", "category", name="uq_parts_markup_rules_tenant_category"),)

    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True
    )
    category: Mapped[str] = mapped_column(String(80), nullable=False)
    markup_percent: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class InvoiceWarranty(Base):
    __tablename__ = "invoice_warranties"

    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True
    )
    invoice_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False, index=True
    )
    warranty_months: Mapped[int] = mapped_column(Integer, default=12)
    terms: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


# ---------------------------------------------------------------------------
# Shared / CRM — salon & garage
# ---------------------------------------------------------------------------


class Vehicle(Base):
    __tablename__ = "vehicles"

    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True
    )
    customer_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("customers.id", ondelete="CASCADE"), nullable=False, index=True
    )
    vin: Mapped[str | None] = mapped_column(String(32))
    registration: Mapped[str | None] = mapped_column(String(20))
    make: Mapped[str | None] = mapped_column(String(80))
    model: Mapped[str | None] = mapped_column(String(80))
    model_year: Mapped[int | None] = mapped_column(Integer)
    mileage: Mapped[int | None] = mapped_column(Integer)
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class VehicleServiceRecord(Base):
    __tablename__ = "vehicle_service_records"

    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True
    )
    vehicle_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("vehicles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    booking_id: Mapped[uuid.UUID | None] = mapped_column(
        UUIDType, ForeignKey("bookings.id", ondelete="SET NULL")
    )
    service_date: Mapped[date] = mapped_column(Date, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    mileage_at_service: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class CustomerSalonProfile(Base):
    __tablename__ = "customer_salon_profiles"

    customer_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("customers.id", ondelete="CASCADE"), primary_key=True
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True
    )
    formula: Mapped[dict] = mapped_column(JSONBType, default=dict)
    allergies: Mapped[str | None] = mapped_column(Text)
    preferences: Mapped[dict] = mapped_column(JSONBType, default=dict)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class CustomerMediaTimeline(Base):
    __tablename__ = "customer_media_timeline"

    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True
    )
    customer_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("customers.id", ondelete="CASCADE"), nullable=False, index=True
    )
    media_url: Mapped[str] = mapped_column(Text, nullable=False)
    caption: Mapped[str | None] = mapped_column(Text)
    taken_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class IndustryRebookReminder(Base):
    __tablename__ = "industry_rebook_reminders"

    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True
    )
    customer_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("customers.id", ondelete="CASCADE"), nullable=False, index=True
    )
    service_id: Mapped[uuid.UUID | None] = mapped_column(
        UUIDType, ForeignKey("booking_services.id", ondelete="SET NULL")
    )
    due_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="pending")
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class VehiclePartsUsage(Base):
    __tablename__ = "vehicle_parts_usage"

    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True
    )
    vehicle_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("vehicles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    part_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("parts_inventory.id", ondelete="RESTRICT"), nullable=False
    )
    booking_id: Mapped[uuid.UUID | None] = mapped_column(
        UUIDType, ForeignKey("bookings.id", ondelete="SET NULL")
    )
    quantity: Mapped[int] = mapped_column(Integer, default=1)
    used_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class MaintenancePrediction(Base):
    __tablename__ = "maintenance_predictions"

    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True
    )
    vehicle_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("vehicles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    prediction_type: Mapped[str] = mapped_column(String(80), nullable=False)
    due_date: Mapped[date | None] = mapped_column(Date)
    confidence: Mapped[int] = mapped_column(Integer, default=50)
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class CustomerGarageScore(Base):
    __tablename__ = "customer_garage_scores"

    customer_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("customers.id", ondelete="CASCADE"), primary_key=True
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True
    )
    clv_score: Mapped[int] = mapped_column(Integer, default=0)
    reliability_score: Mapped[int] = mapped_column(Integer, default=0)
    score_metadata: Mapped[dict] = mapped_column(JSONBType, default=dict)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
