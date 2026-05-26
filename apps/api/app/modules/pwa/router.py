from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import CurrentTenantContext, CurrentUser
from app.modules.pwa import service

router = APIRouter(prefix="/pwa", tags=["PWA"])


@router.get("/branding")
async def pwa_branding(ctx: CurrentTenantContext, db: AsyncSession = Depends(get_db)):
    _, tenant, _ = ctx
    return await service.get_branding_payload(db, tenant_id=tenant.id)


@router.post("/exit-intent")
async def pwa_exit_intent(user: CurrentUser, ctx: CurrentTenantContext, db: AsyncSession = Depends(get_db)):
    _, tenant, _ = ctx
    sent = await service.record_exit_intent(db, tenant_id=tenant.id, user_id=user.id)
    return {"ok": True, "sent": sent}
