"""Notification REST + WebSocket endpoints."""
from __future__ import annotations

import asyncio
import json
import logging
from uuid import UUID

from fastapi import APIRouter, Cookie, Depends, Query, Request, WebSocket, WebSocketDisconnect
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db, get_db_context, set_rls_context
from app.core.dependencies import CurrentTenantContext
from app.core.security import decode_access_token
from app.modules.auth.models import User
from app.modules.notifications import service
from app.modules.notifications.schemas import (
    NotificationListResponse,
    NotificationPreferenceResponse,
    NotificationPreferencesUpdate,
    NotificationResponse,
    PushSubscriptionIn,
    PushSubscriptionResponse,
)
from app.modules.tenants.models import Tenant, TenantMember

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get("/push/public-key")
async def push_public_key():
    return {"public_key": service.push_public_key(), "configured": service.push_is_configured()}


@router.post("/push/subscriptions", response_model=PushSubscriptionResponse)
async def upsert_push_subscription(
    body: PushSubscriptionIn,
    request: Request,
    ctx: CurrentTenantContext,
    db: AsyncSession = Depends(get_db),
):
    user, tenant, _ = ctx
    keys = body.keys or {}
    row = await service.upsert_push_subscription(
        db,
        tenant_id=tenant.id,
        user_id=user.id,
        endpoint=body.endpoint,
        p256dh=keys.get("p256dh", ""),
        auth=keys.get("auth", ""),
        user_agent=body.user_agent or request.headers.get("user-agent"),
    )
    return {"id": row.id, "endpoint": row.endpoint, "is_active": row.is_active}


@router.delete("/push/subscriptions")
async def delete_push_subscription(
    endpoint: str,
    ctx: CurrentTenantContext,
    db: AsyncSession = Depends(get_db),
):
    user, _tenant, _ = ctx
    deleted = await service.delete_push_subscription(db, user_id=user.id, endpoint=endpoint)
    return {"deleted": deleted}


@router.get("/preferences", response_model=list[NotificationPreferenceResponse])
async def list_preferences(
    ctx: CurrentTenantContext,
    db: AsyncSession = Depends(get_db),
):
    user, tenant, _ = ctx
    return await service.list_preferences(db, tenant_id=tenant.id, user_id=user.id)


@router.put("/preferences", response_model=list[NotificationPreferenceResponse])
async def update_preferences(
    body: NotificationPreferencesUpdate,
    ctx: CurrentTenantContext,
    db: AsyncSession = Depends(get_db),
):
    user, tenant, _ = ctx
    return await service.update_preferences(
        db,
        tenant_id=tenant.id,
        user_id=user.id,
        preferences=[p.model_dump() for p in body.preferences],
    )


@router.get("", response_model=NotificationListResponse)
async def list_notifications(
    ctx: CurrentTenantContext,
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    unread_only: bool = Query(False),
    include_archived: bool = Query(False),
):
    user, tenant, _ = ctx
    items, total, unread = await service.list_notifications(
        db,
        tenant.id,
        user.id,
        page=page,
        page_size=page_size,
        unread_only=unread_only,
        include_archived=include_archived,
    )
    return {
        "items": items,
        "total": total,
        "unread": unread,
        "page": page,
        "page_size": page_size,
    }


@router.post("/{notification_id}/read", response_model=NotificationResponse)
async def mark_read(
    notification_id: UUID,
    ctx: CurrentTenantContext,
    db: AsyncSession = Depends(get_db),
):
    user, tenant, _ = ctx
    return await service.mark_read(db, tenant.id, user.id, notification_id)


@router.post("/read-all")
async def mark_all_read(
    ctx: CurrentTenantContext,
    db: AsyncSession = Depends(get_db),
):
    user, tenant, _ = ctx
    updated = await service.mark_all_read(db, tenant.id, user.id)
    return {"updated": updated}


@router.post("/{notification_id}/archive", response_model=NotificationResponse)
async def archive(
    notification_id: UUID,
    ctx: CurrentTenantContext,
    db: AsyncSession = Depends(get_db),
):
    user, tenant, _ = ctx
    return await service.archive(db, tenant.id, user.id, notification_id)


# ── WebSocket channel ────────────────────────────────────────────────────────
# Accepts the access token in the query string OR the access_token cookie
# (since browsers don't allow custom headers on WebSocket connections).

async def _resolve_ws_principal(
    db: AsyncSession,
    token: str | None,
) -> tuple[User, Tenant] | None:
    if not token:
        return None
    try:
        payload = decode_access_token(token)
        user_id = payload.get("sub")
        tenant_id = payload.get("tid")
        if not user_id or not tenant_id:
            return None
    except JWTError:
        return None

    user = (
        await db.execute(select(User).where(User.id == user_id, User.deleted_at.is_(None)))
    ).scalar_one_or_none()
    if not user:
        return None

    member = (
        await db.execute(
            select(TenantMember, Tenant)
            .join(Tenant, TenantMember.tenant_id == Tenant.id)
            .where(
                TenantMember.user_id == user.id,
                TenantMember.tenant_id == tenant_id,
                Tenant.is_active == True,  # noqa: E712
            )
        )
    ).first()
    if not member:
        return None
    return user, member[1]


@router.websocket("/ws")
async def notifications_ws(
    websocket: WebSocket,
    token: str | None = Query(default=None),
    cookie_token: str | None = Cookie(default=None, alias="access_token"),
):
    """Live notification stream.

    Auth: pass the access token either as `?token=...` or via the
    `access_token` cookie (preferred for browsers).
    """
    auth_token = token or cookie_token
    async with get_db_context() as db:
        principal = await _resolve_ws_principal(db, auth_token)

    if not principal:
        await websocket.close(code=4401)  # 4401 = custom unauthorized
        return

    user, tenant = principal
    await websocket.accept()

    queue = service.subscribe(tenant.id, user.id)
    logger.info("WS connected user=%s tenant=%s", user.id, tenant.id)

    try:
        # Initial unread count so the bell updates immediately on reconnect.
        async with get_db_context() as db:
            await set_rls_context(db, tenant.id)
            _, total, unread = await service.list_notifications(db, tenant.id, user.id, page=1, page_size=1)
        await websocket.send_text(json.dumps({"type": "hello", "unread": unread, "total": total}))

        while True:
            try:
                payload = await asyncio.wait_for(queue.get(), timeout=25.0)
                await websocket.send_text(json.dumps({"type": "notification", "data": payload}))
            except asyncio.TimeoutError:
                # Periodic ping keeps the connection alive through proxies.
                await websocket.send_text(json.dumps({"type": "ping"}))
    except WebSocketDisconnect:
        logger.info("WS disconnected user=%s", user.id)
    except Exception as exc:
        logger.warning("WS error user=%s: %s", user.id, exc)
    finally:
        service.unsubscribe(tenant.id, user.id, queue)
