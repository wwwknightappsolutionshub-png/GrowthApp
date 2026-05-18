from datetime import datetime
from uuid import UUID
from pydantic import BaseModel


class PlanResponse(BaseModel):
    model_config = {"from_attributes": True}
    id: UUID
    name: str
    price_gbp_monthly: int
    max_locations: int
    max_leads_per_month: int
    max_sms_per_month: int
    max_users: int
    has_social_posting: bool
    has_ai_content: bool
    has_white_label: bool


class SubscriptionResponse(BaseModel):
    model_config = {"from_attributes": True}
    id: UUID
    tenant_id: UUID
    plan_id: UUID
    status: str
    current_period_start: datetime | None
    current_period_end: datetime | None
    cancel_at: datetime | None
    plan: PlanResponse


class BillingInvoiceResponse(BaseModel):
    model_config = {"from_attributes": True}
    id: UUID
    amount_pence: int
    currency: str
    status: str
    invoice_pdf_url: str | None
    period_start: datetime | None
    period_end: datetime | None
    created_at: datetime


class CheckoutRequest(BaseModel):
    plan_id: UUID
    success_url: str
    cancel_url: str


class CheckoutResponse(BaseModel):
    checkout_url: str


class PortalResponse(BaseModel):
    portal_url: str
