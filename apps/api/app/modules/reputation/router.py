from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.dependencies import CurrentTenantContext
from app.modules.reputation import service
from app.modules.reputation.schemas import ReputationDashboard, ReviewListResponse

router = APIRouter(prefix="/reputation", tags=["Reputation"])


@router.get("/dashboard", response_model=ReputationDashboard)
async def get_dashboard(ctx: CurrentTenantContext, db: AsyncSession = Depends(get_db)):
    _, tenant, _ = ctx
    return await service.get_dashboard(db, tenant.id)


@router.get("/reviews", response_model=ReviewListResponse)
async def list_reviews(ctx: CurrentTenantContext, db: AsyncSession = Depends(get_db), page: int = Query(1, ge=1)):
    _, tenant, _ = ctx
    items, total = await service.list_reviews(db, tenant.id, page)
    return {"items": items, "total": total}
