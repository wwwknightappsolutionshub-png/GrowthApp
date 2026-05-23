"""Membership & Rewards SQLAlchemy models (parallel to industry salon memberships)."""

from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    PrimaryKeyConstraint,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.db_types import JSONBType, UUIDType


class MrTenantSettings(Base):
    __tablename__ = "mr_tenant_settings"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("tenants.id", ondelete="CASCADE"), primary_key=True
    )
    earn_rules: Mapped[dict] = mapped_column(JSONBType, default=dict)
    points_expire_days: Mapped[int | None] = mapped_column(Integer)
    landing_slug: Mapped[str] = mapped_column(String(80), default="memberships")
    landing_published: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class MrMembershipPlan(Base):
    __tablename__ = "mr_membership_plans"

    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    billing_cycle: Mapped[str] = mapped_column(String(20), default="monthly")
    price_pence: Mapped[int] = mapped_column(Integer, default=0)
    included_services: Mapped[list] = mapped_column(JSONBType, default=list)
    discount_percent: Mapped[int] = mapped_column(Integer, default=0)
    rollover_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    rollover_max_periods: Mapped[int] = mapped_column(Integer, default=1)
    cancellation_notice_days: Mapped[int] = mapped_column(Integer, default=30)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    stripe_price_id: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class MrCustomerSubscription(Base):
    __tablename__ = "mr_customer_subscriptions"

    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True
    )
    customer_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("customers.id", ondelete="CASCADE"), nullable=False, index=True
    )
    plan_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("mr_membership_plans.id", ondelete="RESTRICT"), nullable=False
    )
    status: Mapped[str] = mapped_column(String(30), default="active")
    started_at: Mapped[date | None] = mapped_column(Date)
    current_period_end: Mapped[date | None] = mapped_column(Date)
    canceled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    usage_snapshot: Mapped[dict] = mapped_column(JSONBType, default=dict)
    stripe_subscription_id: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class MrLoyaltyTier(Base):
    __tablename__ = "mr_loyalty_tiers"
    __table_args__ = (UniqueConstraint("tenant_id", "code", name="uq_mr_loyalty_tiers_tenant_code"),)

    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True
    )
    code: Mapped[str] = mapped_column(String(30), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    min_points_lifetime: Mapped[int] = mapped_column(Integer, default=0)
    benefits: Mapped[list] = mapped_column(JSONBType, default=list)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class MrCustomerLoyalty(Base):
    __tablename__ = "mr_customer_loyalty"
    __table_args__ = (PrimaryKeyConstraint("tenant_id", "customer_id", name="pk_mr_customer_loyalty"),)

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False
    )
    customer_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("customers.id", ondelete="CASCADE"), nullable=False
    )
    points_balance: Mapped[int] = mapped_column(Integer, default=0)
    points_lifetime: Mapped[int] = mapped_column(Integer, default=0)
    tier_code: Mapped[str] = mapped_column(String(30), default="bronze")
    tier_updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class MrPointsLedger(Base):
    __tablename__ = "mr_points_ledger"

    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True
    )
    customer_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("customers.id", ondelete="CASCADE"), nullable=False, index=True
    )
    amount: Mapped[int] = mapped_column(Integer, nullable=False)
    balance_after: Mapped[int] = mapped_column(Integer, nullable=False)
    source: Mapped[str] = mapped_column(String(50), nullable=False)
    reference_type: Mapped[str | None] = mapped_column(String(50))
    reference_id: Mapped[uuid.UUID | None] = mapped_column(UUIDType)
    description: Mapped[str | None] = mapped_column(String(500))
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class MrRewardCatalog(Base):
    __tablename__ = "mr_reward_catalog"

    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    points_cost: Mapped[int] = mapped_column(Integer, nullable=False)
    reward_type: Mapped[str] = mapped_column(String(30), default="discount")
    config: Mapped[dict] = mapped_column(JSONBType, default=dict)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    stock_remaining: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class MrRewardRedemption(Base):
    __tablename__ = "mr_reward_redemptions"

    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True
    )
    customer_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("customers.id", ondelete="CASCADE"), nullable=False, index=True
    )
    catalog_item_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("mr_reward_catalog.id", ondelete="RESTRICT"), nullable=False
    )
    points_spent: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class MrTrialReminders(Base):
    __tablename__ = "mr_trial_reminders"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("tenants.id", ondelete="CASCADE"), primary_key=True
    )
    trial_started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    trial_ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    day3_email_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    day6_email_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    day6_modal_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    day15_winback_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    converted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    winback_discount_percent: Mapped[int] = mapped_column(Integer, default=50)


class MrLandingConfig(Base):
    __tablename__ = "mr_landing_config"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("tenants.id", ondelete="CASCADE"), primary_key=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    meta_description: Mapped[str | None] = mapped_column(Text)
    hero: Mapped[dict] = mapped_column(JSONBType, default=dict)
    benefits: Mapped[list] = mapped_column(JSONBType, default=list)
    cta_label: Mapped[str] = mapped_column(String(120), default="Join Our Membership Program")
    cta_href: Mapped[str | None] = mapped_column(String(500))
    published: Mapped[bool] = mapped_column(Boolean, default=False)
    auto_generated: Mapped[bool] = mapped_column(Boolean, default=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
