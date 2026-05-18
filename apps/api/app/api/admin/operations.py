"""Super Admin — Operations & Compliance.

GET  /api/admin/operations/logs
GET  /api/admin/operations/logs/{log_id}
GET  /api/admin/operations/monitoring
GET  /api/admin/operations/security
POST /api/admin/operations/security/block-ip
DELETE /api/admin/operations/security/block-ip/{ip}
"""
from __future__ import annotations

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import SuperAdmin
from app.core.rbac import SystemLog, BlockedIP

router = APIRouter(prefix="/api/admin/operations", tags=["Admin — Operations"])


class BlockIPBody(BaseModel):
    ip_address: str
    reason: str = ""


@router.get("/logs")
async def list_logs(
    _: SuperAdmin,
    db: AsyncSession = Depends(get_db),
    level: Optional[str] = Query(None),
    service: Optional[str] = Query(None),
    limit: int = Query(200, ge=1, le=1000),
    offset: int = Query(0, ge=0),
):
    q = select(SystemLog).order_by(desc(SystemLog.created_at))
    if level:
        q = q.where(SystemLog.level == level)
    if service:
        q = q.where(SystemLog.service == service)
    rows = (await db.execute(q.limit(limit).offset(offset))).scalars().all()
    return [
        {
            "id": str(r.id), "level": r.level, "service": r.service,
            "message": r.message, "metadata": r.extra_data,
            "created_at": r.created_at.isoformat(),
        }
        for r in rows
    ]


@router.get("/logs/{log_id}")
async def get_log(log_id: uuid.UUID, _: SuperAdmin, db: AsyncSession = Depends(get_db)):
    r = (await db.execute(select(SystemLog).where(SystemLog.id == log_id))).scalar_one_or_none()
    if not r:
        raise HTTPException(404, "Log not found")
    return {"id": str(r.id), "level": r.level, "service": r.service, "message": r.message, "metadata": r.extra_data, "created_at": r.created_at.isoformat()}


@router.get("/monitoring")
async def get_monitoring(_: SuperAdmin):
    """System health metrics snapshot."""
    import os, sys
    return {
        "python_version": sys.version,
        "platform": sys.platform,
        "pid": os.getpid(),
        "uptime_info": "Use your APM/metrics tool for detailed uptime",
        "status": "operational",
    }


@router.get("/security")
async def list_security(_: SuperAdmin, db: AsyncSession = Depends(get_db)):
    blocked = (await db.execute(select(BlockedIP).order_by(desc(BlockedIP.created_at)).limit(200))).scalars().all()
    return {
        "blocked_ips": [{"ip_address": r.ip_address, "reason": r.reason, "created_at": r.created_at.isoformat()} for r in blocked],
    }


@router.post("/security/block-ip", status_code=201)
async def block_ip(body: BlockIPBody, _: SuperAdmin, db: AsyncSession = Depends(get_db)):
    entry = BlockedIP(ip_address=body.ip_address, reason=body.reason)
    db.add(entry)
    await db.commit()
    await db.refresh(entry)
    return {"ip_address": entry.ip_address, "reason": entry.reason}


@router.delete("/security/block-ip/{ip}", status_code=204)
async def unblock_ip(ip: str, _: SuperAdmin, db: AsyncSession = Depends(get_db)):
    r = (await db.execute(select(BlockedIP).where(BlockedIP.ip_address == ip))).scalar_one_or_none()
    if not r:
        raise HTTPException(404, "IP not found in blocklist")
    await db.delete(r)
    await db.commit()
