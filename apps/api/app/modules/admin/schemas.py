"""Pydantic schemas for the super-admin API."""
from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class PlatformStats(BaseModel):
    total_tenants: int
    active_tenants: int
    suspended_tenants: int
    total_users: int
    total_leads: int
    total_deals: int
    total_invoices: int
    paid_invoices_pence: int
    open_invoices_pence: int
    mrr_pence: int
    new_tenants_30d: int


class TenantSummary(BaseModel):
    id: uuid.UUID
    slug: str
    name: str
    business_type: str
    city: str | None = None
    postcode: str
    plan_name: str | None = None
    plan_price_pence: int = 0
    subscription_status: str | None = None
    is_active: bool
    onboarding_completed: bool
    member_count: int = 0
    lead_count: int = 0
    deal_count: int = 0
    invoice_total_pence: int = 0
    created_at: datetime
    trial_ends_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class AdminUserSummary(BaseModel):
    id: uuid.UUID
    email: str
    full_name: str
    user_type: str = "tenant"
    is_superadmin: bool
    totp_enabled: bool
    email_verified_at: datetime | None = None
    created_at: datetime
    tenant_count: int = 0

    model_config = ConfigDict(from_attributes=True)


class DeleteResponse(BaseModel):
    id: uuid.UUID
    message: str


class TenantToggleResponse(BaseModel):
    id: uuid.UUID
    is_active: bool
    message: str


class TenantHealthMetricsOut(BaseModel):
    missed_leads: int
    missed_messages: int
    missed_calls: int
    missed_reviews: int
    missed_bookings: int
    overdue_invoices: int


class TenantHealthRow(BaseModel):
    tenant_id: uuid.UUID
    name: str
    slug: str
    email: str | None = None
    is_active: bool
    metrics: TenantHealthMetricsOut
    flags: list[str]
    severity: str


class RemindTenantResponse(BaseModel):
    notification_id: str
    owners_emailed: int
    flags: list[str]
