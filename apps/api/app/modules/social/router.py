from uuid import UUID
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.dependencies import CurrentTenantContext
from app.modules.social import service
from app.modules.social.schemas import SocialPostResponse, SocialPostUpdate, SocialAccountResponse
from app.modules.auth.schemas import MessageResponse

router = APIRouter(prefix="/social", tags=["Social"])


@router.get("/posts", response_model=dict)
async def list_posts(ctx: CurrentTenantContext, db: AsyncSession = Depends(get_db), page: int = Query(1, ge=1)):
    _, tenant, _ = ctx
    items, total = await service.list_posts(db, tenant.id, page)
    return {"items": items, "total": total}


@router.get("/posts/{post_id}", response_model=SocialPostResponse)
async def get_post(post_id: UUID, ctx: CurrentTenantContext, db: AsyncSession = Depends(get_db)):
    _, tenant, _ = ctx
    return await service.get_post(db, tenant.id, post_id)


@router.patch("/posts/{post_id}", response_model=SocialPostResponse)
async def update_post(post_id: UUID, data: SocialPostUpdate, ctx: CurrentTenantContext, db: AsyncSession = Depends(get_db)):
    _, tenant, _ = ctx
    return await service.update_post(db, tenant.id, post_id, data)


@router.post("/posts/{post_id}/approve", response_model=SocialPostResponse)
async def approve_post(post_id: UUID, ctx: CurrentTenantContext, db: AsyncSession = Depends(get_db)):
    _, tenant, _ = ctx
    return await service.approve_and_publish(db, tenant.id, post_id)


@router.get("/accounts", response_model=list[SocialAccountResponse])
async def list_accounts(ctx: CurrentTenantContext, db: AsyncSession = Depends(get_db)):
    _, tenant, _ = ctx
    return await service.list_accounts(db, tenant.id)
