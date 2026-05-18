"""Super Admin — Communication Hub.

Templates:
  GET    /api/admin/communications/templates
  GET    /api/admin/communications/templates/{template_id}
  POST   /api/admin/communications/templates
  PUT    /api/admin/communications/templates/{template_id}
  DELETE /api/admin/communications/templates/{template_id}

Broadcast:
  GET    /api/admin/communications/broadcasts
  POST   /api/admin/communications/broadcasts
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import SuperAdmin
from app.core.rbac import CommTemplate, Broadcast

router = APIRouter(prefix="/api/admin/communications", tags=["Admin — Communications"])


class TemplateCreate(BaseModel):
    name: str
    channel: str  # email | sms | whatsapp
    subject: Optional[str] = None
    body: str
    is_active: bool = True


class TemplateUpdate(BaseModel):
    name: Optional[str] = None
    subject: Optional[str] = None
    body: Optional[str] = None
    is_active: Optional[bool] = None


class BroadcastCreate(BaseModel):
    name: str
    channel: str
    template_id: Optional[uuid.UUID] = None
    body: str
    target_filter: dict = {}
    scheduled_at: Optional[datetime] = None


@router.get("/templates")
async def list_templates(
    _: SuperAdmin,
    db: AsyncSession = Depends(get_db),
    channel: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    q = select(CommTemplate).order_by(CommTemplate.created_at.desc())
    if channel:
        q = q.where(CommTemplate.channel == channel)
    rows = (await db.execute(q.limit(limit).offset(offset))).scalars().all()
    return [
        {"id": str(r.id), "name": r.name, "channel": r.channel, "subject": r.subject, "is_active": r.is_active, "created_at": r.created_at.isoformat()}
        for r in rows
    ]


@router.get("/templates/{template_id}")
async def get_template(template_id: uuid.UUID, _: SuperAdmin, db: AsyncSession = Depends(get_db)):
    t = (await db.execute(select(CommTemplate).where(CommTemplate.id == template_id))).scalar_one_or_none()
    if not t:
        raise HTTPException(404, "Template not found")
    return {"id": str(t.id), "name": t.name, "channel": t.channel, "subject": t.subject, "body": t.body, "is_active": t.is_active}


@router.post("/templates", status_code=201)
async def create_template(body: TemplateCreate, _: SuperAdmin, db: AsyncSession = Depends(get_db)):
    t = CommTemplate(**body.model_dump())
    db.add(t)
    await db.commit()
    await db.refresh(t)
    return {"id": str(t.id), "name": t.name}


@router.put("/templates/{template_id}")
async def update_template(template_id: uuid.UUID, body: TemplateUpdate, _: SuperAdmin, db: AsyncSession = Depends(get_db)):
    t = (await db.execute(select(CommTemplate).where(CommTemplate.id == template_id))).scalar_one_or_none()
    if not t:
        raise HTTPException(404, "Template not found")
    for k, v in body.model_dump(exclude_none=True).items():
        setattr(t, k, v)
    await db.commit()
    return {"id": str(t.id), "name": t.name}


@router.delete("/templates/{template_id}", status_code=204)
async def delete_template(template_id: uuid.UUID, _: SuperAdmin, db: AsyncSession = Depends(get_db)):
    t = (await db.execute(select(CommTemplate).where(CommTemplate.id == template_id))).scalar_one_or_none()
    if not t:
        raise HTTPException(404, "Template not found")
    await db.delete(t)
    await db.commit()


@router.get("/broadcasts")
async def list_broadcasts(
    _: SuperAdmin,
    db: AsyncSession = Depends(get_db),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    rows = (await db.execute(select(Broadcast).order_by(Broadcast.created_at.desc()).limit(limit).offset(offset))).scalars().all()
    return [
        {"id": str(r.id), "name": r.name, "channel": r.channel, "status": r.status, "recipient_count": r.recipient_count, "created_at": r.created_at.isoformat()}
        for r in rows
    ]


@router.post("/broadcasts", status_code=201)
async def create_broadcast(body: BroadcastCreate, _: SuperAdmin, db: AsyncSession = Depends(get_db)):
    b = Broadcast(
        name=body.name, channel=body.channel, template_id=body.template_id,
        body=body.body, target_filter=body.target_filter,
        scheduled_at=body.scheduled_at, status="pending", recipient_count=0,
    )
    db.add(b)
    await db.commit()
    await db.refresh(b)
    return {"id": str(b.id), "name": b.name, "status": b.status}
