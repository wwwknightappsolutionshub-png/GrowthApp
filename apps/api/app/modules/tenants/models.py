from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db_types import JSONBType, UUIDType

from app.core.database import Base

if TYPE_CHECKING:
    from app.modules.auth.models import User


class Tenant(Base):
    __tablename__ = "tenants"

    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    business_type: Mapped[str] = mapped_column(String(100), nullable=False)
    logo_url: Mapped[str | None] = mapped_column(Text)
    primary_color: Mapped[str] = mapped_column(String(20), default="#2563EB")
    website_url: Mapped[str | None] = mapped_column(Text)
    phone: Mapped[str | None] = mapped_column(String(50))
    email: Mapped[str | None] = mapped_column(String(255))
    address: Mapped[str | None] = mapped_column(Text)
    city: Mapped[str | None] = mapped_column(String(100))
    postcode: Mapped[str] = mapped_column(String(20), nullable=False)
    country: Mapped[str] = mapped_column(String(10), default="GB")
    google_place_id: Mapped[str | None] = mapped_column(Text)
    google_review_url: Mapped[str | None] = mapped_column(Text)
    timezone: Mapped[str] = mapped_column(String(50), default="Europe/London")
    plan_id: Mapped[uuid.UUID | None] = mapped_column(UUIDType, ForeignKey("subscription_plans.id"), nullable=True)
    trial_ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    onboarding_completed: Mapped[bool] = mapped_column(Boolean, default=False)
    # Atomic per-tenant counters used for quote/invoice numbering.
    last_quote_number: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    last_invoice_number: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    # When a tenant is a freelancer-managed "shadow client", this points at the
    # freelancer User who owns it. Regular tenants leave this NULL.
    owner_user_id: Mapped[uuid.UUID | None] = mapped_column(UUIDType, ForeignKey("users.id"), nullable=True, index=True)
    is_managed_client: Mapped[bool] = mapped_column(Boolean, default=False, server_default="0", nullable=False)
    trial_reminder_sent_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    primary_landing_page_id: Mapped[uuid.UUID | None] = mapped_column(
        UUIDType, ForeignKey("landing_pages.id", ondelete="SET NULL"), nullable=True
    )
    business_site_published: Mapped[bool] = mapped_column(Boolean, default=False, server_default="0")
    business_site_published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    # Social media handles per managed client (used by the freelancer dashboard).
    social_handles: Mapped[dict] = mapped_column(JSONBType, default=dict, nullable=False, server_default="{}")
    integrations_onboarding: Mapped[dict] = mapped_column(JSONBType, default=dict, nullable=False, server_default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    members: Mapped[list["TenantMember"]] = relationship("TenantMember", back_populates="tenant", cascade="all, delete-orphan")
    locations: Mapped[list["Location"]] = relationship("Location", back_populates="tenant", cascade="all, delete-orphan")


class TenantMember(Base):
    __tablename__ = "tenant_members"

    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUIDType, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(UUIDType, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    invited_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    joined_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="members")
    user: Mapped["User"] = relationship("User", back_populates="tenant_memberships")


class Location(Base):
    __tablename__ = "locations"

    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUIDType, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    slug: Mapped[str] = mapped_column(String(100), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    address: Mapped[str | None] = mapped_column(Text)
    city: Mapped[str | None] = mapped_column(String(100))
    postcode: Mapped[str | None] = mapped_column(String(20))
    phone: Mapped[str | None] = mapped_column(String(50))
    email: Mapped[str | None] = mapped_column(String(255))
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="locations")
