"""Super Admin — Tenant Management.

GET    /api/admin/tenants/
GET    /api/admin/tenants/{tenant_id}
POST   /api/admin/tenants/
PUT    /api/admin/tenants/{tenant_id}
DELETE /api/admin/tenants/{tenant_id}
POST   /api/admin/tenants/{tenant_id}/impersonate
POST   /api/admin/tenants/{tenant_id}/toggle-active
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
from app.modules.admin.deletion import active_tenants_filter, delete_tenant
from app.modules.tenants.models import Tenant

router = APIRouter(prefix="/api/admin/tenants", tags=["Admin — Tenants"])


class TenantCreate(BaseModel):
    name: str
    slug: str
    business_type: str
    postcode: str
    email: Optional[str] = None
    phone: Optional[str] = None
    country: str = "GB"


class TenantUpdate(BaseModel):
    name: Optional[str] = None
    business_type: Optional[str] = None
    postcode: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    is_active: Optional[bool] = None


@router.get("/")
async def list_tenants(
    _: SuperAdmin,
    db: AsyncSession = Depends(get_db),
    search: Optional[str] = Query(None),
    active: Optional[bool] = Query(None),
    include_archived: bool = Query(False),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    q = select(Tenant).order_by(Tenant.created_at.desc())
    if not include_archived:
        q = q.where(active_tenants_filter())
    if search:
        q = q.where(Tenant.name.ilike(f"%{search}%") | Tenant.slug.ilike(f"%{search}%"))
    if active is not None:
        q = q.where(Tenant.is_active == active)
    rows = (await db.execute(q.limit(limit).offset(offset))).scalars().all()
    return [
        {
            "id": str(r.id), "name": r.name, "slug": r.slug,
            "business_type": r.business_type, "is_active": r.is_active,
            "email": r.email, "phone": r.phone, "postcode": r.postcode,
            "created_at": r.created_at.isoformat(),
        }
        for r in rows
    ]


@router.get("/{tenant_id}")
async def get_tenant(tenant_id: uuid.UUID, _: SuperAdmin, db: AsyncSession = Depends(get_db)):
    t = (await db.execute(select(Tenant).where(Tenant.id == tenant_id))).scalar_one_or_none()
    if not t:
        raise HTTPException(404, "Tenant not found")
    return {
        "id": str(t.id), "name": t.name, "slug": t.slug,
        "business_type": t.business_type, "is_active": t.is_active,
        "email": t.email, "phone": t.phone, "postcode": t.postcode,
        "country": t.country, "plan_id": str(t.plan_id) if t.plan_id else None,
        "created_at": t.created_at.isoformat(), "updated_at": t.updated_at.isoformat(),
    }


@router.post("/", status_code=201)
async def create_tenant(body: TenantCreate, _: SuperAdmin, db: AsyncSession = Depends(get_db)):
    t = Tenant(**body.model_dump())
    db.add(t)
    await db.commit()
    await db.refresh(t)
    return {"id": str(t.id), "name": t.name, "slug": t.slug}


@router.put("/{tenant_id}")
async def update_tenant(tenant_id: uuid.UUID, body: TenantUpdate, _: SuperAdmin, db: AsyncSession = Depends(get_db)):
    t = (await db.execute(select(Tenant).where(Tenant.id == tenant_id))).scalar_one_or_none()
    if not t:
        raise HTTPException(404, "Tenant not found")
    for k, v in body.model_dump(exclude_none=True).items():
        setattr(t, k, v)
    await db.commit()
    await db.refresh(t)
    return {"id": str(t.id), "name": t.name, "is_active": t.is_active}


@router.delete("/{tenant_id}")
async def delete_tenant_route(
    tenant_id: uuid.UUID,
    _: SuperAdmin,
    db: AsyncSession = Depends(get_db),
    permanent: bool = Query(False),
):
    out = await delete_tenant(db, tenant_id, permanent=permanent)
    return {"ok": True, "message": out["message"]}


@router.post("/{tenant_id}/impersonate")
async def impersonate_tenant(tenant_id: uuid.UUID, admin: SuperAdmin, db: AsyncSession = Depends(get_db)):
    """Return a short-lived impersonation token for the tenant context."""
    t = (await db.execute(select(Tenant).where(Tenant.id == tenant_id))).scalar_one_or_none()
    if not t:
        raise HTTPException(404, "Tenant not found")
    from app.core.security import create_access_token
    token = create_access_token(
        subject=str(admin.id),
        tenant_id=t.id,
        role="owner",
    )
    return {"access_token": token, "tenant_id": str(t.id), "tenant_name": t.name}


@router.post("/{tenant_id}/addons/accounting")
async def set_accounting_addon(
    tenant_id: uuid.UUID,
    body: dict,
    admin: SuperAdmin,
    db: AsyncSession = Depends(get_db),
):
    """Manually grant or revoke the Accounting add-on for a tenant."""
    from app.modules.accounting import service as accounting_service
    from app.modules.accounting.schemas import AdminAddonAction

    payload = AdminAddonAction(**body)
    if payload.action == "grant":
        row = await accounting_service.grant_addon(
            db, tenant_id, granted_by=admin.id, expires_at=payload.expires_at
        )
        return {"ok": True, "status": row.status, "feature_code": row.feature_code}
    if payload.action == "revoke":
        await accounting_service.revoke_addon(db, tenant_id)
        return {"ok": True, "status": "canceled"}
    raise HTTPException(422, "action must be grant or revoke")


@router.post("/{tenant_id}/addons/industry/{feature_code}")
async def set_industry_addon(
    tenant_id: uuid.UUID,
    feature_code: str,
    body: dict,
    admin: SuperAdmin,
    db: AsyncSession = Depends(get_db),
):
    """Grant or revoke industry_booking | industry_billing | industry_crm."""
    from app.modules.addons.common.constants import INDUSTRY_FEATURE_CODES
    from app.modules.addons.common import service as addons_service

    if feature_code not in INDUSTRY_FEATURE_CODES:
        raise HTTPException(422, f"feature_code must be one of: {', '.join(sorted(INDUSTRY_FEATURE_CODES))}")
    action = body.get("action")
    if action == "grant":
        row = await addons_service.grant_addon(db, tenant_id, feature_code, granted_by=admin.id)
        return {"ok": True, "status": row.status, "feature_code": row.feature_code}
    if action == "revoke":
        await addons_service.revoke_addon(db, tenant_id, feature_code)
        return {"ok": True, "status": "canceled", "feature_code": feature_code}
    raise HTTPException(422, "action must be grant or revoke")


@router.post("/{tenant_id}/toggle-active")
async def toggle_active(tenant_id: uuid.UUID, _: SuperAdmin, db: AsyncSession = Depends(get_db)):
    t = (await db.execute(select(Tenant).where(Tenant.id == tenant_id))).scalar_one_or_none()
    if not t:
        raise HTTPException(404, "Tenant not found")
    t.is_active = not t.is_active
    await db.commit()
    return {"id": str(t.id), "is_active": t.is_active}
