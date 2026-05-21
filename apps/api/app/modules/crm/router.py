from uuid import UUID
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.dependencies import CurrentTenantContext
from app.modules.crm import service
from app.modules.crm import pipeline_service
from app.modules.crm.schemas import (
    CustomerCreate, CustomerUpdate, CustomerResponse,
    DealCreate, DealUpdate, DealResponse, PipelineResponse, MoveDealRequest,
    DealActivityResponse,
)
from app.modules.crm.enterprise_schemas import MoveDealRequestV2
from app.modules.auth.schemas import MessageResponse
from pydantic import BaseModel

router = APIRouter(prefix="/crm", tags=["CRM"])


@router.get("/pipeline", response_model=PipelineResponse)
async def get_pipeline(ctx: CurrentTenantContext, db: AsyncSession = Depends(get_db)):
    """Legacy pipeline view (deals only). Prefer GET /crm/board for leads+deals."""
    _, tenant, _ = ctx
    return await service.get_pipeline(db, tenant.id)


@router.get("/customers")
async def list_customers(ctx: CurrentTenantContext, db: AsyncSession = Depends(get_db), page: int = Query(1, ge=1), page_size: int = Query(25, ge=1, le=100)):
    _, tenant, _ = ctx
    items, total = await service.list_customers(db, tenant.id, page, page_size)
    return {"items": items, "total": total, "page": page, "page_size": page_size}


@router.post("/customers", response_model=CustomerResponse, status_code=201)
async def create_customer(data: CustomerCreate, ctx: CurrentTenantContext, db: AsyncSession = Depends(get_db)):
    user, tenant, _ = ctx
    return await service.create_customer(db, tenant.id, data, actor_user_id=user.id)


@router.get("/customers/{customer_id}", response_model=CustomerResponse)
async def get_customer(customer_id: UUID, ctx: CurrentTenantContext, db: AsyncSession = Depends(get_db)):
    _, tenant, _ = ctx
    return await service.get_customer(db, tenant.id, customer_id)


@router.patch("/customers/{customer_id}", response_model=CustomerResponse)
async def update_customer(customer_id: UUID, data: CustomerUpdate, ctx: CurrentTenantContext, db: AsyncSession = Depends(get_db)):
    user, tenant, _ = ctx
    return await service.update_customer(db, tenant.id, customer_id, data, actor_user_id=user.id)


@router.delete("/customers/{customer_id}", status_code=204)
async def delete_customer(customer_id: UUID, ctx: CurrentTenantContext, db: AsyncSession = Depends(get_db)):
    user, tenant, _ = ctx
    await service.delete_customer(db, tenant.id, customer_id, actor_user_id=user.id)


@router.post("/deals", response_model=DealResponse, status_code=201)
async def create_deal(data: DealCreate, ctx: CurrentTenantContext, db: AsyncSession = Depends(get_db)):
    user, tenant, _ = ctx
    return await service.create_deal(db, tenant.id, data, user.id)


@router.get("/deals/{deal_id}", response_model=DealResponse)
async def get_deal(deal_id: UUID, ctx: CurrentTenantContext, db: AsyncSession = Depends(get_db)):
    _, tenant, _ = ctx
    return await service.get_deal(db, tenant.id, deal_id)


@router.patch("/deals/{deal_id}", response_model=DealResponse)
async def update_deal(deal_id: UUID, data: DealUpdate, ctx: CurrentTenantContext, db: AsyncSession = Depends(get_db)):
    user, tenant, _ = ctx
    return await service.update_deal(db, tenant.id, deal_id, data, user.id)


@router.post("/deals/{deal_id}/move", response_model=DealResponse)
async def move_deal(
    deal_id: UUID,
    data: MoveDealRequest,
    ctx: CurrentTenantContext,
    db: AsyncSession = Depends(get_db),
):
    user, tenant, _ = ctx
    return await service.move_deal(db, tenant.id, deal_id, data.stage, data.stage_order, user.id)


@router.post("/deals/{deal_id}/move-stage", response_model=DealResponse)
async def move_deal_by_stage_id(
    deal_id: UUID,
    data: MoveDealRequestV2,
    ctx: CurrentTenantContext,
    db: AsyncSession = Depends(get_db),
):
    user, tenant, _ = ctx
    return await pipeline_service.move_deal_by_stage(
        db,
        tenant.id,
        deal_id,
        stage_id=data.stage_id,
        stage_name=data.stage,
        stage_order=data.stage_order,
        user_id=user.id,
    )


class NoteRequest(BaseModel):
    note: str


@router.post("/deals/{deal_id}/notes", response_model=DealActivityResponse, status_code=201)
async def add_note(deal_id: UUID, data: NoteRequest, ctx: CurrentTenantContext, db: AsyncSession = Depends(get_db)):
    user, tenant, _ = ctx
    return await service.add_note(db, tenant.id, deal_id, data.note, user.id)
