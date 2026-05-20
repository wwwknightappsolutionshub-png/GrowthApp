from datetime import datetime
from uuid import UUID
from typing import Literal
from pydantic import BaseModel, EmailStr, Field


class LeadCreate(BaseModel):
    first_name: str
    last_name: str | None = None
    email: EmailStr | None = None
    phone: str | None = None
    message: str | None = None
    service_needed: str | None = None
    postcode: str | None = None
    source: str = "web_form"
    utm_source: str | None = None
    utm_medium: str | None = None
    utm_campaign: str | None = None
    location_id: UUID | None = None


class LeadUpdate(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    email: EmailStr | None = None
    phone: str | None = None
    message: str | None = None
    service_needed: str | None = None
    status: str | None = None
    is_spam: bool | None = None
    tags: list[str] | None = None


class LeadResponse(BaseModel):
    model_config = {"from_attributes": True}
    id: UUID
    tenant_id: UUID
    first_name: str
    last_name: str | None
    email: str | None
    phone: str | None
    message: str | None
    service_needed: str | None
    postcode: str | None
    source: str
    status: str
    is_spam: bool
    tags: list
    score: int | None = None
    score_label: str | None = None
    score_reason: str | None = None
    scored_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class LeadListResponse(BaseModel):
    items: list[LeadResponse]
    total: int
    page: int
    page_size: int


# ── Lead Requests ────────────────────────────────────────────────────────────

class LeadRequestCreate(BaseModel):
    requested_count: int = Field(ge=1, le=500)
    tenant_notes: str | None = None


class LeadRequestAdminAction(BaseModel):
    approved_count: int | None = Field(default=None, ge=0)
    admin_notes: str | None = None


class LeadRequestResponse(BaseModel):
    model_config = {"from_attributes": True}
    id: UUID
    tenant_id: UUID
    month_year: str
    requested_count: int
    approved_count: int | None = None
    status: str
    tenant_notes: str | None = None
    admin_notes: str | None = None
    fulfilled_at: datetime | None = None
    created_at: datetime
    updated_at: datetime | None = None


class TrialLeadStatusResponse(BaseModel):
    in_trial: bool
    trial_days_total: int
    trial_day: int
    trial_ends_at: str
    leads_per_day: int
    delivered_today: int
    remaining_today: int
    total_delivered: int
    reminder_sent: bool


class LeadSourceCatalogItem(BaseModel):
    id: str | None = None
    name: str
    url_pattern: str
    scraping_type: str
    source_platform: str
    postcode_prefix: str | None = None
    region_label: str | None = None
    is_catalog_default: bool = True
    notes: str | None = None


class LeadSourceCatalogResponse(BaseModel):
    business_type: str
    trade_label: str
    postcode: str
    sources: list[LeadSourceCatalogItem]


class LeadQuotaResponse(BaseModel):
    month_year: str
    plan_quota: int
    requests_this_month: int
    remaining: int
    current_request: LeadRequestResponse | None = None
