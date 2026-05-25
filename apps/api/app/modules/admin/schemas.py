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


class IntegrationsOnboardingOut(BaseModel):
    google_connected: bool = False
    social_connected: bool = False
    skipped: bool = False


class SocialChannelSummary(BaseModel):
    channel_type: str
    status: str
    connected_at: datetime | None = None
    last_webhook_at: datetime | None = None


class TenantGoogleSummary(BaseModel):
    platform_connected: bool
    platform_location_title: str | None = None
    platform_last_sync_at: datetime | None = None
    credentials_registered: bool
    credentials_status: str | None = None
    credentials_expires_at: datetime | None = None
    review_count: int = 0
    last_sync_at: datetime | None = None
    last_sync_type: str | None = None
    last_sync_status: str | None = None


class TenantSocialSummary(BaseModel):
    channels_provisioned: int = 0
    channels_connected: int = 0
    platforms: list[SocialChannelSummary] = []
    last_webhook_at: datetime | None = None
    last_webhook_status: str | None = None
    webhook_failures_7d: int = 0


class TenantIntegrationsRow(BaseModel):
    tenant_id: uuid.UUID
    tenant_name: str
    tenant_slug: str
    is_active: bool
    integrations_onboarding: IntegrationsOnboardingOut
    google: TenantGoogleSummary
    social: TenantSocialSummary
    health_flags: list[str]


class IntegrationsOverviewTotals(BaseModel):
    tenants_total: int
    tenants_with_google_platform: int
    tenants_with_google_credentials: int
    tenants_with_any_social_channel: int
    tenants_with_connected_social: int
    onboarding_skipped: int
    google_sync_failures_24h: int
    social_webhook_failures_24h: int


class IntegrationsOverviewResponse(BaseModel):
    totals: IntegrationsOverviewTotals
    tenants: list[TenantIntegrationsRow]
