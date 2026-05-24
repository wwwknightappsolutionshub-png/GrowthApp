from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import CurrentTenantContext, OwnerContext
from app.modules.membership_rewards import service
from app.modules.membership_rewards.entitlement import require_membership_rewards
from app.modules.membership_rewards.schemas import (
    AnalyticsResponse,
    CatalogItemCreate,
    CatalogItemResponse,
    CatalogListResponse,
    CustomerLoyaltyResponse,
    EarnRulesUpdate,
    LandingConfigResponse,
    CheckoutRequest,
    CheckoutResponse,
    DashboardResponse,
    LandingConfigUpdate,
    LoyaltyCustomerListResponse,
    LoyaltyLeaderboardResponse,
    MembershipStatusResponse,
    TrialStatusResponse,
    PlanCreate,
    PlanListResponse,
    PlanResponse,
    PlanUpdate,
    PointsAdjustRequest,
    RedemptionListResponse,
    SubscriptionCreate,
    SubscriptionListResponse,
    SubscriptionResponse,
    PointsLedgerEntry,
    QrScanRequest,
    QrScanResponse,
    RedemptionFulfillRequest,
    RedemptionFulfillResponse,
    SettingsResponse,
    TierListResponse,
    TierResponse,
    TierUpdate,
)

router = APIRouter(prefix="/membership-rewards", tags=["Membership & Rewards"])


@router.post(
    "/qr/scan",
    response_model=QrScanResponse,
    dependencies=[Depends(require_membership_rewards)],
)
async def scan_customer_qr(
    data: QrScanRequest,
    ctx: CurrentTenantContext,
    db: AsyncSession = Depends(get_db),
):
    """Staff scans a customer's in-store loyalty QR code."""
    from app.modules.membership_rewards.services.qr_scan_service import staff_scan_qr

    user, tenant, _ = ctx
    return await staff_scan_qr(
        db,
        tenant_id=tenant.id,
        payload=data.payload,
        staff_user_id=user.id,
    )


@router.post(
    "/redemptions/fulfill",
    response_model=RedemptionFulfillResponse,
    dependencies=[Depends(require_membership_rewards)],
)
async def fulfill_redemption_code(
    data: RedemptionFulfillRequest,
    ctx: CurrentTenantContext,
    db: AsyncSession = Depends(get_db),
):
    """Staff validates a customer's one-time redemption code in store."""
    from sqlalchemy import select

    from app.modules.crm.models import Customer
    from app.modules.membership_rewards.engines.redemption_engine import fulfill_redemption_by_code
    from app.modules.membership_rewards.models import MrRewardCatalog

    _, tenant, _ = ctx
    redemption = await fulfill_redemption_by_code(
        db, tenant_id=tenant.id, fulfillment_code=data.fulfillment_code
    )
    catalog = await db.get(MrRewardCatalog, redemption.catalog_item_id)
    customer = (
        await db.execute(select(Customer).where(Customer.id == redemption.customer_id))
    ).scalar_one_or_none()
    name = None
    if customer:
        name = f"{customer.first_name or ''} {customer.last_name or ''}".strip() or customer.email
    return {
        "id": redemption.id,
        "status": redemption.status,
        "reward_name": catalog.name if catalog else None,
        "customer_name": name,
        "points_spent": redemption.points_spent,
        "message": "Redemption fulfilled",
    }


@router.get("/status", response_model=MembershipStatusResponse)
async def membership_status(ctx: CurrentTenantContext, db: AsyncSession = Depends(get_db)):
    _, tenant, _ = ctx
    return await service.get_status(db, tenant.id)


@router.get("/trial", response_model=TrialStatusResponse)
async def membership_trial_status(ctx: CurrentTenantContext, db: AsyncSession = Depends(get_db)):
    """Trial banner, urgency modal, and win-back state for the dashboard."""
    from app.modules.membership_rewards.reminders import get_trial_status

    _, tenant, _ = ctx
    return await get_trial_status(db, tenant.id)


@router.post("/dev/grant", response_model=MembershipStatusResponse)
async def dev_grant_membership_rewards(
    ctx: CurrentTenantContext,
    db: AsyncSession = Depends(get_db),
):
    """Development only: grant Membership & Rewards without Stripe."""
    from app.core.config import settings
    from fastapi import HTTPException

    if settings.ENVIRONMENT == "production":
        raise HTTPException(403, "Not available in production")
    _, tenant, _ = ctx
    await service.grant_addon(db, tenant.id)
    return await service.get_status(db, tenant.id)


@router.post("/checkout", response_model=CheckoutResponse)
async def membership_checkout(
    data: CheckoutRequest,
    ctx: OwnerContext,
    db: AsyncSession = Depends(get_db),
):
    _, tenant, _ = ctx
    url = await service.create_addon_checkout(
        db, tenant, success_url=data.success_url, cancel_url=data.cancel_url
    )
    return CheckoutResponse(checkout_url=url)


@router.get("/dashboard", response_model=DashboardResponse, dependencies=[Depends(require_membership_rewards)])
async def membership_dashboard(ctx: CurrentTenantContext, db: AsyncSession = Depends(get_db)):
    _, tenant, _ = ctx
    return await service.get_dashboard(db, tenant.id)


@router.get("/analytics", response_model=AnalyticsResponse, dependencies=[Depends(require_membership_rewards)])
async def membership_analytics(ctx: CurrentTenantContext, db: AsyncSession = Depends(get_db)):
    _, tenant, _ = ctx
    return await service.get_analytics(db, tenant.id)


@router.get(
    "/loyalty/customers",
    response_model=LoyaltyCustomerListResponse,
    dependencies=[Depends(require_membership_rewards)],
)
async def loyalty_customers(
    ctx: CurrentTenantContext,
    db: AsyncSession = Depends(get_db),
    search: str | None = None,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    _, tenant, _ = ctx
    return await service.list_loyalty_customers(db, tenant.id, search=search, limit=limit, offset=offset)


@router.get(
    "/redemptions",
    response_model=RedemptionListResponse,
    dependencies=[Depends(require_membership_rewards)],
)
async def list_redemptions(
    ctx: CurrentTenantContext,
    db: AsyncSession = Depends(get_db),
    status: str | None = None,
    limit: int = Query(50, ge=1, le=200),
):
    _, tenant, _ = ctx
    items = await service.list_redemptions(db, tenant.id, status=status, limit=limit)
    return {"items": items}


@router.get(
    "/loyalty/leaderboard",
    response_model=LoyaltyLeaderboardResponse,
    dependencies=[Depends(require_membership_rewards)],
)
async def loyalty_leaderboard(
    ctx: CurrentTenantContext,
    db: AsyncSession = Depends(get_db),
    limit: int = Query(20, ge=1, le=100),
):
    _, tenant, _ = ctx
    items = await service.list_loyalty_leaderboard(db, tenant.id, limit=limit)
    return {"items": items}


@router.get("/settings", response_model=SettingsResponse, dependencies=[Depends(require_membership_rewards)])
async def get_settings(ctx: CurrentTenantContext, db: AsyncSession = Depends(get_db)):
    _, tenant, _ = ctx
    row = await service.get_settings(db, tenant.id)
    return row


@router.patch("/settings", response_model=SettingsResponse, dependencies=[Depends(require_membership_rewards)])
async def patch_settings(
    data: EarnRulesUpdate,
    ctx: CurrentTenantContext,
    db: AsyncSession = Depends(get_db),
):
    _, tenant, _ = ctx
    return await service.update_settings(db, tenant.id, data)


@router.get("/plans", response_model=PlanListResponse, dependencies=[Depends(require_membership_rewards)])
async def list_plans(
    ctx: CurrentTenantContext,
    db: AsyncSession = Depends(get_db),
    active_only: bool = Query(False),
):
    _, tenant, _ = ctx
    items = await service.list_plans(db, tenant.id, active_only=active_only)
    return {"items": items}


@router.post("/plans", response_model=PlanResponse, dependencies=[Depends(require_membership_rewards)])
async def create_plan(
    data: PlanCreate,
    ctx: CurrentTenantContext,
    db: AsyncSession = Depends(get_db),
):
    _, tenant, _ = ctx
    return await service.create_plan(db, tenant.id, data)


@router.patch("/plans/{plan_id}", response_model=PlanResponse, dependencies=[Depends(require_membership_rewards)])
async def update_plan(
    plan_id: uuid.UUID,
    data: PlanUpdate,
    ctx: CurrentTenantContext,
    db: AsyncSession = Depends(get_db),
):
    _, tenant, _ = ctx
    return await service.update_plan(db, tenant.id, plan_id, data)


@router.delete("/plans/{plan_id}", status_code=204, dependencies=[Depends(require_membership_rewards)])
async def delete_plan(
    plan_id: uuid.UUID,
    ctx: CurrentTenantContext,
    db: AsyncSession = Depends(get_db),
):
    _, tenant, _ = ctx
    await service.delete_plan(db, tenant.id, plan_id)


@router.get("/tiers", response_model=TierListResponse, dependencies=[Depends(require_membership_rewards)])
async def list_tiers(ctx: CurrentTenantContext, db: AsyncSession = Depends(get_db)):
    _, tenant, _ = ctx
    items = await service.list_tiers(db, tenant.id)
    return {"items": items}


@router.patch("/tiers/{tier_id}", response_model=TierResponse, dependencies=[Depends(require_membership_rewards)])
async def update_tier(
    tier_id: uuid.UUID,
    data: TierUpdate,
    ctx: CurrentTenantContext,
    db: AsyncSession = Depends(get_db),
):
    _, tenant, _ = ctx
    return await service.update_tier(db, tenant.id, tier_id, data)


@router.get("/catalog", response_model=CatalogListResponse, dependencies=[Depends(require_membership_rewards)])
async def list_catalog(ctx: CurrentTenantContext, db: AsyncSession = Depends(get_db)):
    _, tenant, _ = ctx
    items = await service.list_catalog(db, tenant.id)
    return {"items": items}


@router.post("/catalog", response_model=CatalogItemResponse, dependencies=[Depends(require_membership_rewards)])
async def create_catalog_item(
    data: CatalogItemCreate,
    ctx: CurrentTenantContext,
    db: AsyncSession = Depends(get_db),
):
    _, tenant, _ = ctx
    return await service.create_catalog_item(db, tenant.id, data)


@router.get(
    "/customers/{customer_id}/loyalty",
    response_model=CustomerLoyaltyResponse,
    dependencies=[Depends(require_membership_rewards)],
)
async def customer_loyalty(
    customer_id: uuid.UUID,
    ctx: CurrentTenantContext,
    db: AsyncSession = Depends(get_db),
):
    _, tenant, _ = ctx
    row = await service.get_customer_loyalty(db, tenant.id, customer_id)
    return row


@router.get(
    "/customers/{customer_id}/ledger",
    response_model=list[PointsLedgerEntry],
    dependencies=[Depends(require_membership_rewards)],
)
async def customer_ledger(
    customer_id: uuid.UUID,
    ctx: CurrentTenantContext,
    db: AsyncSession = Depends(get_db),
    limit: int = Query(50, ge=1, le=200),
):
    _, tenant, _ = ctx
    return await service.list_ledger(db, tenant.id, customer_id, limit=limit)


@router.post("/points/adjust", response_model=PointsLedgerEntry, dependencies=[Depends(require_membership_rewards)])
async def adjust_points(
    data: PointsAdjustRequest,
    ctx: CurrentTenantContext,
    db: AsyncSession = Depends(get_db),
):
    _, tenant, _ = ctx
    return await service.adjust_points(
        db,
        tenant.id,
        data.customer_id,
        data.amount,
        source=data.source,
        description=data.description,
    )


@router.post(
    "/customers/{customer_id}/redeem/{catalog_item_id}",
    dependencies=[Depends(require_membership_rewards)],
)
async def redeem_reward(
    customer_id: uuid.UUID,
    catalog_item_id: uuid.UUID,
    ctx: CurrentTenantContext,
    db: AsyncSession = Depends(get_db),
):
    _, tenant, _ = ctx
    redemption = await service.redeem_reward(db, tenant.id, customer_id, catalog_item_id)
    return {"id": str(redemption.id), "status": redemption.status, "points_spent": redemption.points_spent}


@router.get("/landing", response_model=LandingConfigResponse, dependencies=[Depends(require_membership_rewards)])
async def get_landing(ctx: CurrentTenantContext, db: AsyncSession = Depends(get_db)):
    _, tenant, _ = ctx
    data = await service.get_landing_config(db, tenant.id)
    return data


@router.patch("/landing", dependencies=[Depends(require_membership_rewards)])
async def patch_landing(
    data: LandingConfigUpdate,
    ctx: CurrentTenantContext,
    db: AsyncSession = Depends(get_db),
):
    _, tenant, _ = ctx
    await service.update_landing_config(db, tenant.id, data)
    return await service.get_landing_config(db, tenant.id)


@router.post("/landing/publish", dependencies=[Depends(require_membership_rewards)])
async def publish_landing(ctx: CurrentTenantContext, db: AsyncSession = Depends(get_db)):
    _, tenant, _ = ctx
    await service.publish_landing(db, tenant.id)
    return await service.get_landing_config(db, tenant.id)


@router.post("/landing/regenerate", dependencies=[Depends(require_membership_rewards)])
async def regenerate_landing(ctx: CurrentTenantContext, db: AsyncSession = Depends(get_db)):
    _, tenant, _ = ctx
    await service.regenerate_landing(db, tenant.id)
    return await service.get_landing_config(db, tenant.id)


@router.get("/subscriptions", response_model=SubscriptionListResponse, dependencies=[Depends(require_membership_rewards)])
async def list_subscriptions(
    ctx: CurrentTenantContext,
    db: AsyncSession = Depends(get_db),
    customer_id: uuid.UUID | None = None,
    status: str | None = None,
):
    _, tenant, _ = ctx
    items = await service.list_subscriptions(db, tenant.id, customer_id=customer_id, status=status)
    return {"items": items}


@router.post("/subscriptions", response_model=SubscriptionResponse, dependencies=[Depends(require_membership_rewards)])
async def create_subscription(
    data: SubscriptionCreate,
    ctx: CurrentTenantContext,
    db: AsyncSession = Depends(get_db),
):
    _, tenant, _ = ctx
    return await service.create_subscription(
        db,
        tenant.id,
        customer_id=data.customer_id,
        plan_id=data.plan_id,
        started_at=data.started_at,
    )


@router.get(
    "/subscriptions/{subscription_id}",
    response_model=SubscriptionResponse,
    dependencies=[Depends(require_membership_rewards)],
)
async def get_subscription(
    subscription_id: uuid.UUID,
    ctx: CurrentTenantContext,
    db: AsyncSession = Depends(get_db),
):
    _, tenant, _ = ctx
    return await service.get_subscription(db, tenant.id, subscription_id)


@router.post(
    "/subscriptions/{subscription_id}/cancel",
    response_model=SubscriptionResponse,
    dependencies=[Depends(require_membership_rewards)],
)
async def cancel_subscription(
    subscription_id: uuid.UUID,
    ctx: CurrentTenantContext,
    db: AsyncSession = Depends(get_db),
):
    _, tenant, _ = ctx
    return await service.cancel_subscription(db, tenant.id, subscription_id)
