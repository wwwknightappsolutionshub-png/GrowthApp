"""Super Admin — Dashboard.

GET  /api/admin/dashboard/stats
GET  /api/admin/dashboard/health
"""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import SuperAdmin
from app.modules.auth.models import User
from app.modules.billing.models import Subscription, SubscriptionPlan
from app.modules.leads.models import Lead
from app.modules.tenants.models import Tenant

router = APIRouter(prefix="/api/admin/dashboard", tags=["Admin — Dashboard"])


@router.get("/stats")
async def get_stats(_: SuperAdmin, db: AsyncSession = Depends(get_db)):
    total_tenants = (await db.execute(select(func.count()).select_from(Tenant))).scalar_one()
    active_tenants = (await db.execute(select(func.count()).select_from(Tenant).where(Tenant.is_active == True))).scalar_one()  # noqa: E712
    total_users = (await db.execute(select(func.count()).select_from(User))).scalar_one()
    total_leads = (await db.execute(select(func.count()).select_from(Lead))).scalar_one()
    active_subs = (await db.execute(select(func.count()).select_from(Subscription).where(Subscription.status == "active"))).scalar_one()
    return {
        "total_tenants": total_tenants,
        "active_tenants": active_tenants,
        "suspended_tenants": total_tenants - active_tenants,
        "total_users": total_users,
        "total_leads": total_leads,
        "active_subscriptions": active_subs,
    }


@router.get("/health")
async def get_health(_: SuperAdmin):
    return {"status": "ok", "service": "CustomerFlow AI"}
