import uuid
from datetime import datetime
from decimal import Decimal
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from app.core.db_types import UUIDType, JSONBType


class SubscriptionPlan(Base):
    __tablename__ = "subscription_plans"

    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    price_gbp_monthly: Mapped[int] = mapped_column(Integer, nullable=False)
    stripe_price_id: Mapped[str | None] = mapped_column(String(255))
    max_locations: Mapped[int] = mapped_column(Integer, default=1)
    max_leads_per_month: Mapped[int] = mapped_column(Integer, default=500)
    max_sms_per_month: Mapped[int] = mapped_column(Integer, default=1000)
    max_users: Mapped[int] = mapped_column(Integer, default=1)
    has_social_posting: Mapped[bool] = mapped_column(Boolean, default=False)
    has_ai_content: Mapped[bool] = mapped_column(Boolean, default=False)
    has_white_label: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, server_default="1")
    # Number of AI-sourced lead requests a tenant may submit per calendar month.
    # 0 = not included in this plan.
    ai_lead_requests_per_month: Mapped[int] = mapped_column(Integer, default=0, nullable=False, server_default="0")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Subscription(Base):
    __tablename__ = "subscriptions"

    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUIDType, ForeignKey("tenants.id"), unique=True, nullable=False)
    plan_id: Mapped[uuid.UUID] = mapped_column(UUIDType, ForeignKey("subscription_plans.id"), nullable=False)
    stripe_customer_id: Mapped[str | None] = mapped_column(String(255))
    stripe_subscription_id: Mapped[str | None] = mapped_column(String(255), index=True)
    status: Mapped[str] = mapped_column(String(50), default="trialing")
    current_period_start: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    current_period_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    cancel_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    plan: Mapped["SubscriptionPlan"] = relationship("SubscriptionPlan")


class BillingInvoice(Base):
    __tablename__ = "billing_invoices"

    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUIDType, ForeignKey("tenants.id"), nullable=False)
    stripe_invoice_id: Mapped[str | None] = mapped_column(String(255), unique=True)
    amount_pence: Mapped[int] = mapped_column(Integer, nullable=False)
    currency: Mapped[str] = mapped_column(String(10), default="gbp")
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    invoice_pdf_url: Mapped[str | None] = mapped_column(Text)
    period_start: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    period_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class FreelancerBilling(Base):
    """Subscription price snapshot generated at freelancer signup.

    Pricing logic is tiered on estimated_client_count:
      1–50    → £50
      51–100  → £40
      >100    → £40 + ((count - 100) * £5)
    """

    __tablename__ = "freelancer_billings"

    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUIDType, ForeignKey("users.id"), nullable=False, unique=True)
    estimated_client_count: Mapped[int] = mapped_column(Integer, nullable=False)
    calculated_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    override_price: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    calculation_source: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default="auto", default="auto"
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
