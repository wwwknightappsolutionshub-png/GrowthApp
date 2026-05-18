"""Super Admin — Scraper Sources CRUD.

GET    /api/admin/scraper_sources/
GET    /api/admin/scraper_sources/{source_id}
POST   /api/admin/scraper_sources/
PUT    /api/admin/scraper_sources/{source_id}
DELETE /api/admin/scraper_sources/{source_id}
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
from app.modules.ai_scraper.models import AiScraperSource

router = APIRouter(prefix="/api/admin/scraper_sources", tags=["Admin — Scraper Sources"])


class SourceCreate(BaseModel):
    name: str
    url: str
    scraping_type: str = "html"
    category_id: Optional[uuid.UUID] = None
    is_active: bool = True


class SourceUpdate(BaseModel):
    name: Optional[str] = None
    url: Optional[str] = None
    scraping_type: Optional[str] = None
    is_active: Optional[bool] = None


@router.get("/")
async def list_sources(
    _: SuperAdmin,
    db: AsyncSession = Depends(get_db),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    rows = (await db.execute(select(AiScraperSource).order_by(AiScraperSource.created_at.desc()).limit(limit).offset(offset))).scalars().all()
    return [
        {
            "id": str(r.id), "name": r.name, "url": r.url,
            "scraping_type": r.scraping_type, "is_active": r.is_active,
            "created_at": r.created_at.isoformat(),
        }
        for r in rows
    ]


@router.get("/{source_id}")
async def get_source(source_id: uuid.UUID, _: SuperAdmin, db: AsyncSession = Depends(get_db)):
    s = (await db.execute(select(AiScraperSource).where(AiScraperSource.id == source_id))).scalar_one_or_none()
    if not s:
        raise HTTPException(404, "Source not found")
    return {"id": str(s.id), "name": s.name, "url": s.url, "scraping_type": s.scraping_type, "is_active": s.is_active, "created_at": s.created_at.isoformat()}


@router.post("/", status_code=201)
async def create_source(body: SourceCreate, _: SuperAdmin, db: AsyncSession = Depends(get_db)):
    s = AiScraperSource(**body.model_dump())
    db.add(s)
    await db.commit()
    await db.refresh(s)
    return {"id": str(s.id), "name": s.name}


@router.put("/{source_id}")
async def update_source(source_id: uuid.UUID, body: SourceUpdate, _: SuperAdmin, db: AsyncSession = Depends(get_db)):
    s = (await db.execute(select(AiScraperSource).where(AiScraperSource.id == source_id))).scalar_one_or_none()
    if not s:
        raise HTTPException(404, "Source not found")
    for k, v in body.model_dump(exclude_none=True).items():
        setattr(s, k, v)
    await db.commit()
    return {"id": str(s.id), "name": s.name}


@router.delete("/{source_id}", status_code=204)
async def delete_source(source_id: uuid.UUID, _: SuperAdmin, db: AsyncSession = Depends(get_db)):
    s = (await db.execute(select(AiScraperSource).where(AiScraperSource.id == source_id))).scalar_one_or_none()
    if not s:
        raise HTTPException(404, "Source not found")
    await db.delete(s)
    await db.commit()
