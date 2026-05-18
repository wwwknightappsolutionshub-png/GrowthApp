"""Super Admin — Scraper Tasks CRUD + scheduling.

GET    /api/admin/scraper_tasks/
GET    /api/admin/scraper_tasks/{task_id}
POST   /api/admin/scraper_tasks/
PUT    /api/admin/scraper_tasks/{task_id}
DELETE /api/admin/scraper_tasks/{task_id}
POST   /api/admin/scraper_tasks/{task_id}/run
"""
from __future__ import annotations

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import SuperAdmin
from app.modules.ai_scraper.models import AiScraperTask
from app.modules.ai_scraper import service as svc

router = APIRouter(prefix="/api/admin/scraper_tasks", tags=["Admin — Scraper Tasks"])


class TaskCreate(BaseModel):
    source_id: uuid.UUID
    name: str
    aggression_level: str = "low"
    cron_expression: Optional[str] = None
    max_pages: int = 5
    is_active: bool = True


class TaskUpdate(BaseModel):
    name: Optional[str] = None
    aggression_level: Optional[str] = None
    cron_expression: Optional[str] = None
    max_pages: Optional[int] = None
    is_active: Optional[bool] = None


@router.get("/")
async def list_tasks(
    _: SuperAdmin,
    db: AsyncSession = Depends(get_db),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    rows = (await db.execute(select(AiScraperTask).order_by(AiScraperTask.created_at.desc()).limit(limit).offset(offset))).scalars().all()
    return [
        {
            "id": str(r.id), "name": r.name, "source_id": str(r.source_id),
            "aggression_level": r.aggression_level, "status": r.status,
            "cron_expression": r.cron_expression, "max_pages": r.max_pages,
            "is_active": r.is_active, "created_at": r.created_at.isoformat(),
        }
        for r in rows
    ]


@router.get("/{task_id}")
async def get_task(task_id: uuid.UUID, _: SuperAdmin, db: AsyncSession = Depends(get_db)):
    t = (await db.execute(select(AiScraperTask).where(AiScraperTask.id == task_id))).scalar_one_or_none()
    if not t:
        raise HTTPException(404, "Task not found")
    return {
        "id": str(t.id), "name": t.name, "source_id": str(t.source_id),
        "aggression_level": t.aggression_level, "status": t.status,
        "cron_expression": t.cron_expression, "max_pages": t.max_pages,
        "is_active": t.is_active, "created_at": t.created_at.isoformat(),
    }


@router.post("/", status_code=201)
async def create_task(body: TaskCreate, _: SuperAdmin, db: AsyncSession = Depends(get_db)):
    t = AiScraperTask(**body.model_dump())
    db.add(t)
    await db.commit()
    await db.refresh(t)
    return {"id": str(t.id), "name": t.name}


@router.put("/{task_id}")
async def update_task(task_id: uuid.UUID, body: TaskUpdate, _: SuperAdmin, db: AsyncSession = Depends(get_db)):
    t = (await db.execute(select(AiScraperTask).where(AiScraperTask.id == task_id))).scalar_one_or_none()
    if not t:
        raise HTTPException(404, "Task not found")
    for k, v in body.model_dump(exclude_none=True).items():
        setattr(t, k, v)
    await db.commit()
    return {"id": str(t.id), "name": t.name}


@router.delete("/{task_id}", status_code=204)
async def delete_task(task_id: uuid.UUID, _: SuperAdmin, db: AsyncSession = Depends(get_db)):
    t = (await db.execute(select(AiScraperTask).where(AiScraperTask.id == task_id))).scalar_one_or_none()
    if not t:
        raise HTTPException(404, "Task not found")
    await db.delete(t)
    await db.commit()


@router.post("/{task_id}/run")
async def run_task(task_id: uuid.UUID, _: SuperAdmin, db: AsyncSession = Depends(get_db)):
    job_id = await svc.trigger_task_run(db, task_id)
    return {"job_id": job_id, "task_id": str(task_id), "status": "queued"}
