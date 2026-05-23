import uuid
from datetime import date, datetime
from sqlalchemy import Date, DateTime, ForeignKey, Numeric, String, Text, Boolean, Integer, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from app.core.db_types import UUIDType, JSONBType


class Customer(Base):
    __tablename__ = "customers"
    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUIDType, ForeignKey("tenants.id"), nullable=False, index=True)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str | None] = mapped_column(String(100))
    email: Mapped[str | None] = mapped_column(String(255), index=True)
    phone: Mapped[str | None] = mapped_column(String(50))
    address: Mapped[str | None] = mapped_column(Text)
    postcode: Mapped[str | None] = mapped_column(String(20))
    notes: Mapped[str | None] = mapped_column(Text)
    source: Mapped[str | None] = mapped_column(String(100))
    gdpr_consent: Mapped[bool] = mapped_column(Boolean, default=False)
    gdpr_consent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    # Visit tracking & follow-up (CRM extension)
    first_visit_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    next_visit_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    requires_followup: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, server_default="false")
    followup_reminder_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    special_comments: Mapped[str | None] = mapped_column(Text, nullable=True)
    client_type: Mapped[str] = mapped_column(String(20), nullable=False, default="individual", server_default="individual")
    business_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    upsell_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    special_event: Mapped[str | None] = mapped_column(Text, nullable=True)
    needs_reminders: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, server_default="false")
    assigned_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUIDType, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    ref_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False, server_default="0")
    referral_program_id: Mapped[uuid.UUID | None] = mapped_column(
        UUIDType, ForeignKey("referral_programs.id", ondelete="SET NULL"), nullable=True, index=True
    )
    reward_amount: Mapped[float | None] = mapped_column(Numeric(14, 2), nullable=True)
    reward_type: Mapped[str | None] = mapped_column(String(30), nullable=True)
    reward_delivery_method: Mapped[str | None] = mapped_column(String(30), nullable=True)
    service_recurrency: Mapped[str | None] = mapped_column(String(30), nullable=True)
    service_renewal_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    service_renewal_invoice_id: Mapped[uuid.UUID | None] = mapped_column(UUIDType, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    deals: Mapped[list["Deal"]] = relationship("Deal", back_populates="customer")


class Deal(Base):
    __tablename__ = "deals"
    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUIDType, ForeignKey("tenants.id"), nullable=False, index=True)
    customer_id: Mapped[uuid.UUID] = mapped_column(UUIDType, ForeignKey("customers.id"), nullable=False)
    lead_id: Mapped[uuid.UUID | None] = mapped_column(UUIDType, ForeignKey("leads.id"), nullable=True)
    location_id: Mapped[uuid.UUID | None] = mapped_column(UUIDType, ForeignKey("locations.id"), nullable=True)
    assigned_user_id: Mapped[uuid.UUID | None] = mapped_column(UUIDType, ForeignKey("users.id"), nullable=True)
    pipeline_id: Mapped[uuid.UUID | None] = mapped_column(
        UUIDType, ForeignKey("crm_pipelines.id", ondelete="SET NULL"), nullable=True, index=True
    )
    stage_id: Mapped[uuid.UUID | None] = mapped_column(
        UUIDType, ForeignKey("crm_stages.id", ondelete="SET NULL"), nullable=True, index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    stage: Mapped[str] = mapped_column(String(50), default="New")
    stage_order: Mapped[int] = mapped_column(Integer, default=0)
    service_type: Mapped[str | None] = mapped_column(String(100))
    description: Mapped[str | None] = mapped_column(Text)
    value_pence: Mapped[int] = mapped_column(Integer, default=0)
    source: Mapped[str | None] = mapped_column(String(100))
    lost_reason: Mapped[str | None] = mapped_column(Text)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    customer: Mapped["Customer"] = relationship("Customer", back_populates="deals")
    activities: Mapped[list["DealActivity"]] = relationship("DealActivity", back_populates="deal", order_by="DealActivity.created_at.desc()")


class DealActivity(Base):
    __tablename__ = "deal_activities"
    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUIDType, ForeignKey("tenants.id"), nullable=False, index=True)
    deal_id: Mapped[uuid.UUID] = mapped_column(UUIDType, ForeignKey("deals.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[uuid.UUID | None] = mapped_column(UUIDType, ForeignKey("users.id"), nullable=True)
    type: Mapped[str] = mapped_column(String(50), nullable=False)
    body: Mapped[str | None] = mapped_column(Text)
    extra_metadata: Mapped[dict] = mapped_column("metadata", JSONBType, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    deal: Mapped["Deal"] = relationship("Deal", back_populates="activities")
