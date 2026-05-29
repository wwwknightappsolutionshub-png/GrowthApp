"""Tenant integrations API."""
from __future__ import annotations

import orjson
from urllib.parse import quote as url_quote
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Query, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.dependencies import CurrentTenantContext
from app.core.exceptions import BadRequestException
from app.modules.integrations import service
from app.modules.integrations.google import service as tenant_google
from app.modules.integrations.social import service as social_service
from app.modules.integrations.webhooks import social_webhook_handler
from app.modules.integrations.schemas import (
    GoogleAuthUrlResponse,
    GoogleConnectionStatus,
    GoogleGenericSyncResponse,
    GoogleLocationPick,
    GoogleReviewReplyRequest,
    GoogleReviewResponse,
    GoogleSyncResponse,
    IntegrationsOnboardingState,
    IntegrationsOnboardingUpdate,
    SocialChannelResponse,
    SocialPostRequest,
    TenantGoogleCredentialsRegister,
    TenantGoogleCredentialsStatus,
)
from app.modules.tenants.models import Tenant

router = APIRouter(prefix="/integrations", tags=["Integrations"])


def _integrations_redirect(extra: str = "") -> str:
    base = f"{settings.FRONTEND_URL.rstrip('/')}/dashboard/integrations"
    return f"{base}{extra}"


# ── Platform Google OAuth (existing) ─────────────────────────────────────


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
    """Platform OAuth redirect target."""
    base = _integrations_redirect()
    if error:
        reason = url_quote(str(error)[:80], safe="")
        return RedirectResponse(
            url=f"{base}?google=error&reason={reason}",
            status_code=302,
        )
    if not code or not state:
        return RedirectResponse(url=f"{base}?google=error&reason=missing_code", status_code=302)

    try:
        tenant_id, _user_id = service.parse_oauth_state(state)
        await service.complete_oauth_callback(db, code=code, tenant_id=tenant_id)
    except BadRequestException as exc:
        reason = url_quote(str(exc.detail)[:80], safe="")
        return RedirectResponse(
            url=f"{base}?google=error&reason={reason}",
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


# ── Tenant-owned Google OAuth ─────────────────────────────────────────────


@router.get("/google/credentials", response_model=TenantGoogleCredentialsStatus)
async def google_credentials_status(ctx: CurrentTenantContext, db: AsyncSession = Depends(get_db)):
    _, tenant, _ = ctx
    row = await tenant_google.get_credentials(db, tenant.id)
    return tenant_google.credentials_status(row)


@router.post("/google/register-credentials", response_model=TenantGoogleCredentialsStatus)
async def google_register_credentials(
    body: TenantGoogleCredentialsRegister,
    ctx: CurrentTenantContext,
    db: AsyncSession = Depends(get_db),
):
    _, tenant, _ = ctx
    return await tenant_google.register_credentials(
        db,
        tenant.id,
        google_client_id=body.google_client_id,
        google_client_secret=body.google_client_secret,
    )


@router.get("/google/auth-url", response_model=GoogleAuthUrlResponse)
async def google_auth_url(ctx: CurrentTenantContext, db: AsyncSession = Depends(get_db)):
    user, tenant, _ = ctx
    url = await tenant_google.auth_url(db, tenant.id, user.id)
    return GoogleAuthUrlResponse(url=url)


@router.get("/google/oauth-callback")
async def google_oauth_callback(
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    """Tenant-owned OAuth redirect — CustomerFlow hosts URI only."""
    base = _integrations_redirect("/google")
    if error:
        reason = url_quote(str(error)[:80], safe="")
        return RedirectResponse(
            url=f"{base}?google=error&reason={reason}",
            status_code=302,
        )
    if not code or not state:
        return RedirectResponse(url=f"{base}?google=error&reason=missing_code", status_code=302)

    try:
        tenant_id, _user_id = service.parse_oauth_state(state)
        await tenant_google.complete_oauth_callback(db, code=code, tenant_id=tenant_id)
    except BadRequestException as exc:
        reason = url_quote(str(exc.detail)[:80], safe="")
        return RedirectResponse(
            url=f"{base}?google=error&reason={reason}",
            status_code=302,
        )
    except Exception:  # noqa: BLE001
        return RedirectResponse(url=f"{base}?google=error&reason=oauth_failed", status_code=302)

    return RedirectResponse(url=f"{base}?google=connected", status_code=302)


@router.post("/google/refresh-token", response_model=TenantGoogleCredentialsStatus)
async def google_refresh_token(ctx: CurrentTenantContext, db: AsyncSession = Depends(get_db)):
    _, tenant, _ = ctx
    return await tenant_google.refresh_token(db, tenant.id)


@router.get("/google/reviews/sync", response_model=GoogleSyncResponse)
async def google_reviews_sync(ctx: CurrentTenantContext, db: AsyncSession = Depends(get_db)):
    _, tenant, _ = ctx
    result = await tenant_google.sync_reviews(db, tenant.id)
    return GoogleSyncResponse(synced=result.get("synced", 0), total_fetched=result.get("total_fetched", 0))


@router.get("/google/messages/sync", response_model=GoogleGenericSyncResponse)
async def google_messages_sync(ctx: CurrentTenantContext, db: AsyncSession = Depends(get_db)):
    _, tenant, _ = ctx
    detail = await tenant_google.sync_messages(db, tenant.id)
    return GoogleGenericSyncResponse(detail=detail)


@router.get("/google/posts/sync", response_model=GoogleGenericSyncResponse)
async def google_posts_sync(ctx: CurrentTenantContext, db: AsyncSession = Depends(get_db)):
    _, tenant, _ = ctx
    detail = await tenant_google.sync_posts(db, tenant.id)
    return GoogleGenericSyncResponse(detail=detail)


@router.get("/google/photos/sync", response_model=GoogleGenericSyncResponse)
async def google_photos_sync(ctx: CurrentTenantContext, db: AsyncSession = Depends(get_db)):
    _, tenant, _ = ctx
    detail = await tenant_google.sync_photos(db, tenant.id)
    return GoogleGenericSyncResponse(detail=detail)


@router.get("/google/analytics/sync", response_model=GoogleGenericSyncResponse)
async def google_analytics_sync(ctx: CurrentTenantContext, db: AsyncSession = Depends(get_db)):
    _, tenant, _ = ctx
    detail = await tenant_google.sync_analytics(db, tenant.id)
    return GoogleGenericSyncResponse(detail=detail)


# ── Social channels (Zapier/Make) ─────────────────────────────────────────


@router.get("/social/channels", response_model=list[SocialChannelResponse])
async def list_social_channels(ctx: CurrentTenantContext, db: AsyncSession = Depends(get_db)):
    _, tenant, _ = ctx
    rows = await social_service.list_channels(db, tenant.id)
    return [social_service.channel_response(r) for r in rows]


@router.post("/social/channels/{platform}", response_model=SocialChannelResponse)
async def provision_social_channel(
    platform: str,
    ctx: CurrentTenantContext,
    db: AsyncSession = Depends(get_db),
):
    _, tenant, _ = ctx
    row = await social_service.provision_channel(db, tenant.id, platform)
    return social_service.channel_response(row)


@router.post("/social/post")
async def social_post(
    body: SocialPostRequest,
    ctx: CurrentTenantContext,
    db: AsyncSession = Depends(get_db),
):
    _, tenant, _ = ctx
    return await social_service.post_to_social(
        db,
        tenant.id,
        platform=body.platform,
        content=body.content,
        media_url=body.media_url,
    )


@router.post("/webhooks/social/{channel_id}")
async def social_webhook(
    channel_id: UUID,
    request: Request,
    key: str = Query(..., alias="key"),
    x_cf_signature: str | None = Header(default=None, alias="X-CF-Signature"),
    db: AsyncSession = Depends(get_db),
):
    body = await request.body()
    try:
        payload_dict = orjson.loads(body) if body else {}
    except orjson.JSONDecodeError:
        raise BadRequestException("Invalid JSON payload")

    return await social_webhook_handler.handle_social_webhook(
        db,
        channel_id=str(channel_id),
        api_key=key,
        body=body,
        signature=x_cf_signature,
        payload_dict=payload_dict if isinstance(payload_dict, dict) else {},
    )


# ── Onboarding progress ───────────────────────────────────────────────────


@router.get("/onboarding", response_model=IntegrationsOnboardingState)
async def integrations_onboarding_get(ctx: CurrentTenantContext, db: AsyncSession = Depends(get_db)):
    _, tenant, _ = ctx
    row = await db.get(Tenant, tenant.id)
    data = row.integrations_onboarding if row else {}
    return IntegrationsOnboardingState(**{**IntegrationsOnboardingState().model_dump(), **(data or {})})


@router.post("/onboarding", response_model=IntegrationsOnboardingState)
async def integrations_onboarding_save(
    body: IntegrationsOnboardingUpdate,
    ctx: CurrentTenantContext,
    db: AsyncSession = Depends(get_db),
):
    _, tenant, _ = ctx
    row = await db.get(Tenant, tenant.id)
    if not row:
        raise BadRequestException("Tenant not found")
    current = dict(row.integrations_onboarding or {})
    for field, value in body.model_dump(exclude_none=True).items():
        current[field] = value
    row.integrations_onboarding = current
    db.add(row)
    await db.commit()
    return IntegrationsOnboardingState(**{**IntegrationsOnboardingState().model_dump(), **current})
