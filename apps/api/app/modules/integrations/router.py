"""Tenant integrations API."""
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.dependencies import CurrentTenantContext
from app.core.exceptions import BadRequestException
from app.modules.integrations import service
from app.modules.integrations.schemas import (
    GoogleConnectionStatus,
    GoogleLocationPick,
    GoogleReviewReplyRequest,
    GoogleReviewResponse,
    GoogleSyncResponse,
)

router = APIRouter(prefix="/integrations", tags=["Integrations"])


@router.get("/google/status", response_model=GoogleConnectionStatus)
async def google_status(ctx: CurrentTenantContext, db: AsyncSession = Depends(get_db)):
    _, tenant, _ = ctx
    return await service.connection_status(db, tenant.id)


@router.get("/google/connect")
async def google_connect(ctx: CurrentTenantContext):
    user, tenant, _ = ctx
    url = service.connect_authorization_url(tenant_id=tenant.id, user_id=user.id)
    return RedirectResponse(url=url, status_code=302)


@router.get("/google/callback")
async def google_callback(
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    """OAuth redirect target (unauthenticated — state carries tenant id)."""
    base = f"{settings.FRONTEND_URL.rstrip('/')}/dashboard/integrations"
    if error:
        return RedirectResponse(url=f"{base}?google=error&reason={error}", status_code=302)
    if not code or not state:
        return RedirectResponse(url=f"{base}?google=error&reason=missing_code", status_code=302)

    try:
        tenant_id, _user_id = service.parse_oauth_state(state)
        await service.complete_oauth_callback(db, code=code, tenant_id=tenant_id)
    except BadRequestException as exc:
        return RedirectResponse(
            url=f"{base}?google=error&reason={str(exc.detail)[:80]}",
            status_code=302,
        )
    except Exception:  # noqa: BLE001
        return RedirectResponse(url=f"{base}?google=error&reason=oauth_failed", status_code=302)

    return RedirectResponse(url=f"{base}?google=connected", status_code=302)


@router.post("/google/disconnect")
async def google_disconnect(ctx: CurrentTenantContext, db: AsyncSession = Depends(get_db)):
    _, tenant, _ = ctx
    await service.disconnect_google(db, tenant.id)
    return {"ok": True}


@router.post("/google/select-location", response_model=GoogleConnectionStatus)
async def google_select_location(
    body: GoogleLocationPick,
    ctx: CurrentTenantContext,
    db: AsyncSession = Depends(get_db),
):
    _, tenant, _ = ctx
    await service.select_location(db, tenant.id, location_name=body.location_name)
    return await service.connection_status(db, tenant.id)


@router.post("/google/sync", response_model=GoogleSyncResponse)
async def google_sync(ctx: CurrentTenantContext, db: AsyncSession = Depends(get_db)):
    _, tenant, _ = ctx
    result = await service.sync_google_reviews(db, tenant.id)
    return GoogleSyncResponse(**result)


@router.get("/google/reviews", response_model=list[GoogleReviewResponse])
async def google_reviews(ctx: CurrentTenantContext, db: AsyncSession = Depends(get_db)):
    _, tenant, _ = ctx
    rows = await service.list_google_reviews(db, tenant.id)
    return rows


@router.post("/google/reviews/{review_id}/reply", response_model=GoogleReviewResponse)
async def google_review_reply(
    review_id: UUID,
    body: GoogleReviewReplyRequest,
    ctx: CurrentTenantContext,
    db: AsyncSession = Depends(get_db),
):
    _, tenant, _ = ctx
    row = await service.reply_to_google_review(
        db, tenant.id, review_id=review_id, comment=body.comment
    )
    return row
