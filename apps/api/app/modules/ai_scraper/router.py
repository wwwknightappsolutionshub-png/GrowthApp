"""AI Scraper router (super-admin only).

Mounted at `/api/superadmin/ai-scraper` per spec.
Every route requires `is_superadmin = True`.
"""
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import SuperAdmin
from app.modules.ai_scraper import schemas as s
from app.modules.ai_scraper import service as svc
from app.modules.ai_scraper.models import (
    AiScraperResult,
    AiScraperSettings,
    AiScraperSource,
    AiScraperTask,
)

router = APIRouter(prefix="/superadmin/ai-scraper", tags=["AI Scraper"])

# SuperAdmin is already Annotated[User, Depends(require_superadmin)]
SuperAdminDep = SuperAdmin


# ── Categories ──────────────────────────────────────────────────────────────


@router.get("/categories", response_model=list[s.CategoryResponse])
async def list_categories(_: SuperAdminDep, db: AsyncSession = Depends(get_db)):
    return await svc.list_categories(db)


@router.post("/categories", response_model=s.CategoryResponse, status_code=201)
async def create_category(
    body: s.CategoryCreate, _: SuperAdminDep, db: AsyncSession = Depends(get_db)
):
    return await svc.create_category(db, body)


@router.get("/categories/{category_id}", response_model=s.CategoryResponse)
async def get_category(
    category_id: UUID, _: SuperAdminDep, db: AsyncSession = Depends(get_db)
):
    return await svc.get_category(db, category_id)


@router.patch("/categories/{category_id}", response_model=s.CategoryResponse)
async def patch_category(
    category_id: UUID,
    body: s.CategoryUpdate,
    _: SuperAdminDep,
    db: AsyncSession = Depends(get_db),
):
    return await svc.update_category(db, category_id, body)


@router.delete("/categories/{category_id}", status_code=204)
async def delete_category(
    category_id: UUID, _: SuperAdminDep, db: AsyncSession = Depends(get_db)
):
    await svc.delete_category(db, category_id)


# ── Sources ─────────────────────────────────────────────────────────────────


@router.get("/sources", response_model=list[s.SourceResponse])
async def list_sources(
    _: SuperAdminDep,
    db: AsyncSession = Depends(get_db),
    active: bool | None = Query(default=None),
    category_id: UUID | None = Query(default=None),
):
    return await svc.list_sources(db, active=active, category_id=category_id)


@router.post("/sources", response_model=s.SourceResponse, status_code=201)
async def create_source(
    body: s.SourceCreate, _: SuperAdminDep, db: AsyncSession = Depends(get_db)
):
    return await svc.create_source(db, body)


@router.get("/sources/{source_id}", response_model=s.SourceResponse)
async def get_source(
    source_id: UUID, _: SuperAdminDep, db: AsyncSession = Depends(get_db)
):
    return await svc.get_source(db, source_id)


@router.patch("/sources/{source_id}", response_model=s.SourceResponse)
async def patch_source(
    source_id: UUID,
    body: s.SourceUpdate,
    _: SuperAdminDep,
    db: AsyncSession = Depends(get_db),
):
    return await svc.update_source(db, source_id, body)


@router.delete("/sources/{source_id}", status_code=204)
async def delete_source(
    source_id: UUID, _: SuperAdminDep, db: AsyncSession = Depends(get_db)
):
    await svc.delete_source(db, source_id)


# ── Tasks ───────────────────────────────────────────────────────────────────


@router.get("/tasks", response_model=list[s.TaskRunnerRow])
async def list_tasks(
    _: SuperAdminDep,
    db: AsyncSession = Depends(get_db),
    source_id: UUID | None = Query(default=None),
    status: str | None = Query(default=None),
):
    items = await svc.list_tasks(db, source_id=source_id, status=status)
    rows: list[s.TaskRunnerRow] = []
    for t in items:
        _t, count = await svc.task_with_lead_count(db, t)
        rows.append(
            s.TaskRunnerRow(
                id=t.id,
                source_id=t.source_id,
                category_id=t.category_id,
                aggression_level=t.aggression_level,
                frequency=t.frequency,
                last_run=t.last_run,
                next_run=t.next_run,
                status=t.status,
                total_leads_extracted=count,
            )
        )
    return rows


@router.post("/tasks", response_model=s.TaskResponse, status_code=201)
async def create_task(
    body: s.TaskCreate, _: SuperAdminDep, db: AsyncSession = Depends(get_db)
):
    return await svc.create_task(db, body)


@router.get("/tasks/{task_id}", response_model=s.TaskResponse)
async def get_task(task_id: UUID, _: SuperAdminDep, db: AsyncSession = Depends(get_db)):
    return await svc.get_task(db, task_id)


@router.patch("/tasks/{task_id}", response_model=s.TaskResponse)
async def patch_task(
    task_id: UUID,
    body: s.TaskUpdate,
    _: SuperAdminDep,
    db: AsyncSession = Depends(get_db),
):
    return await svc.update_task(db, task_id, body)


@router.delete("/tasks/{task_id}", status_code=204)
async def delete_task(
    task_id: UUID, _: SuperAdminDep, db: AsyncSession = Depends(get_db)
):
    await svc.delete_task(db, task_id)


@router.post("/tasks/{task_id}/run", response_model=s.TaskRunResponse)
async def run_task(
    task_id: UUID, _: SuperAdminDep, db: AsyncSession = Depends(get_db)
):
    task, enqueued = await svc.trigger_task_run(db, task_id)
    return s.TaskRunResponse(
        task_id=task.id,
        enqueued=enqueued,
        message="Task scheduled" if enqueued else "Task marked running (queue offline)",
    )


# ── Results ─────────────────────────────────────────────────────────────────


@router.get("/results", response_model=list[s.ResultResponse])
async def list_results(
    _: SuperAdminDep,
    db: AsyncSession = Depends(get_db),
    task_id: UUID | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
):
    return await svc.list_results(db, task_id=task_id, limit=limit)


@router.get("/results/{result_id}", response_model=s.ResultResponse)
async def get_result(
    result_id: UUID, _: SuperAdminDep, db: AsyncSession = Depends(get_db)
):
    return await svc.get_result(db, result_id)


# ── Settings ────────────────────────────────────────────────────────────────


@router.get("/settings", response_model=s.SettingsResponse)
async def get_settings(_: SuperAdminDep, db: AsyncSession = Depends(get_db)):
    return await svc.get_settings(db)


@router.put("/settings", response_model=s.SettingsResponse)
async def put_settings(
    body: s.SettingsBody, _: SuperAdminDep, db: AsyncSession = Depends(get_db)
):
    return await svc.update_settings(db, body)


@router.post("/seed-catalog")
async def seed_catalog(
    _: SuperAdminDep,
    db: AsyncSession = Depends(get_db),
    force: bool = Query(default=False),
):
    """Seed default trade sources, territories, marketplace categories, overnight tasks."""
    from app.modules.ai_scraper.seed_catalog import seed_lead_factory_catalog
    from app.modules.lead_marketplace.pool import get_marketplace_pool_tenant_id

    await get_marketplace_pool_tenant_id(db)
    stats = await seed_lead_factory_catalog(db, force=force)
    return {"ok": True, "stats": stats}


__all__ = ["router"]

