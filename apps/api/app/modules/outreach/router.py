"""REST endpoints for the outreach engine."""
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import CurrentTenantContext
from app.modules.outreach import service
from app.modules.outreach.models import OutreachCampaign
from app.modules.outreach.schemas import (
    AIStepDraftRequest,
    AIStepDraftResponse,
    CampaignCreate,
    CampaignResponse,
    CampaignStats,
    CampaignUpdate,
    WinbackPresetRequest,
)

router = APIRouter(prefix="/outreach", tags=["Outreach"])


@router.get("/campaigns", response_model=list[CampaignResponse])
async def list_campaigns(
    ctx: CurrentTenantContext,
    db: AsyncSession = Depends(get_db),
    status_filter: str | None = Query(default=None, alias="status"),
    limit: int = Query(default=100, ge=1, le=500),
):
    _, tenant, _ = ctx
    q = select(OutreachCampaign).where(OutreachCampaign.tenant_id == tenant.id)
    if status_filter:
        q = q.where(OutreachCampaign.status == status_filter)
    rows = (await db.execute(q.order_by(OutreachCampaign.created_at.desc()).limit(limit))).scalars().all()
    return rows


@router.post("/campaigns", response_model=CampaignResponse, status_code=status.HTTP_201_CREATED)
async def create_campaign(
    body: CampaignCreate,
    ctx: CurrentTenantContext,
    db: AsyncSession = Depends(get_db),
):
    user, tenant, _ = ctx
    return await service.create_campaign(db, tenant.id, user.id, body)


@router.get("/campaigns/{campaign_id}", response_model=CampaignResponse)
async def get_campaign(
    campaign_id: UUID,
    ctx: CurrentTenantContext,
    db: AsyncSession = Depends(get_db),
):
    _, tenant, _ = ctx
    return await service._get(db, tenant.id, campaign_id)


@router.patch("/campaigns/{campaign_id}", response_model=CampaignResponse)
async def update_campaign(
    campaign_id: UUID,
    body: CampaignUpdate,
    ctx: CurrentTenantContext,
    db: AsyncSession = Depends(get_db),
):
    user, tenant, _ = ctx
    return await service.update_campaign(db, tenant.id, user.id, campaign_id, body)


@router.delete("/campaigns/{campaign_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_campaign(
    campaign_id: UUID,
    ctx: CurrentTenantContext,
    db: AsyncSession = Depends(get_db),
):
    user, tenant, _ = ctx
    await service.delete_campaign(db, tenant.id, user.id, campaign_id)


@router.post("/campaigns/{campaign_id}/launch", response_model=CampaignResponse)
async def launch_campaign(
    campaign_id: UUID,
    ctx: CurrentTenantContext,
    db: AsyncSession = Depends(get_db),
):
    user, tenant, _ = ctx
    return await service.launch_campaign(db, tenant.id, user.id, campaign_id)


@router.post("/campaigns/{campaign_id}/pause", response_model=CampaignResponse)
async def pause_campaign(
    campaign_id: UUID,
    ctx: CurrentTenantContext,
    db: AsyncSession = Depends(get_db),
):
    user, tenant, _ = ctx
    return await service.pause_campaign(db, tenant.id, user.id, campaign_id)


@router.post("/campaigns/{campaign_id}/resume", response_model=CampaignResponse)
async def resume_campaign(
    campaign_id: UUID,
    ctx: CurrentTenantContext,
    db: AsyncSession = Depends(get_db),
):
    user, tenant, _ = ctx
    return await service.resume_campaign(db, tenant.id, user.id, campaign_id)


@router.get("/campaigns/{campaign_id}/stats", response_model=CampaignStats)
async def get_stats(
    campaign_id: UUID,
    ctx: CurrentTenantContext,
    db: AsyncSession = Depends(get_db),
):
    _, tenant, _ = ctx
    return await service.campaign_stats(db, tenant.id, campaign_id)


@router.post("/ai-draft-step", response_model=AIStepDraftResponse)
async def ai_draft_step(
    body: AIStepDraftRequest,
    ctx: CurrentTenantContext,
    db: AsyncSession = Depends(get_db),
):
    user, tenant, _ = ctx
    return await service.ai_draft_step(db, tenant.id, user.id, body)


@router.post("/winback", response_model=CampaignResponse, status_code=status.HTTP_201_CREATED)
async def winback_preset(
    body: WinbackPresetRequest,
    ctx: CurrentTenantContext,
    db: AsyncSession = Depends(get_db),
):
    user, tenant, _ = ctx
    return await service.create_winback_preset(db, tenant.id, user.id, body)
