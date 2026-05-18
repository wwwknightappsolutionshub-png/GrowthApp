"""Lead Marketplace ORM models.

Tables (exact per spec):
    lead_categories
    lead_quality_rules
    lead_pricing
    lead_territories
    lead_marketplace
    lead_assignment_rules
"""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.db_types import UUIDType


# Enums (stored as VARCHAR for SQLite / PostgreSQL compat)
EXCLUSIVITY_OPTIONS = ("shared", "semi-exclusive", "exclusive")
MARKETPLACE_STATUSES = ("available", "reserved", "sold", "expired")


class LeadCategory(Base):
    __tablename__ = "lead_categories"

    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(200), nullable=False, unique=True, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class LeadQualityRule(Base):
    __tablename__ = "lead_quality_rules"

    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    min_ai_score: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    max_age_days: Mapped[int] = mapped_column(Integer, nullable=False, default=30)
    requires_phone: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    requires_email: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    apply_to_category: Mapped[uuid.UUID | None] = mapped_column(
        UUIDType,
        ForeignKey("lead_categories.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class LeadPricing(Base):
    __tablename__ = "lead_pricing"

    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)
    category_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType,
        ForeignKey("lead_categories.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    base_price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    high_quality_multiplier: Mapped[float] = mapped_column(Numeric(6, 3), nullable=False, default=1.0)
    exclusive_multiplier: Mapped[float] = mapped_column(Numeric(6, 3), nullable=False, default=1.0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class LeadTerritory(Base):
    __tablename__ = "lead_territories"

    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    region_code: Mapped[str] = mapped_column(String(20), nullable=False)
    country: Mapped[str] = mapped_column(String(10), nullable=False, default="GB")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class LeadMarketplace(Base):
    __tablename__ = "lead_marketplace"

    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)
    lead_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType,
        ForeignKey("leads.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    category_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType,
        ForeignKey("lead_categories.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    territory_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType,
        ForeignKey("lead_territories.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    ai_score: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False, default=0)
    exclusivity: Mapped[str] = mapped_column(String(20), nullable=False, default="shared")
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="available", index=True)
    # When reserved/sold — which tenant
    assigned_tenant_id: Mapped[uuid.UUID | None] = mapped_column(
        UUIDType,
        ForeignKey("tenants.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class LeadAssignmentRule(Base):
    __tablename__ = "lead_assignment_rules"

    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)
    rule_name: Mapped[str] = mapped_column(String(200), nullable=False)
    category_id: Mapped[uuid.UUID | None] = mapped_column(
        UUIDType,
        ForeignKey("lead_categories.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    territory_id: Mapped[uuid.UUID | None] = mapped_column(
        UUIDType,
        ForeignKey("lead_territories.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    min_subscription_level: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    priority_weight: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
