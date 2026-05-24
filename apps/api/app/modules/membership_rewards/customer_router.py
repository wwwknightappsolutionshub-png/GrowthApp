"""Customer loyalty portal API — `/api/v1/loyalty-portal/*`."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import NotFoundException, UnauthorizedException
from app.modules.membership_rewards import service as mr_service
from app.modules.membership_rewards.customer_auth.credentials import (
    authenticate_customer,
    set_password,
)
from app.modules.membership_rewards.customer_auth.magic_link import (
    consume_magic_link,
    issue_magic_link,
)
from app.modules.membership_rewards.customer_dependencies import CurrentCustomerContext
from app.modules.membership_rewards.entitlement import tenant_has_membership_rewards
from app.modules.membership_rewards.models import MrRewardCatalog
from app.modules.membership_rewards.schemas import (
    CatalogListResponse,
    CustomerPortalMeResponse,
    CustomerPortalRedeemResponse,
    LoyaltyBrandingResponse,
    MagicLinkRequest,
    MagicLinkVerifyRequest,
    MessageResponse,
    PortalAuthResponse,
    PortalHistoryResponse,
    PortalLoginRequest,
    PortalPendingRedemptionsResponse,
    PortalPreferencesResponse,
    PortalPreferencesUpdate,
    PortalQrResponse,
    PortalSetPasswordRequest,
    PushSubscribeRequest,
    PushSubscribeResponse,
)
from app.modules.membership_rewards.services.portal_service import (
    build_customer_profile,
    delete_customer_push_subscriptions,
    find_customer_by_email,
    get_customer_qr_payload,
    get_portal_branding,
    list_active_rewards,
    list_pending_redemptions,
    resolve_tenant_by_slug,
    upsert_customer_push_subscription,
)
from app.modules.membership_rewards.services.customer_loyalty_service import list_ledger
from app.modules.membership_rewards.services.customer_preferences_service import (
    get_or_create_preferences,
    preferences_payload,
    update_preferences,
)

router = APIRouter(prefix="/loyalty-portal", tags=["Loyalty Portal"])


@router.get("/public/branding/{tenant_slug}", response_model=LoyaltyBrandingResponse)
async def portal_branding(tenant_slug: str, db: AsyncSession = Depends(get_db)):
    return await get_portal_branding(db, tenant_slug)


@router.post("/auth/magic-link", response_model=MessageResponse)
async def request_magic_link(data: MagicLinkRequest, db: AsyncSession = Depends(get_db)):
    """Request a login link. Always returns success to avoid email enumeration."""
    tenant = await resolve_tenant_by_slug(db, data.tenant_slug)
    if not await tenant_has_membership_rewards(db, tenant.id):
        return {"message": "If an account exists, a sign-in link has been sent."}

    customer = await find_customer_by_email(db, tenant.id, data.email)
    if customer:
        await issue_magic_link(
            db,
            tenant_id=tenant.id,
            customer_id=customer.id,
            email=data.email,
            next_path=data.next_path,
        )
    return {"message": "If an account exists, a sign-in link has been sent."}


@router.post("/auth/magic-link/verify", response_model=PortalAuthResponse)
async def verify_magic_link(
    data: MagicLinkVerifyRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    tenant = await resolve_tenant_by_slug(db, data.tenant_slug)
    ip = request.client.host if request.client else None
    tokens = await consume_magic_link(db, raw_token=data.token, tenant_id=tenant.id, ip=ip)
    return tokens


@router.post("/auth/login", response_model=PortalAuthResponse)
async def portal_login(data: PortalLoginRequest, db: AsyncSession = Depends(get_db)):
    tenant = await resolve_tenant_by_slug(db, data.tenant_slug)
    if not await tenant_has_membership_rewards(db, tenant.id):
        raise UnauthorizedException("Invalid email or password")

    customer = await find_customer_by_email(db, tenant.id, data.email)
    if not customer:
        raise UnauthorizedException("Invalid email or password")

    return await authenticate_customer(db, tenant.id, customer.id, data.password)


@router.post("/auth/set-password", response_model=MessageResponse)
async def portal_set_password(
    data: PortalSetPasswordRequest,
    ctx: CurrentCustomerContext,
    db: AsyncSession = Depends(get_db),
):
    customer, tenant = ctx
    await set_password(db, tenant.id, customer.id, data.new_password, must_change=False)
    return {"message": "Password updated"}


@router.get("/me", response_model=CustomerPortalMeResponse)
async def portal_me(ctx: CurrentCustomerContext, db: AsyncSession = Depends(get_db)):
    customer, tenant = ctx
    return await build_customer_profile(db, tenant, customer)


@router.get("/me/preferences", response_model=PortalPreferencesResponse)
async def portal_get_preferences(ctx: CurrentCustomerContext, db: AsyncSession = Depends(get_db)):
    customer, tenant = ctx
    prefs = await get_or_create_preferences(db, tenant.id, customer.id)
    return preferences_payload(prefs, customer)


@router.patch("/me/preferences", response_model=PortalPreferencesResponse)
async def portal_update_preferences(
    data: PortalPreferencesUpdate,
    ctx: CurrentCustomerContext,
    db: AsyncSession = Depends(get_db),
):
    customer, tenant = ctx
    return await update_preferences(
        db,
        tenant_id=tenant.id,
        customer=customer,
        date_of_birth=data.date_of_birth,
        marketing_email=data.marketing_email,
        marketing_sms=data.marketing_sms,
        birthday_participation=data.birthday_participation,
        expiring_points_reminders=data.expiring_points_reminders,
        update_dob="date_of_birth" in data.model_fields_set,
    )


@router.get("/rewards", response_model=CatalogListResponse)
async def portal_rewards(ctx: CurrentCustomerContext, db: AsyncSession = Depends(get_db)):
    _, tenant = ctx
    items = await list_active_rewards(db, tenant.id)
    return {"items": items}


@router.post("/rewards/{catalog_item_id}/redeem", response_model=CustomerPortalRedeemResponse)
async def portal_redeem(
    catalog_item_id: uuid.UUID,
    ctx: CurrentCustomerContext,
    db: AsyncSession = Depends(get_db),
):
    customer, tenant = ctx
    redemption = await mr_service.redeem_reward(db, tenant.id, customer.id, catalog_item_id)
    item = await db.get(MrRewardCatalog, catalog_item_id)
    return {
        "id": redemption.id,
        "status": redemption.status,
        "points_spent": redemption.points_spent,
        "reward_name": item.name if item else None,
        "fulfillment_code": redemption.fulfillment_code,
        "code_expires_at": redemption.code_expires_at,
    }


@router.get("/redemptions/pending", response_model=PortalPendingRedemptionsResponse)
async def portal_pending_redemptions(ctx: CurrentCustomerContext, db: AsyncSession = Depends(get_db)):
    customer, tenant = ctx
    items = await list_pending_redemptions(db, tenant.id, customer.id)
    return {"items": items}


@router.get("/history", response_model=PortalHistoryResponse)
async def portal_history(
    ctx: CurrentCustomerContext,
    db: AsyncSession = Depends(get_db),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    customer, tenant = ctx
    entries = await list_ledger(db, tenant.id, customer.id, limit=limit + offset)
    sliced = entries[offset : offset + limit]
    return {
        "items": sliced,
        "limit": limit,
        "offset": offset,
        "has_more": len(entries) > offset + limit,
    }


@router.get("/qr", response_model=PortalQrResponse)
async def portal_qr(ctx: CurrentCustomerContext, db: AsyncSession = Depends(get_db)):
    customer, tenant = ctx
    return await get_customer_qr_payload(db, tenant.id, customer.id)


@router.post("/push/subscribe", response_model=PushSubscribeResponse)
async def portal_push_subscribe(
    data: PushSubscribeRequest,
    ctx: CurrentCustomerContext,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    customer, tenant = ctx
    row = await upsert_customer_push_subscription(
        db,
        tenant_id=tenant.id,
        customer_id=customer.id,
        endpoint=data.endpoint,
        p256dh=data.keys.p256dh,
        auth=data.keys.auth,
        user_agent=request.headers.get("user-agent"),
    )
    return {"id": row.id, "endpoint": row.endpoint}


@router.post("/push/unsubscribe", response_model=MessageResponse)
async def portal_push_unsubscribe(ctx: CurrentCustomerContext, db: AsyncSession = Depends(get_db)):
    customer, tenant = ctx
    await delete_customer_push_subscriptions(db, tenant.id, customer.id)
    return {"message": "Push notifications disabled for this device"}
