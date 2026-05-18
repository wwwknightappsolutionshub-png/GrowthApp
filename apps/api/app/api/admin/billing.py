"""Super Admin — Billing & Monetization.

Plans:
  GET    /api/admin/billing/plans
  GET    /api/admin/billing/plans/{plan_id}
  POST   /api/admin/billing/plans
  PUT    /api/admin/billing/plans/{plan_id}
  DELETE /api/admin/billing/plans/{plan_id}

Subscriptions / Transactions:
  GET    /api/admin/billing/subscriptions
  GET    /api/admin/billing/transactions
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
from app.modules.billing.models import SubscriptionPlan, Subscription

router = APIRouter(prefix="/api/admin/billing", tags=["Admin — Billing"])


class PlanCreate(BaseModel):
    name: str
    price_gbp_monthly: float
    max_users: int = 5
    max_locations: int = 1
    max_leads_per_month: int = 50
    has_ai_content: bool = False
    has_social_posting: bool = False
    ai_lead_requests_per_month: int = 0
    is_active: bool = True


class PlanUpdate(BaseModel):
    name: Optional[str] = None
    price_gbp_monthly: Optional[float] = None
    max_users: Optional[int] = None
    max_locations: Optional[int] = None
    max_leads_per_month: Optional[int] = None
    has_ai_content: Optional[bool] = None
    has_social_posting: Optional[bool] = None
    ai_lead_requests_per_month: Optional[int] = None
    is_active: Optional[bool] = None


@router.get("/plans")
async def list_plans(_: SuperAdmin, db: AsyncSession = Depends(get_db)):
    rows = (await db.execute(select(SubscriptionPlan).order_by(SubscriptionPlan.price_gbp_monthly))).scalars().all()
    return [
        {
            "id": str(r.id), "name": r.name, "price_gbp_monthly": float(r.price_gbp_monthly),
            "max_users": r.max_users, "max_locations": r.max_locations,
            "max_leads_per_month": r.max_leads_per_month, "has_ai_content": r.has_ai_content,
            "has_social_posting": r.has_social_posting,
            "ai_lead_requests_per_month": r.ai_lead_requests_per_month,
            "is_active": r.is_active,
        }
        for r in rows
    ]


@router.get("/plans/{plan_id}")
async def get_plan(plan_id: uuid.UUID, _: SuperAdmin, db: AsyncSession = Depends(get_db)):
    p = (await db.execute(select(SubscriptionPlan).where(SubscriptionPlan.id == plan_id))).scalar_one_or_none()
    if not p:
        raise HTTPException(404, "Plan not found")
    return {
        "id": str(p.id), "name": p.name, "price_gbp_monthly": float(p.price_gbp_monthly),
        "max_users": p.max_users, "is_active": p.is_active,
        "ai_lead_requests_per_month": p.ai_lead_requests_per_month,
    }


@router.post("/plans", status_code=201)
async def create_plan(body: PlanCreate, _: SuperAdmin, db: AsyncSession = Depends(get_db)):
    p = SubscriptionPlan(**body.model_dump())
    db.add(p)
    await db.commit()
    await db.refresh(p)
    return {"id": str(p.id), "name": p.name}


@router.put("/plans/{plan_id}")
async def update_plan(plan_id: uuid.UUID, body: PlanUpdate, _: SuperAdmin, db: AsyncSession = Depends(get_db)):
    p = (await db.execute(select(SubscriptionPlan).where(SubscriptionPlan.id == plan_id))).scalar_one_or_none()
    if not p:
        raise HTTPException(404, "Plan not found")
    for k, v in body.model_dump(exclude_none=True).items():
        setattr(p, k, v)
    await db.commit()
    return {"id": str(p.id), "name": p.name}


@router.delete("/plans/{plan_id}", status_code=204)
async def delete_plan(plan_id: uuid.UUID, _: SuperAdmin, db: AsyncSession = Depends(get_db)):
    p = (await db.execute(select(SubscriptionPlan).where(SubscriptionPlan.id == plan_id))).scalar_one_or_none()
    if not p:
        raise HTTPException(404, "Plan not found")
    p.is_active = False
    await db.commit()


@router.get("/subscriptions")
async def list_subscriptions(
    _: SuperAdmin,
    db: AsyncSession = Depends(get_db),
    status: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    q = select(Subscription).order_by(Subscription.created_at.desc())
    if status:
        q = q.where(Subscription.status == status)
    rows = (await db.execute(q.limit(limit).offset(offset))).scalars().all()
    return [
        {
            "id": str(r.id), "tenant_id": str(r.tenant_id), "plan_id": str(r.plan_id),
            "status": r.status, "stripe_subscription_id": r.stripe_subscription_id,
            "created_at": r.created_at.isoformat(),
        }
        for r in rows
    ]


@router.get("/transactions")
async def list_transactions(
    _: SuperAdmin,
    db: AsyncSession = Depends(get_db),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    """Return subscriptions as transaction records (extend with dedicated transactions table if needed)."""
    q = select(Subscription).where(Subscription.status == "active").order_by(Subscription.created_at.desc())
    rows = (await db.execute(q.limit(limit).offset(offset))).scalars().all()
    return [
        {
            "subscription_id": str(r.id), "tenant_id": str(r.tenant_id),
            "plan_id": str(r.plan_id), "status": r.status,
            "created_at": r.created_at.isoformat(),
        }
        for r in rows
    ]
