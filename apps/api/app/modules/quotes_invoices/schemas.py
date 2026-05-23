from datetime import datetime, date
from uuid import UUID
from pydantic import BaseModel


class QuoteItemIn(BaseModel):
    description: str
    quantity: int = 1
    unit_price_pence: int
    vat_rate: int = 20
    sort_order: int = 0


class QuoteItemResponse(QuoteItemIn):
    model_config = {"from_attributes": True}
    id: UUID
    line_total_pence: int


class QuoteCreate(BaseModel):
    customer_id: UUID
    deal_id: UUID | None = None
    title: str
    notes: str | None = None
    valid_until: date | None = None
    items: list[QuoteItemIn] = []


class QuoteUpdate(BaseModel):
    title: str | None = None
    notes: str | None = None
    valid_until: date | None = None
    deal_id: UUID | None = None
    items: list[QuoteItemIn] | None = None


class QuoteResponse(BaseModel):
    model_config = {"from_attributes": True}
    id: UUID
    tenant_id: UUID
    customer_id: UUID
    deal_id: UUID | None
    quote_number: str
    public_token: str
    status: str
    title: str
    notes: str | None
    valid_until: date | None
    subtotal_pence: int
    vat_pence: int
    total_pence: int
    sent_at: datetime | None
    accepted_at: datetime | None
    created_at: datetime
    items: list[QuoteItemResponse] = []


class QuoteListResponse(BaseModel):
    items: list[QuoteResponse]
    total: int


class InvoiceCreate(BaseModel):
    customer_id: UUID
    quote_id: UUID | None = None
    deal_id: UUID | None = None
    title: str
    notes: str | None = None
    due_date: date | None = None
    items: list[QuoteItemIn] = []


class InvoiceUpdate(BaseModel):
    title: str | None = None
    notes: str | None = None
    due_date: date | None = None
    deal_id: UUID | None = None
    items: list[QuoteItemIn] | None = None


class InvoiceResponse(BaseModel):
    model_config = {"from_attributes": True}
    id: UUID
    tenant_id: UUID
    customer_id: UUID
    invoice_number: str
    status: str
    title: str
    subtotal_pence: int
    vat_pence: int
    total_pence: int
    paid_pence: int
    due_date: date | None
    stripe_payment_link: str | None
    sent_at: datetime | None
    paid_at: datetime | None
    created_at: datetime
    items: list[QuoteItemResponse] = []


class InvoiceListResponse(BaseModel):
    items: list[InvoiceResponse]
    total: int
