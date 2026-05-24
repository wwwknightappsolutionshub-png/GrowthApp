from __future__ import annotations

import uuid
from datetime import date, datetime

from pydantic import BaseModel, Field


class TrialReminderState(BaseModel):
    day3_email_at: str | None = None
    day6_email_at: str | None = None
    day6_modal_at: str | None = None
    day15_winback_at: str | None = None


class TrialStatusResponse(BaseModel):
    on_trial: bool
    trial_expired: bool
    converted: bool
    days_remaining: int
    trial_ends_at: str | None = None
    trial_started_at: str | None = None
    show_urgency_modal: bool
    show_winback_banner: bool
    winback_discount_percent: int
    upgrade_url: str
    setup_url: str
    reminders: TrialReminderState | dict = Field(default_factory=dict)


class MembershipStatusResponse(BaseModel):
    has_membership_rewards: bool
    feature_code: str
    status: str | None = None
    expires_at: datetime | None = None
    trial_ends_at: datetime | None = None
    landing_url: str | None = None
    trial: TrialStatusResponse | None = None
    stripe_configured: bool = False
    is_trial: bool = False
    is_paid: bool = False
    billing_source: str | None = None


class EarnRulesUpdate(BaseModel):
    earn_rules: dict = Field(default_factory=dict)
    points_expire_days: int | None = None


class SettingsResponse(BaseModel):
    tenant_id: uuid.UUID
    earn_rules: dict
    points_expire_days: int | None
    landing_slug: str
    landing_published: bool


class PlanCreate(BaseModel):
    name: str
    description: str | None = None
    billing_cycle: str = "monthly"
    price_pence: int = 0
    included_services: list = Field(default_factory=list)
    discount_percent: int = 0
    rollover_enabled: bool = False
    rollover_max_periods: int = 1
    cancellation_notice_days: int = 30
    is_active: bool = True
    sort_order: int = 0


class PlanUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    billing_cycle: str | None = None
    price_pence: int | None = None
    included_services: list | None = None
    discount_percent: int | None = None
    rollover_enabled: bool | None = None
    rollover_max_periods: int | None = None
    cancellation_notice_days: int | None = None
    is_active: bool | None = None
    sort_order: int | None = None


class PlanResponse(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    name: str
    description: str | None
    billing_cycle: str
    price_pence: int
    included_services: list
    discount_percent: int
    rollover_enabled: bool
    rollover_max_periods: int
    cancellation_notice_days: int
    is_active: bool
    sort_order: int

    model_config = {"from_attributes": True}


class PlanListResponse(BaseModel):
    items: list[PlanResponse]


class TierResponse(BaseModel):
    id: uuid.UUID
    code: str
    name: str
    min_points_lifetime: int
    benefits: list
    sort_order: int

    model_config = {"from_attributes": True}


class TierUpdate(BaseModel):
    name: str | None = None
    min_points_lifetime: int | None = None
    benefits: list | None = None
    sort_order: int | None = None


class TierListResponse(BaseModel):
    items: list[TierResponse]


class CatalogItemCreate(BaseModel):
    name: str
    description: str | None = None
    points_cost: int
    reward_type: str = "discount"
    config: dict = Field(default_factory=dict)
    is_active: bool = True
    stock_remaining: int | None = None


class CatalogItemUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    points_cost: int | None = None
    reward_type: str | None = None
    config: dict | None = None
    is_active: bool | None = None
    stock_remaining: int | None = None


class CatalogItemResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None
    points_cost: int
    reward_type: str
    config: dict
    is_active: bool
    stock_remaining: int | None

    model_config = {"from_attributes": True}


class CatalogListResponse(BaseModel):
    items: list[CatalogItemResponse]


class PointsAdjustRequest(BaseModel):
    customer_id: uuid.UUID
    amount: int
    source: str = "adjustment"
    description: str | None = None


class PointsLedgerEntry(BaseModel):
    id: uuid.UUID
    amount: int
    balance_after: int
    source: str
    description: str | None
    created_at: datetime
    expires_at: datetime | None = None

    model_config = {"from_attributes": True}


class CustomerLoyaltyResponse(BaseModel):
    customer_id: uuid.UUID
    points_balance: int
    points_lifetime: int
    tier_code: str


class LandingConfigUpdate(BaseModel):
    title: str | None = None
    meta_description: str | None = None
    hero: dict | None = None
    benefits: list | None = None
    cta_label: str | None = None
    cta_href: str | None = None
    published: bool | None = None


class TierSummary(BaseModel):
    code: str
    name: str
    min_points_lifetime: int
    benefits: list = Field(default_factory=list)


class LandingConfigResponse(BaseModel):
    title: str
    meta_description: str | None
    hero: dict
    benefits: list
    cta_label: str
    cta_href: str | None
    published: bool
    auto_generated: bool = True
    public_url: str | None = None
    preview_path: str | None = None
    booking_cta_url: str | None = None
    plans: list[PlanResponse] = Field(default_factory=list)
    tiers: list[TierSummary] = Field(default_factory=list)


class MembershipInterestRequest(BaseModel):
    first_name: str
    last_name: str | None = None
    email: str | None = None
    phone: str | None = None
    message: str | None = None
    plan_id: uuid.UUID | None = None


class LoyaltyEnrollRequest(BaseModel):
    name: str
    email: str
    phone: str | None = None
    tier_code: str


class LoyaltyEnrollResponse(BaseModel):
    message: str
    tier_code: str
    tier_name: str
    signup_bonus_points: int
    points_balance: int
    portal_account_created: bool = False
    rewards_email_sent: bool = False


class CheckoutRequest(BaseModel):
    success_url: str
    cancel_url: str


class CheckoutResponse(BaseModel):
    checkout_url: str


class SubscriptionCreate(BaseModel):
    customer_id: uuid.UUID
    plan_id: uuid.UUID
    started_at: date | None = None


class SubscriptionResponse(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    customer_id: uuid.UUID
    plan_id: uuid.UUID
    status: str
    started_at: date | None
    current_period_end: date | None
    canceled_at: datetime | None

    model_config = {"from_attributes": True}


class SubscriptionListResponse(BaseModel):
    items: list[SubscriptionResponse]


class DashboardResponse(BaseModel):
    active_subscriptions: int
    members_with_points: int
    points_issued_lifetime: int
    redemptions_count: int
    active_plans: int
    landing_published: bool


class LoyaltyLeaderboardEntry(BaseModel):
    customer_id: str
    customer_name: str | None
    points_balance: int
    points_lifetime: int
    tier_code: str


class LoyaltyLeaderboardResponse(BaseModel):
    items: list[LoyaltyLeaderboardEntry]


class AnalyticsRedemptionEntry(BaseModel):
    id: str
    customer_id: str
    customer_name: str | None
    reward_name: str
    points_spent: int
    status: str
    created_at: str | None


class AnalyticsResponse(BaseModel):
    points_by_source: dict[str, int]
    tier_distribution: dict[str, int]
    members_total: int
    members_with_balance: int
    redemptions_total: int
    redemptions_30d: int
    redemption_rate_percent: float
    points_issued_30d: int
    points_redeemed_30d: int
    expiring_points_soon: int
    top_customers: list[LoyaltyLeaderboardEntry]
    recent_redemptions: list[AnalyticsRedemptionEntry]


class LoyaltyCustomerEntry(BaseModel):
    customer_id: str
    customer_name: str | None
    email: str | None
    phone: str | None
    points_balance: int
    points_lifetime: int
    tier_code: str


class LoyaltyCustomerListResponse(BaseModel):
    items: list[LoyaltyCustomerEntry]
    total: int
    limit: int
    offset: int


class RedemptionListResponse(BaseModel):
    items: list[AnalyticsRedemptionEntry]


# ── Customer portal (Phase 4) ─────────────────────────────────────────────────


class MessageResponse(BaseModel):
    message: str


class MagicLinkRequest(BaseModel):
    email: str
    tenant_slug: str
    next_path: str | None = None


class MagicLinkVerifyRequest(BaseModel):
    token: str
    tenant_slug: str


class PortalLoginRequest(BaseModel):
    email: str
    password: str
    tenant_slug: str


class PortalSetPasswordRequest(BaseModel):
    new_password: str = Field(min_length=8)


class PortalAuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    customer_id: str
    must_change_password: bool | None = None


class LoyaltyBrandingResponse(BaseModel):
    tenant_slug: str
    tenant_name: str
    logo_url: str | None = None
    primary_color: str
    rewards_portal_url: str
    loyalty_enabled: bool


class CustomerPortalMeResponse(BaseModel):
    customer_id: uuid.UUID
    first_name: str
    last_name: str | None = None
    email: str | None = None
    phone: str | None = None
    points_balance: int
    points_lifetime: int
    points_earned: int = 0
    points_redeemed: int = 0
    points_expiring_soon: int = 0
    pending_redemptions: int = 0
    tier_code: str
    tier_name: str
    tier_benefits: list = Field(default_factory=list)
    next_tier_code: str | None = None
    next_tier_name: str | None = None
    points_to_next_tier: int = 0
    tier_progress_percent: int = 0
    must_change_password: bool = False
    push_notifications_enabled: bool = False
    date_of_birth: date | None = None
    marketing_email: bool = True
    marketing_sms: bool = False
    birthday_participation: bool = True
    expiring_points_reminders: bool = True
    tenant_slug: str
    tenant_name: str


class PortalPreferencesUpdate(BaseModel):
    date_of_birth: date | None = None
    marketing_email: bool | None = None
    marketing_sms: bool | None = None
    birthday_participation: bool | None = None
    expiring_points_reminders: bool | None = None


class PortalPreferencesResponse(BaseModel):
    date_of_birth: date | None = None
    marketing_email: bool
    marketing_sms: bool
    birthday_participation: bool
    expiring_points_reminders: bool


class CustomerPortalRedeemResponse(BaseModel):
    id: uuid.UUID
    status: str
    points_spent: int
    reward_name: str | None = None
    fulfillment_code: str | None = None
    code_expires_at: datetime | None = None


class PortalPendingRedemption(BaseModel):
    id: uuid.UUID
    reward_name: str
    points_spent: int
    fulfillment_code: str
    code_expires_at: datetime | None = None
    status: str


class PortalPendingRedemptionsResponse(BaseModel):
    items: list[PortalPendingRedemption]


class PortalHistoryResponse(BaseModel):
    items: list[PointsLedgerEntry]
    limit: int
    offset: int
    has_more: bool


class PortalQrResponse(BaseModel):
    token: str
    expires_at: str
    qr_data_url: str
    payload: str


class PushSubscribeKeys(BaseModel):
    p256dh: str
    auth: str


class PushSubscribeRequest(BaseModel):
    endpoint: str
    keys: PushSubscribeKeys


class PushSubscribeResponse(BaseModel):
    id: uuid.UUID
    endpoint: str


class QrScanRequest(BaseModel):
    payload: str = Field(min_length=8)


class QrScanResponse(BaseModel):
    scan_id: uuid.UUID
    customer_id: uuid.UUID
    customer_name: str | None
    points_awarded: int
    points_balance: int
    tier_code: str
    message: str


class RedemptionFulfillRequest(BaseModel):
    fulfillment_code: str = Field(min_length=4, max_length=16)


class RedemptionFulfillResponse(BaseModel):
    id: uuid.UUID
    status: str
    reward_name: str | None = None
    customer_name: str | None = None
    points_spent: int
    message: str


class PortalSubscriptionSummary(BaseModel):
    plan_id: str
    plan_name: str
    plan_description: str | None = None
    billing_cycle: str
    price_pence: int
    discount_percent: int = 0
    benefits: list[str] = Field(default_factory=list)
    status: str
    current_period_end: str | None = None


class PortalTargetedOffer(BaseModel):
    type: str
    title: str
    body: str
    cta_label: str
    cta_url: str


class PortalUpsellResponse(BaseModel):
    memberships_url: str
    refer_win_url: str
    booking_url: str
    google_review_url: str | None = None
    google_review_available: bool = False
    has_membership_plans: bool = False
    active_subscription: PortalSubscriptionSummary | None = None
    targeted_offers: list[PortalTargetedOffer] = Field(default_factory=list)
    affordable_rewards_count: int = 0


class CustomerBroadcastRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=120)
    body: str = Field(..., min_length=1, max_length=2000)
    send_push: bool = True
    send_email: bool = False
    path: str = "dashboard"


class CustomerBroadcastPreviewResponse(BaseModel):
    customers: int
    push_subscribers: int
    email_opted_in: int


class CustomerBroadcastResponse(BaseModel):
    customers: int
    push_sent: int
    in_app_sent: int = 0
    email_sent: int


class CustomerNotificationResponse(BaseModel):
    id: uuid.UUID
    kind: str
    title: str
    body: str | None = None
    link: str | None = None
    read_at: datetime | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class CustomerNotificationListResponse(BaseModel):
    items: list[CustomerNotificationResponse]
    unread: int
    limit: int
    offset: int
