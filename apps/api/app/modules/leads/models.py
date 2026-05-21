import uuid
from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, Boolean, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from app.core.db_types import UUIDType, JSONBType

# Statuses for tenant lead-request workflow
LEAD_REQUEST_STATUSES = ("pending", "approved", "rejected", "fulfilled")


class LeadSource(Base):
    __tablename__ = "lead_sources"
    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUIDType, ForeignKey("tenants.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Lead(Base):
    __tablename__ = "leads"
    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUIDType, ForeignKey("tenants.id"), nullable=False, index=True)
    location_id: Mapped[uuid.UUID | None] = mapped_column(UUIDType, ForeignKey("locations.id"), nullable=True)
    pipeline_id: Mapped[uuid.UUID | None] = mapped_column(
        UUIDType, ForeignKey("crm_pipelines.id", ondelete="SET NULL"), nullable=True, index=True
    )
    stage_id: Mapped[uuid.UUID | None] = mapped_column(
        UUIDType, ForeignKey("crm_stages.id", ondelete="SET NULL"), nullable=True, index=True
    )
    stage_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False, server_default="0")
    assigned_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUIDType, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str | None] = mapped_column(String(100))
    email: Mapped[str | None] = mapped_column(String(255), index=True)
    phone: Mapped[str | None] = mapped_column(String(50))
    message: Mapped[str | None] = mapped_column(Text)
    service_needed: Mapped[str | None] = mapped_column(String(200))
    postcode: Mapped[str | None] = mapped_column(String(20))
    source: Mapped[str] = mapped_column(String(100), default="web_form")
    utm_source: Mapped[str | None] = mapped_column(String(100))
    utm_medium: Mapped[str | None] = mapped_column(String(100))
    utm_campaign: Mapped[str | None] = mapped_column(String(100))
    ip_address: Mapped[str | None] = mapped_column(String(45))
    referrer_url: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(30), default="new")
    is_spam: Mapped[bool] = mapped_column(Boolean, default=False)
    tags: Mapped[list] = mapped_column(JSONBType, default=list)
    extra_data: Mapped[dict] = mapped_column(JSONBType, default=dict)
    # AI lead scoring (Phase 2). NULL = not scored yet. Range 0-100.
    score: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    score_label: Mapped[str | None] = mapped_column(String(20))  # cold | warm | hot | unqualified
    score_reason: Mapped[str | None] = mapped_column(Text)
    scored_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    converted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class LeadRequest(Base):
    """A tenant's request for the platform to source a batch of AI-scraped leads."""
    __tablename__ = "lead_requests"

    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUIDType, ForeignKey("tenants.id"), nullable=False, index=True)
    # YYYY-MM string so we can enforce one request per month easily
    month_year: Mapped[str] = mapped_column(String(7), nullable=False)
    requested_count: Mapped[int] = mapped_column(Integer, nullable=False)
    approved_count: Mapped[int] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)
    tenant_notes: Mapped[str | None] = mapped_column(Text)
    admin_notes: Mapped[str | None] = mapped_column(Text)
    fulfilled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
