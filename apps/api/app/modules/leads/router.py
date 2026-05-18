from uuid import UUID
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.dependencies import CurrentTenantContext
from app.modules.leads import service
from app.modules.leads.schemas import (
    LeadCreate, LeadUpdate, LeadResponse, LeadListResponse,
    LeadRequestCreate, LeadRequestResponse, LeadQuotaResponse,
)
from app.modules.auth.schemas import MessageResponse

router = APIRouter(prefix="/leads", tags=["Leads"])


@router.get("", response_model=LeadListResponse)
async def list_leads(
    ctx: CurrentTenantContext,
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    status: str | None = None,
    source: str | None = None,
):
    _, tenant, _ = ctx
    items, total = await service.list_leads(db, tenant.id, page, page_size, status, source)
    return LeadListResponse(items=items, total=total, page=page, page_size=page_size)


@router.post("", response_model=LeadResponse, status_code=201)
async def create_lead(data: LeadCreate, ctx: CurrentTenantContext, db: AsyncSession = Depends(get_db)):
    _, tenant, _ = ctx
    return await service.create_lead_public(db, tenant, data)


# ── Lead Requests ─────────────────────────────────────────────────────────────

@router.get("/quota", response_model=LeadQuotaResponse)
async def get_quota(ctx: CurrentTenantContext, db: AsyncSession = Depends(get_db)):
    _, tenant, _ = ctx
    return await service.get_lead_quota(db, tenant.id)


@router.post("/request", response_model=LeadRequestResponse, status_code=201)
async def submit_request(
    body: LeadRequestCreate,
    ctx: CurrentTenantContext,
    db: AsyncSession = Depends(get_db),
):
    user, tenant, _ = ctx
    return await service.submit_lead_request(db, tenant.id, body, actor_user_id=user.id)


@router.get("/requests", response_model=list[LeadRequestResponse])
async def list_requests(
    ctx: CurrentTenantContext,
    db: AsyncSession = Depends(get_db),
):
    _, tenant, _ = ctx
    return await service.list_lead_requests(db, tenant.id)


@router.get("/{lead_id}", response_model=LeadResponse)
async def get_lead(lead_id: UUID, ctx: CurrentTenantContext, db: AsyncSession = Depends(get_db)):
    _, tenant, _ = ctx
    return await service.get_lead(db, tenant.id, lead_id)


@router.patch("/{lead_id}", response_model=LeadResponse)
async def update_lead(lead_id: UUID, data: LeadUpdate, ctx: CurrentTenantContext, db: AsyncSession = Depends(get_db)):
    user, tenant, _ = ctx
    return await service.update_lead(db, tenant.id, lead_id, data, actor_user_id=user.id)


@router.post("/{lead_id}/convert", status_code=201)
async def convert_lead(lead_id: UUID, ctx: CurrentTenantContext, db: AsyncSession = Depends(get_db)):
    user, tenant, _ = ctx
    deal = await service.convert_lead_to_deal(db, tenant.id, lead_id, actor_user_id=user.id)
    return {"deal_id": str(deal.id), "message": "Lead converted to deal"}


@router.delete("/{lead_id}", response_model=MessageResponse)
async def delete_lead(lead_id: UUID, ctx: CurrentTenantContext, db: AsyncSession = Depends(get_db)):
    user, tenant, _ = ctx
    await service.delete_lead(db, tenant.id, lead_id, actor_user_id=user.id)
    return MessageResponse(message="Lead deleted")
