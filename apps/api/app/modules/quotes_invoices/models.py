import uuid
from datetime import datetime, date
from sqlalchemy import DateTime, ForeignKey, String, Text, Boolean, Integer, Date, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from app.core.db_types import UUIDType, JSONBType


class QuoteTemplate(Base):
    __tablename__ = "quote_templates"
    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUIDType, ForeignKey("tenants.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    items: Mapped[list] = mapped_column(JSONBType, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Quote(Base):
    __tablename__ = "quotes"
    __table_args__ = (UniqueConstraint("tenant_id", "quote_number", name="uq_quotes_tenant_number"),)
    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUIDType, ForeignKey("tenants.id"), nullable=False, index=True)
    deal_id: Mapped[uuid.UUID | None] = mapped_column(UUIDType, ForeignKey("deals.id"), nullable=True)
    customer_id: Mapped[uuid.UUID] = mapped_column(UUIDType, ForeignKey("customers.id"), nullable=False)
    quote_number: Mapped[str] = mapped_column(String(50), nullable=False)
    public_token: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(30), default="draft")
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)
    valid_until: Mapped[date | None] = mapped_column(Date)
    subtotal_pence: Mapped[int] = mapped_column(Integer, default=0)
    vat_pence: Mapped[int] = mapped_column(Integer, default=0)
    total_pence: Mapped[int] = mapped_column(Integer, default=0)
    accepted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    declined_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    viewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    items: Mapped[list["QuoteItem"]] = relationship("QuoteItem", back_populates="quote", cascade="all, delete-orphan")


class QuoteItem(Base):
    __tablename__ = "quote_items"
    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)
    quote_id: Mapped[uuid.UUID] = mapped_column(UUIDType, ForeignKey("quotes.id", ondelete="CASCADE"), nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, default=1)
    unit_price_pence: Mapped[int] = mapped_column(Integer, nullable=False)
    vat_rate: Mapped[int] = mapped_column(Integer, default=20)
    line_total_pence: Mapped[int] = mapped_column(Integer, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    quote: Mapped["Quote"] = relationship("Quote", back_populates="items")


class Invoice(Base):
    __tablename__ = "invoices"
    __table_args__ = (UniqueConstraint("tenant_id", "invoice_number", name="uq_invoices_tenant_number"),)
    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUIDType, ForeignKey("tenants.id"), nullable=False, index=True)
    quote_id: Mapped[uuid.UUID | None] = mapped_column(UUIDType, ForeignKey("quotes.id"), nullable=True)
    deal_id: Mapped[uuid.UUID | None] = mapped_column(UUIDType, ForeignKey("deals.id"), nullable=True)
    booking_id: Mapped[uuid.UUID | None] = mapped_column(UUIDType, ForeignKey("bookings.id", ondelete="SET NULL"), nullable=True)
    customer_id: Mapped[uuid.UUID] = mapped_column(UUIDType, ForeignKey("customers.id"), nullable=False)
    invoice_number: Mapped[str] = mapped_column(String(50), nullable=False)
    public_token: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="draft")
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)
    due_date: Mapped[date | None] = mapped_column(Date)
    subtotal_pence: Mapped[int] = mapped_column(Integer, default=0)
    vat_pence: Mapped[int] = mapped_column(Integer, default=0)
    total_pence: Mapped[int] = mapped_column(Integer, default=0)
    paid_pence: Mapped[int] = mapped_column(Integer, default=0)
    stripe_payment_link: Mapped[str | None] = mapped_column(Text)
    currency: Mapped[str] = mapped_column(String(10), default="gbp")
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    viewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_reminder_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    payment_channel: Mapped[str | None] = mapped_column(String(30), nullable=True)
    recurrency: Mapped[str | None] = mapped_column(String(30), nullable=True)
    renewal_due_date: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)
    renewal_reminder_sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    items: Mapped[list["InvoiceItem"]] = relationship("InvoiceItem", back_populates="invoice", cascade="all, delete-orphan")


class InvoiceItem(Base):
    __tablename__ = "invoice_items"
    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)
    invoice_id: Mapped[uuid.UUID] = mapped_column(UUIDType, ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, default=1)
    unit_price_pence: Mapped[int] = mapped_column(Integer, nullable=False)
    vat_rate: Mapped[int] = mapped_column(Integer, default=20)
    line_total_pence: Mapped[int] = mapped_column(Integer, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    line_kind: Mapped[str] = mapped_column(String(20), default="service", server_default="service")
    invoice: Mapped["Invoice"] = relationship("Invoice", back_populates="items")


class Payment(Base):
    __tablename__ = "payments"
    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUIDType, ForeignKey("tenants.id"), nullable=False)
    invoice_id: Mapped[uuid.UUID] = mapped_column(UUIDType, ForeignKey("invoices.id"), nullable=False)
    amount_pence: Mapped[int] = mapped_column(Integer, nullable=False)
    method: Mapped[str] = mapped_column(String(50), default="stripe")
    stripe_payment_intent_id: Mapped[str | None] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(30), default="succeeded")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
