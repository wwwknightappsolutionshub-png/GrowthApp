"""Task REST endpoints.

All operations are tenant-scoped (RLS-enforced) and audit-logged.
"""
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import CurrentTenantContext
from app.modules.tasks import service
from app.modules.tasks.schemas import (
    TaskBoardResponse,
    TaskCreate,
    TaskListResponse,
    TaskMove,
    TaskResponse,
    TaskUpdate,
)

router = APIRouter(prefix="/tasks", tags=["Tasks"])


@router.get("", response_model=TaskListResponse)
async def list_tasks(
    ctx: CurrentTenantContext,
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    status: str | None = Query(None),
    assigned_user_id: UUID | None = Query(None),
    related_type: str | None = Query(None),
    related_id: UUID | None = Query(None),
    q: str | None = Query(None, description="Substring search over title"),
):
    _, tenant, _ = ctx
    items, total = await service.list_tasks(
        db,
        tenant.id,
        page=page,
        page_size=page_size,
        status=status,
        assigned_user_id=assigned_user_id,
        related_type=related_type,
        related_id=related_id,
        q=q,
    )
    return {"items": items, "total": total, "page": page, "page_size": page_size}


@router.get("/board", response_model=TaskBoardResponse)
async def get_board(ctx: CurrentTenantContext, db: AsyncSession = Depends(get_db)):
    _, tenant, _ = ctx
    return await service.get_board(db, tenant.id)


@router.post("", response_model=TaskResponse, status_code=201)
async def create_task(
    data: TaskCreate, ctx: CurrentTenantContext, db: AsyncSession = Depends(get_db)
):
    user, tenant, _ = ctx
    return await service.create_task(db, tenant.id, data, user_id=user.id)


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(task_id: UUID, ctx: CurrentTenantContext, db: AsyncSession = Depends(get_db)):
    _, tenant, _ = ctx
    return await service.get_task(db, tenant.id, task_id)


@router.patch("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: UUID,
    data: TaskUpdate,
    ctx: CurrentTenantContext,
    db: AsyncSession = Depends(get_db),
):
    user, tenant, _ = ctx
    return await service.update_task(db, tenant.id, task_id, data, user_id=user.id)


@router.post("/{task_id}/move", response_model=TaskResponse)
async def move_task(
    task_id: UUID,
    move: TaskMove,
    ctx: CurrentTenantContext,
    db: AsyncSession = Depends(get_db),
):
    user, tenant, _ = ctx
    return await service.move_task(db, tenant.id, task_id, move, user_id=user.id)


@router.delete("/{task_id}", status_code=204)
async def delete_task(
    task_id: UUID,
    ctx: CurrentTenantContext,
    db: AsyncSession = Depends(get_db),
):
    user, tenant, _ = ctx
    await service.delete_task(db, tenant.id, task_id, user_id=user.id)
    return None
