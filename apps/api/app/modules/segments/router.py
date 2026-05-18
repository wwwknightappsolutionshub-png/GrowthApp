"""Customer segments REST endpoints."""
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import CurrentTenantContext, OwnerContext
from app.modules.segments import service

router = APIRouter(prefix="/segments", tags=["Segments"])


class SegmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    name: str
    description: str | None
    rules: dict
    size: int
    computed_at: datetime | None
    is_system: bool
    created_at: datetime


class SegmentCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    description: str | None = None
    rules: dict = Field(default_factory=dict)


@router.get("", response_model=list[SegmentResponse])
async def list_segments(ctx: CurrentTenantContext, db: AsyncSession = Depends(get_db)):
    _, tenant, _ = ctx
    rows = await service.list_segments(db, tenant.id)
    if not rows:
        # First call seeds the default system segments — saves a bootstrap step.
        await service.seed_system_segments(db, tenant.id)
        rows = await service.list_segments(db, tenant.id)
    return rows


@router.post("", response_model=SegmentResponse, status_code=201)
async def create_segment(
    data: SegmentCreateRequest, ctx: OwnerContext, db: AsyncSession = Depends(get_db)
):
    user, tenant, _ = ctx
    return await service.create_segment(
        db,
        tenant.id,
        name=data.name,
        description=data.description,
        rules=data.rules,
        created_by=user.id,
    )


@router.post("/recompute", response_model=dict)
async def recompute(ctx: OwnerContext, db: AsyncSession = Depends(get_db)):
    _, tenant, _ = ctx
    count = await service.recompute_all(db, tenant.id)
    return {"recomputed": count}
