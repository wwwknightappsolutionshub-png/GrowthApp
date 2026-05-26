"""Industry add-ons — status and vertical configuration (Phase 2 base)."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import CurrentTenantContext
from app.modules.addons.common.constants import (
    FEATURE_INDUSTRY_BILLING,
    FEATURE_INDUSTRY_BOOKING,
    FEATURE_INDUSTRY_CRM,
    Vertical,
)
from app.modules.addons.common.entitlement import tenant_has_addon
from app.modules.membership_rewards.constants import FEATURE_MEMBERSHIP_REWARDS
from app.modules.membership_rewards.entitlement import tenant_has_membership_rewards
from app.modules.pwa.constants import FEATURE_PWA_WHITE_LABEL
from app.modules.pwa.entitlement import tenant_has_pwa_white_label
from app.modules.addons.common.schemas import AddonStatusItem, AddonStatusResponse, SetVerticalRequest
from app.modules.addons.common.vertical import get_tenant_vertical, set_tenant_vertical

router = APIRouter(prefix="/addons", tags=["addons"])


@router.get("/status", response_model=AddonStatusResponse)
async def addon_status(
    ctx: CurrentTenantContext,
    db: AsyncSession = Depends(get_db),
) -> AddonStatusResponse:
    _, tenant, _ = ctx
    vertical = await get_tenant_vertical(db, tenant)
    booking = await tenant_has_addon(db, tenant.id, FEATURE_INDUSTRY_BOOKING)
    billing = await tenant_has_addon(db, tenant.id, FEATURE_INDUSTRY_BILLING)
    crm = await tenant_has_addon(db, tenant.id, FEATURE_INDUSTRY_CRM)
    membership = await tenant_has_membership_rewards(db, tenant.id)
    pwa_white_label = await tenant_has_pwa_white_label(db, tenant.id)
    return AddonStatusResponse(
        vertical=vertical.value,
        industry_booking=booking,
        industry_billing=billing,
        industry_crm=crm,
        membership_rewards=membership,
        items=[
            AddonStatusItem(feature_code=FEATURE_INDUSTRY_BOOKING, active=booking),
            AddonStatusItem(feature_code=FEATURE_INDUSTRY_BILLING, active=billing),
            AddonStatusItem(feature_code=FEATURE_INDUSTRY_CRM, active=crm),
            AddonStatusItem(feature_code=FEATURE_MEMBERSHIP_REWARDS, active=membership),
            AddonStatusItem(feature_code=FEATURE_PWA_WHITE_LABEL, active=pwa_white_label),
        ],
    )


@router.post("/dev/grant-all")
async def dev_grant_all_addons(
    ctx: CurrentTenantContext,
    db: AsyncSession = Depends(get_db),
):
    """Development only: grant all industry add-ons for local preview."""
    from app.core.config import settings
    from app.modules.addons.common.constants import (
        FEATURE_INDUSTRY_BILLING,
        FEATURE_INDUSTRY_BOOKING,
        FEATURE_INDUSTRY_CRM,
    )
    from app.modules.addons.common import service as addon_service
    from app.modules.membership_rewards import service as mr_service

    if settings.ENVIRONMENT == "production":
        from fastapi import HTTPException

        raise HTTPException(403, "Not available in production")
    _, tenant, _ = ctx
    for code in (FEATURE_INDUSTRY_BOOKING, FEATURE_INDUSTRY_BILLING, FEATURE_INDUSTRY_CRM):
        await addon_service.grant_addon(db, tenant.id, code)
    await mr_service.grant_addon(db, tenant.id)
    return await addon_status(ctx, db)


@router.patch("/vertical", response_model=AddonStatusResponse)
async def update_vertical(
    body: SetVerticalRequest,
    ctx: CurrentTenantContext,
    db: AsyncSession = Depends(get_db),
) -> AddonStatusResponse:
    _, tenant, _ = ctx
    await set_tenant_vertical(db, tenant.id, Vertical(body.vertical))
    await db.commit()
    return await addon_status(ctx, db)
