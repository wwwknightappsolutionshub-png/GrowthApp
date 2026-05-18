"""Super Admin — Lead Marketplace Management.

GET    /api/admin/marketplace/
GET    /api/admin/marketplace/{item_id}
POST   /api/admin/marketplace/
PUT    /api/admin/marketplace/{item_id}
DELETE /api/admin/marketplace/{item_id}
POST   /api/admin/marketplace/{item_id}/assign
POST   /api/admin/marketplace/{item_id}/release
POST   /api/admin/marketplace/{item_id}/distribute
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
from app.modules.lead_marketplace.models import LeadMarketplace, LeadCategory, LeadTerritory
from app.modules.lead_marketplace import service as svc

router = APIRouter(prefix="/api/admin/marketplace", tags=["Admin — Marketplace"])


class ItemCreate(BaseModel):
    lead_id: uuid.UUID
    category_id: uuid.UUID
    territory_id: uuid.UUID
    ai_score: int = 0
    price: float = 0.0
    exclusivity: str = "shared"


class ItemUpdate(BaseModel):
    price: Optional[float] = None
    exclusivity: Optional[str] = None
    status: Optional[str] = None


class AssignBody(BaseModel):
    tenant_id: uuid.UUID


@router.get("/")
async def list_items(
    _: SuperAdmin,
    db: AsyncSession = Depends(get_db),
    status: Optional[str] = Query(None),
    category_id: Optional[uuid.UUID] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    q = select(LeadMarketplace).order_by(LeadMarketplace.created_at.desc())
    if status:
        q = q.where(LeadMarketplace.status == status)
    if category_id:
        q = q.where(LeadMarketplace.category_id == category_id)
    rows = (await db.execute(q.limit(limit).offset(offset))).scalars().all()
    return [
        {
            "id": str(r.id), "lead_id": str(r.lead_id), "ai_score": r.ai_score,
            "price": float(r.price), "exclusivity": r.exclusivity, "status": r.status,
            "assigned_tenant_id": str(r.assigned_tenant_id) if r.assigned_tenant_id else None,
            "created_at": r.created_at.isoformat(),
        }
        for r in rows
    ]


@router.get("/{item_id}")
async def get_item(item_id: uuid.UUID, _: SuperAdmin, db: AsyncSession = Depends(get_db)):
    item = (await db.execute(select(LeadMarketplace).where(LeadMarketplace.id == item_id))).scalar_one_or_none()
    if not item:
        raise HTTPException(404, "Item not found")
    return {
        "id": str(item.id), "lead_id": str(item.lead_id), "ai_score": item.ai_score,
        "price": float(item.price), "exclusivity": item.exclusivity, "status": item.status,
        "category_id": str(item.category_id), "territory_id": str(item.territory_id),
        "assigned_tenant_id": str(item.assigned_tenant_id) if item.assigned_tenant_id else None,
        "created_at": item.created_at.isoformat(), "updated_at": item.updated_at.isoformat(),
    }


@router.post("/", status_code=201)
async def create_item(body: ItemCreate, _: SuperAdmin, db: AsyncSession = Depends(get_db)):
    item = LeadMarketplace(**body.model_dump())
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return {"id": str(item.id)}


@router.put("/{item_id}")
async def update_item(item_id: uuid.UUID, body: ItemUpdate, _: SuperAdmin, db: AsyncSession = Depends(get_db)):
    item = (await db.execute(select(LeadMarketplace).where(LeadMarketplace.id == item_id))).scalar_one_or_none()
    if not item:
        raise HTTPException(404, "Item not found")
    for k, v in body.model_dump(exclude_none=True).items():
        setattr(item, k, v)
    await db.commit()
    return {"id": str(item.id), "status": item.status}


@router.delete("/{item_id}", status_code=204)
async def delete_item(item_id: uuid.UUID, _: SuperAdmin, db: AsyncSession = Depends(get_db)):
    item = (await db.execute(select(LeadMarketplace).where(LeadMarketplace.id == item_id))).scalar_one_or_none()
    if not item:
        raise HTTPException(404, "Item not found")
    await db.delete(item)
    await db.commit()


@router.post("/{item_id}/assign")
async def assign_item(item_id: uuid.UUID, body: AssignBody, _: SuperAdmin, db: AsyncSession = Depends(get_db)):
    item = (await db.execute(select(LeadMarketplace).where(LeadMarketplace.id == item_id))).scalar_one_or_none()
    if not item:
        raise HTTPException(404, "Item not found")
    item.assigned_tenant_id = body.tenant_id
    item.status = "reserved"
    await db.commit()
    return {"id": str(item.id), "status": item.status, "assigned_tenant_id": str(item.assigned_tenant_id)}


@router.post("/{item_id}/release")
async def release_item(item_id: uuid.UUID, _: SuperAdmin, db: AsyncSession = Depends(get_db)):
    item = (await db.execute(select(LeadMarketplace).where(LeadMarketplace.id == item_id))).scalar_one_or_none()
    if not item:
        raise HTTPException(404, "Item not found")
    item.assigned_tenant_id = None
    item.status = "available"
    await db.commit()
    return {"id": str(item.id), "status": item.status}


@router.post("/{item_id}/distribute")
async def distribute_item(item_id: uuid.UUID, _: SuperAdmin, db: AsyncSession = Depends(get_db)):
    result = await svc.run_distribution(db, item_id)
    if not result:
        raise HTTPException(422, "No eligible tenant found for distribution")
    return result
