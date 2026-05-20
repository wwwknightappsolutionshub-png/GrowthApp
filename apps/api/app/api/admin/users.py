"""Super Admin — CRM & User Management.

Admin Users:
  GET    /api/admin/users/
  GET    /api/admin/users/{user_id}
  POST   /api/admin/users/
  PUT    /api/admin/users/{user_id}
  DELETE /api/admin/users/{user_id}

Roles:
  GET    /api/admin/users/roles
  POST   /api/admin/users/roles
  DELETE /api/admin/users/roles/{role_id}

Activity Logs:
  GET    /api/admin/users/activity
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
from app.modules.admin.deletion import active_users_filter, delete_platform_user
from app.modules.auth.models import User
from app.core.rbac import AdminRole, AdminActivityLog

router = APIRouter(prefix="/api/admin/users", tags=["Admin — Users"])


class UserCreate(BaseModel):
    email: str
    full_name: str
    is_superadmin: bool = False
    admin_role: Optional[str] = None


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    is_superadmin: Optional[bool] = None
    is_active: Optional[bool] = None
    admin_role: Optional[str] = None


class RoleCreate(BaseModel):
    name: str
    permissions: list[str] = []
    description: str = ""


@router.get("/")
async def list_users(
    _: SuperAdmin,
    db: AsyncSession = Depends(get_db),
    search: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    q = select(User).where(active_users_filter()).order_by(User.created_at.desc())
    if search:
        q = q.where(User.email.ilike(f"%{search}%") | User.full_name.ilike(f"%{search}%"))
    rows = (await db.execute(q.limit(limit).offset(offset))).scalars().all()
    return [
        {
            "id": str(r.id), "email": r.email, "full_name": r.full_name,
            "is_superadmin": r.is_superadmin,
            "email_verified_at": r.email_verified_at.isoformat() if r.email_verified_at else None,
            "created_at": r.created_at.isoformat(),
        }
        for r in rows
    ]


@router.get("/roles")
async def list_roles(_: SuperAdmin, db: AsyncSession = Depends(get_db)):
    rows = (await db.execute(select(AdminRole).order_by(AdminRole.name))).scalars().all()
    return [{"id": str(r.id), "name": r.name, "permissions": r.permissions, "description": r.description} for r in rows]


@router.post("/roles", status_code=201)
async def create_role(body: RoleCreate, _: SuperAdmin, db: AsyncSession = Depends(get_db)):
    r = AdminRole(**body.model_dump())
    db.add(r)
    await db.commit()
    await db.refresh(r)
    return {"id": str(r.id), "name": r.name}


@router.put("/roles/{role_id}")
async def update_role(role_id: uuid.UUID, body: RoleCreate, _: SuperAdmin, db: AsyncSession = Depends(get_db)):
    r = (await db.execute(select(AdminRole).where(AdminRole.id == role_id))).scalar_one_or_none()
    if not r:
        raise HTTPException(404, "Role not found")
    for k, v in body.model_dump().items():
        if hasattr(r, k):
            setattr(r, k, v)
    await db.commit()
    await db.refresh(r)
    return {"id": str(r.id), "name": r.name, "permissions": r.permissions, "description": r.description}


@router.delete("/roles/{role_id}", status_code=204)
async def delete_role(role_id: uuid.UUID, _: SuperAdmin, db: AsyncSession = Depends(get_db)):
    r = (await db.execute(select(AdminRole).where(AdminRole.id == role_id))).scalar_one_or_none()
    if not r:
        raise HTTPException(404, "Role not found")
    await db.delete(r)
    await db.commit()


@router.get("/activity")
async def list_activity(
    _: SuperAdmin,
    db: AsyncSession = Depends(get_db),
    user_id: Optional[uuid.UUID] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    q = select(AdminActivityLog).order_by(AdminActivityLog.created_at.desc())
    if user_id:
        q = q.where(AdminActivityLog.user_id == user_id)
    rows = (await db.execute(q.limit(limit).offset(offset))).scalars().all()
    return [
        {
            "id": str(r.id), "user_id": str(r.user_id), "action": r.action,
            "resource_type": r.resource_type, "resource_id": r.resource_id,
            "ip_address": r.ip_address, "metadata": r.extra_data, "created_at": r.created_at.isoformat(),
        }
        for r in rows
    ]


@router.get("/{user_id}")
async def get_user(user_id: uuid.UUID, _: SuperAdmin, db: AsyncSession = Depends(get_db)):
    u = (await db.execute(select(User).where(User.id == user_id))).scalar_one_or_none()
    if not u:
        raise HTTPException(404, "User not found")
    return {
        "id": str(u.id), "email": u.email, "full_name": u.full_name,
        "is_superadmin": u.is_superadmin,
        "totp_enabled": u.totp_enabled if hasattr(u, "totp_enabled") else False,
        "created_at": u.created_at.isoformat(),
    }


@router.put("/{user_id}")
async def update_user(user_id: uuid.UUID, body: UserUpdate, _: SuperAdmin, db: AsyncSession = Depends(get_db)):
    u = (await db.execute(select(User).where(User.id == user_id))).scalar_one_or_none()
    if not u:
        raise HTTPException(404, "User not found")
    for k, v in body.model_dump(exclude_none=True, exclude={"admin_role"}).items():
        if hasattr(u, k):
            setattr(u, k, v)
    await db.commit()
    return {"id": str(u.id), "email": u.email, "is_superadmin": u.is_superadmin}


@router.delete("/{user_id}")
async def delete_user(
    user_id: uuid.UUID,
    _: SuperAdmin,
    db: AsyncSession = Depends(get_db),
    permanent: bool = Query(False),
):
    out = await delete_platform_user(db, user_id, permanent=permanent)
    return {"ok": True, "message": out["message"]}
