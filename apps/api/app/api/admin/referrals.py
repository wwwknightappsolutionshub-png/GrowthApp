"""Super Admin — Referral & Incentive Management.

GET    /api/admin/referrals/programs
GET    /api/admin/referrals/programs/{program_id}
POST   /api/admin/referrals/programs
PUT    /api/admin/referrals/programs/{program_id}
DELETE /api/admin/referrals/programs/{program_id}
GET    /api/admin/referrals/events
GET    /api/admin/referrals/payouts
POST   /api/admin/referrals/payouts/{payout_id}/approve
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
from app.modules.referrals.models import ReferralProgram, ReferralEvent, ReferralPayout

router = APIRouter(prefix="/api/admin/referrals", tags=["Admin — Referrals"])


class ProgramCreate(BaseModel):
    name: str
    program_type: str = "tradesman"
    reward_type: str = "credit"
    reward_value: float
    min_bookings: int = 1
    is_active: bool = True
    retargeting_enabled: bool = False


class ProgramUpdate(BaseModel):
    name: Optional[str] = None
    reward_value: Optional[float] = None
    min_bookings: Optional[int] = None
    is_active: Optional[bool] = None
    retargeting_enabled: Optional[bool] = None


@router.get("/programs")
async def list_programs(
    _: SuperAdmin,
    db: AsyncSession = Depends(get_db),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    rows = (await db.execute(select(ReferralProgram).order_by(ReferralProgram.created_at.desc()).limit(limit).offset(offset))).scalars().all()
    return [
        {
            "id": str(r.id), "name": r.name, "program_type": r.program_type,
            "reward_type": r.reward_type, "reward_value": float(r.reward_value),
            "is_active": r.is_active, "created_at": r.created_at.isoformat(),
        }
        for r in rows
    ]


@router.get("/programs/{program_id}")
async def get_program(program_id: uuid.UUID, _: SuperAdmin, db: AsyncSession = Depends(get_db)):
    p = (await db.execute(select(ReferralProgram).where(ReferralProgram.id == program_id))).scalar_one_or_none()
    if not p:
        raise HTTPException(404, "Program not found")
    return {"id": str(p.id), "name": p.name, "program_type": p.program_type, "reward_type": p.reward_type, "reward_value": float(p.reward_value), "is_active": p.is_active}


@router.post("/programs", status_code=201)
async def create_program(body: ProgramCreate, _: SuperAdmin, db: AsyncSession = Depends(get_db)):
    p = ReferralProgram(**body.model_dump())
    db.add(p)
    await db.commit()
    await db.refresh(p)
    return {"id": str(p.id), "name": p.name}


@router.put("/programs/{program_id}")
async def update_program(program_id: uuid.UUID, body: ProgramUpdate, _: SuperAdmin, db: AsyncSession = Depends(get_db)):
    p = (await db.execute(select(ReferralProgram).where(ReferralProgram.id == program_id))).scalar_one_or_none()
    if not p:
        raise HTTPException(404, "Program not found")
    for k, v in body.model_dump(exclude_none=True).items():
        setattr(p, k, v)
    await db.commit()
    return {"id": str(p.id), "name": p.name}


@router.delete("/programs/{program_id}", status_code=204)
async def delete_program(program_id: uuid.UUID, _: SuperAdmin, db: AsyncSession = Depends(get_db)):
    p = (await db.execute(select(ReferralProgram).where(ReferralProgram.id == program_id))).scalar_one_or_none()
    if not p:
        raise HTTPException(404, "Program not found")
    await db.delete(p)
    await db.commit()


@router.get("/events")
async def list_events(
    _: SuperAdmin,
    db: AsyncSession = Depends(get_db),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    rows = (await db.execute(select(ReferralEvent).order_by(ReferralEvent.created_at.desc()).limit(limit).offset(offset))).scalars().all()
    return [
        {
            "id": str(r.id), "program_id": str(r.program_id), "referrer_id": str(r.referrer_id),
            "event_type": r.event_type, "status": r.status, "created_at": r.created_at.isoformat(),
        }
        for r in rows
    ]


@router.get("/payouts")
async def list_payouts(
    _: SuperAdmin,
    db: AsyncSession = Depends(get_db),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    rows = (await db.execute(select(ReferralPayout).order_by(ReferralPayout.created_at.desc()).limit(limit).offset(offset))).scalars().all()
    return [
        {
            "id": str(r.id), "user_id": str(r.user_id), "amount": float(r.amount),
            "status": r.status, "created_at": r.created_at.isoformat(),
        }
        for r in rows
    ]


@router.post("/payouts/{payout_id}/approve")
async def approve_payout(payout_id: uuid.UUID, _: SuperAdmin, db: AsyncSession = Depends(get_db)):
    p = (await db.execute(select(ReferralPayout).where(ReferralPayout.id == payout_id))).scalar_one_or_none()
    if not p:
        raise HTTPException(404, "Payout not found")
    p.status = "paid"
    await db.commit()
    return {"id": str(p.id), "status": p.status}
