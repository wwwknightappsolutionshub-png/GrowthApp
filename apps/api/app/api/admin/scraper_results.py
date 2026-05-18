"""Super Admin — Scraper Results viewer.

GET    /api/admin/scraper_results/
GET    /api/admin/scraper_results/{result_id}
POST   /api/admin/scraper_results/
PUT    /api/admin/scraper_results/{result_id}
DELETE /api/admin/scraper_results/{result_id}
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
from app.modules.ai_scraper.models import AiScraperResult

router = APIRouter(prefix="/api/admin/scraper_results", tags=["Admin — Scraper Results"])


class ResultCreate(BaseModel):
    task_id: uuid.UUID
    url: str
    raw_content: Optional[str] = None
    extracted_json: Optional[dict] = None
    ai_score: int = 0
    status: str = "pending"


class ResultUpdate(BaseModel):
    status: Optional[str] = None
    ai_score: Optional[int] = None


@router.get("/")
async def list_results(
    _: SuperAdmin,
    db: AsyncSession = Depends(get_db),
    task_id: Optional[uuid.UUID] = Query(None),
    status: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    q = select(AiScraperResult).order_by(AiScraperResult.created_at.desc())
    if task_id:
        q = q.where(AiScraperResult.task_id == task_id)
    if status:
        q = q.where(AiScraperResult.status == status)
    rows = (await db.execute(q.limit(limit).offset(offset))).scalars().all()
    return [
        {
            "id": str(r.id), "task_id": str(r.task_id), "url": r.url,
            "ai_score": r.ai_score, "status": r.status,
            "created_at": r.created_at.isoformat(),
            "extracted_json": r.extracted_json,
        }
        for r in rows
    ]


@router.get("/{result_id}")
async def get_result(result_id: uuid.UUID, _: SuperAdmin, db: AsyncSession = Depends(get_db)):
    r = (await db.execute(select(AiScraperResult).where(AiScraperResult.id == result_id))).scalar_one_or_none()
    if not r:
        raise HTTPException(404, "Result not found")
    return {
        "id": str(r.id), "task_id": str(r.task_id), "url": r.url,
        "raw_content": r.raw_content, "extracted_json": r.extracted_json,
        "ai_score": r.ai_score, "status": r.status, "created_at": r.created_at.isoformat(),
    }


@router.post("/", status_code=201)
async def create_result(body: ResultCreate, _: SuperAdmin, db: AsyncSession = Depends(get_db)):
    r = AiScraperResult(**body.model_dump())
    db.add(r)
    await db.commit()
    await db.refresh(r)
    return {"id": str(r.id)}


@router.put("/{result_id}")
async def update_result(result_id: uuid.UUID, body: ResultUpdate, _: SuperAdmin, db: AsyncSession = Depends(get_db)):
    r = (await db.execute(select(AiScraperResult).where(AiScraperResult.id == result_id))).scalar_one_or_none()
    if not r:
        raise HTTPException(404, "Result not found")
    for k, v in body.model_dump(exclude_none=True).items():
        setattr(r, k, v)
    await db.commit()
    return {"id": str(r.id), "status": r.status}


@router.delete("/{result_id}", status_code=204)
async def delete_result(result_id: uuid.UUID, _: SuperAdmin, db: AsyncSession = Depends(get_db)):
    r = (await db.execute(select(AiScraperResult).where(AiScraperResult.id == result_id))).scalar_one_or_none()
    if not r:
        raise HTTPException(404, "Result not found")
    await db.delete(r)
    await db.commit()
