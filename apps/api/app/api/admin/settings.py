"""Super Admin — System Settings.

GET  /api/admin/settings/
PUT  /api/admin/settings/
GET  /api/admin/settings/{key}
PUT  /api/admin/settings/{key}
DELETE /api/admin/settings/{key}
"""
from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import SuperAdmin
from app.core.rbac import SystemSetting

router = APIRouter(prefix="/api/admin/settings", tags=["Admin — Settings"])


class SettingCreate(BaseModel):
    key: str
    value: Any
    description: str = ""
    is_secret: bool = False


class SettingUpdate(BaseModel):
    value: Any
    description: Optional[str] = None


@router.get("/")
async def list_settings(_: SuperAdmin, db: AsyncSession = Depends(get_db)):
    rows = (await db.execute(select(SystemSetting).order_by(SystemSetting.key))).scalars().all()
    return [
        {
            "key": r.key, "value": None if r.is_secret else r.value,
            "description": r.description, "is_secret": r.is_secret,
            "updated_at": r.updated_at.isoformat(),
        }
        for r in rows
    ]


@router.get("/{key}")
async def get_setting(key: str, _: SuperAdmin, db: AsyncSession = Depends(get_db)):
    r = (await db.execute(select(SystemSetting).where(SystemSetting.key == key))).scalar_one_or_none()
    if not r:
        raise HTTPException(404, "Setting not found")
    return {"key": r.key, "value": None if r.is_secret else r.value, "description": r.description, "is_secret": r.is_secret}


@router.put("/")
async def upsert_settings(body: list[SettingCreate], _: SuperAdmin, db: AsyncSession = Depends(get_db)):
    for item in body:
        existing = (await db.execute(select(SystemSetting).where(SystemSetting.key == item.key))).scalar_one_or_none()
        if existing:
            existing.value = item.value
            if item.description:
                existing.description = item.description
        else:
            db.add(SystemSetting(**item.model_dump()))
    await db.commit()
    return {"updated": len(body)}


@router.put("/{key}")
async def update_setting(key: str, body: SettingUpdate, _: SuperAdmin, db: AsyncSession = Depends(get_db)):
    r = (await db.execute(select(SystemSetting).where(SystemSetting.key == key))).scalar_one_or_none()
    if not r:
        raise HTTPException(404, "Setting not found")
    r.value = body.value
    if body.description is not None:
        r.description = body.description
    await db.commit()
    return {"key": r.key, "updated": True}


@router.delete("/{key}", status_code=204)
async def delete_setting(key: str, _: SuperAdmin, db: AsyncSession = Depends(get_db)):
    r = (await db.execute(select(SystemSetting).where(SystemSetting.key == key))).scalar_one_or_none()
    if not r:
        raise HTTPException(404, "Setting not found")
    await db.delete(r)
    await db.commit()
