from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field


class AccountingStatusResponse(BaseModel):
    has_accounting: bool
    feature_code: str = "accounting"
    status: str | None = None
    expires_at: datetime | None = None


class AccountingCheckoutRequest(BaseModel):
    success_url: str
    cancel_url: str


class AccountingCheckoutResponse(BaseModel):
    checkout_url: str


class AccountingSettingsResponse(BaseModel):
    vat_scheme: str
    flat_rate_percent: int | None
    late_fee_enabled: bool
    late_fee_percent: int
    auto_invoice_on_booking_complete: bool
    reminder_days: list[int]


class AccountingSettingsUpdate(BaseModel):
    vat_scheme: str | None = None
    flat_rate_percent: int | None = None
    late_fee_enabled: bool | None = None
    late_fee_percent: int | None = None
    auto_invoice_on_booking_complete: bool | None = None
    reminder_days: list[int] | None = None


class ExpenseCreate(BaseModel):
    description: str
    amount_pence: int = Field(ge=0)
    vat_rate: int = Field(default=20, ge=0, le=100)
    category: str = "general"
    expense_date: date
    customer_id: UUID | None = None
    deal_id: UUID | None = None
    booking_id: UUID | None = None
    receipt_url: str | None = None
    notes: str | None = None


class ExpenseResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: UUID
    tenant_id: UUID
    description: str
    amount_pence: int
    vat_rate: int
    vat_pence: int
    category: str
    expense_date: date
    customer_id: UUID | None
    deal_id: UUID | None
    booking_id: UUID | None
    receipt_url: str | None
    notes: str | None
    created_at: datetime


class ExpenseListResponse(BaseModel):
    items: list[ExpenseResponse]
    total: int


class RecurringLineItem(BaseModel):
    description: str
    quantity: int = 1
    unit_price_pence: int
    vat_rate: int = 20


class RecurringScheduleCreate(BaseModel):
    customer_id: UUID
    title: str
    notes: str | None = None
    deal_id: UUID | None = None
    interval_unit: str = "monthly"
    interval_count: int = 1
    next_run_at: date
    line_items: list[RecurringLineItem]
    auto_charge: bool = False
    auto_send: bool = True


class RecurringScheduleResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: UUID
    tenant_id: UUID
    customer_id: UUID
    deal_id: UUID | None
    title: str
    notes: str | None
    interval_unit: str
    interval_count: int
    next_run_at: date
    line_items: list
    auto_charge: bool
    auto_send: bool
    is_active: bool
    created_at: datetime


class RecurringScheduleListResponse(BaseModel):
    items: list[RecurringScheduleResponse]
    total: int


class TaxSummaryResponse(BaseModel):
    year: int
    income_pence: int
    expenses_pence: int
    vat_collected_pence: int
    vat_on_expenses_pence: int
    net_pence: int
    vat_scheme: str


class CustomerFinancialsResponse(BaseModel):
    customer_id: UUID
    outstanding_pence: int
    lifetime_paid_pence: int
    invoice_count: int
    invoices: list[dict]
    payments: list[dict]


class AdminAddonAction(BaseModel):
    action: str  # grant | revoke
    expires_at: datetime | None = None
