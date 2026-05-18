"""Super Admin — Marketer Tools.

POST /api/admin/marketer/set-quotas
POST /api/admin/marketer/set-pricing
GET  /api/admin/marketer/overview
"""
from __future__ import annotations

import uuid
from typing import Any, Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import SuperAdmin
from app.modules.marketer.models import (
    AudienceResearchReport,
    CompetitorIntelligenceReport,
    MarketerFunnelBlueprint,
    MarketerQuota,
)
from app.modules.tenants.models import Tenant

router = APIRouter(prefix="/api/admin/marketer", tags=["Admin — Marketer Tools"])

# In-memory pricing config (extend to DB-backed in production)
_pricing_config: dict[str, Any] = {
    "funnel_blueprint_credits": 1,
    "audience_research_credits": 1,
    "competitor_scan_credits": 1,
    "plan_quotas": {
        "starter": 3,
        "growth": 10,
        "pro": 25,
    },
}


# ── Schemas ────────────────────────────────────────────────────────────────

class SetQuotasIn(BaseModel):
    tenant_id: str
    max_reports_per_month: int


class SetPricingIn(BaseModel):
    funnel_blueprint_credits: Optional[int] = None
    audience_research_credits: Optional[int] = None
    competitor_scan_credits: Optional[int] = None
    plan_quotas: Optional[dict[str, int]] = None


# ── Endpoints ──────────────────────────────────────────────────────────────

@router.post("/set-quotas")
async def set_quotas(
    body: SetQuotasIn,
    _: SuperAdmin,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Set or update a specific tenant's monthly report quota."""
    tenant_uuid = uuid.UUID(body.tenant_id)
    quota = (
        await db.execute(
            select(MarketerQuota).where(MarketerQuota.tenant_id == tenant_uuid)
        )
    ).scalar_one_or_none()

    if quota:
        quota.max_reports_per_month = body.max_reports_per_month
    else:
        quota = MarketerQuota(
            id=uuid.uuid4(),
            tenant_id=tenant_uuid,
            max_reports_per_month=body.max_reports_per_month,
            used_reports=0,
        )
        db.add(quota)

    await db.commit()
    return {
        "ok": True,
        "tenant_id": body.tenant_id,
        "max_reports_per_month": body.max_reports_per_month,
    }


@router.post("/set-pricing")
async def set_pricing(
    body: SetPricingIn,
    _: SuperAdmin,
) -> dict[str, Any]:
    """Update the global marketer tools pricing/credit config."""
    if body.funnel_blueprint_credits is not None:
        _pricing_config["funnel_blueprint_credits"] = body.funnel_blueprint_credits
    if body.audience_research_credits is not None:
        _pricing_config["audience_research_credits"] = body.audience_research_credits
    if body.competitor_scan_credits is not None:
        _pricing_config["competitor_scan_credits"] = body.competitor_scan_credits
    if body.plan_quotas is not None:
        _pricing_config["plan_quotas"].update(body.plan_quotas)
    return {"ok": True, "pricing": _pricing_config}


@router.get("/overview")
async def marketer_overview(
    _: SuperAdmin,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Platform-wide overview of Marketer Tools usage."""
    funnel_count = (
        await db.execute(select(func.count()).select_from(MarketerFunnelBlueprint))
    ).scalar_one()
    audience_count = (
        await db.execute(select(func.count()).select_from(AudienceResearchReport))
    ).scalar_one()
    competitor_count = (
        await db.execute(select(func.count()).select_from(CompetitorIntelligenceReport))
    ).scalar_one()
    total_used = (
        await db.execute(select(func.sum(MarketerQuota.used_reports)))
    ).scalar_one() or 0
    total_max = (
        await db.execute(select(func.sum(MarketerQuota.max_reports_per_month)))
    ).scalar_one() or 0

    return {
        "reports_generated": {
            "funnel_blueprints": funnel_count,
            "audience_research": audience_count,
            "competitor_scans": competitor_count,
            "total": funnel_count + audience_count + competitor_count,
        },
        "quota_summary": {
            "total_used_this_month": total_used,
            "total_allocated": total_max,
        },
        "pricing": _pricing_config,
    }


# ── Read endpoints powering the Step 4 admin pages ────────────────────────


@router.get("/pricing")
async def get_pricing(_: SuperAdmin) -> dict[str, Any]:
    """Return the global marketer pricing config."""
    return {"pricing": _pricing_config}


@router.get("/quotas")
async def list_quotas(
    _: SuperAdmin,
    db: AsyncSession = Depends(get_db),
) -> list[dict[str, Any]]:
    """List every tenant's marketer report quota."""
    rows = (
        await db.execute(
            select(
                Tenant.id,
                Tenant.name,
                MarketerQuota.max_reports_per_month,
                MarketerQuota.used_reports,
            )
            .outerjoin(MarketerQuota, MarketerQuota.tenant_id == Tenant.id)
            .order_by(Tenant.name)
        )
    ).all()
    return [
        {
            "tenant_id": str(r.id),
            "tenant_name": r.name,
            "max_reports_per_month": r.max_reports_per_month or 0,
            "used_reports": r.used_reports or 0,
            "remaining": max(0, (r.max_reports_per_month or 0) - (r.used_reports or 0)),
        }
        for r in rows
    ]


@router.get("/usage")
async def usage_logs(
    _: SuperAdmin,
    db: AsyncSession = Depends(get_db),
    limit: int = Query(100, le=500),
) -> dict[str, Any]:
    """Recent funnel, audience-research, and competitor-scan reports across tenants."""
    funnels = (
        await db.execute(
            select(
                MarketerFunnelBlueprint.id,
                MarketerFunnelBlueprint.tenant_id,
                MarketerFunnelBlueprint.funnel_type,
                Tenant.name.label("tenant_name"),
            )
            .outerjoin(Tenant, Tenant.id == MarketerFunnelBlueprint.tenant_id)
            .limit(limit)
        )
    ).all()
    audience = (
        await db.execute(
            select(
                AudienceResearchReport.id,
                AudienceResearchReport.tenant_id,
                AudienceResearchReport.industry,
                Tenant.name.label("tenant_name"),
            )
            .outerjoin(Tenant, Tenant.id == AudienceResearchReport.tenant_id)
            .limit(limit)
        )
    ).all()
    competitor = (
        await db.execute(
            select(
                CompetitorIntelligenceReport.id,
                CompetitorIntelligenceReport.tenant_id,
                CompetitorIntelligenceReport.competitor_name,
                CompetitorIntelligenceReport.website,
                Tenant.name.label("tenant_name"),
            )
            .outerjoin(Tenant, Tenant.id == CompetitorIntelligenceReport.tenant_id)
            .limit(limit)
        )
    ).all()

    return {
        "funnels": [
            {
                "id": str(r.id),
                "tenant_id": str(r.tenant_id),
                "tenant_name": r.tenant_name,
                "funnel_type": r.funnel_type,
            }
            for r in funnels
        ],
        "audience_research": [
            {
                "id": str(r.id),
                "tenant_id": str(r.tenant_id),
                "tenant_name": r.tenant_name,
                "industry": r.industry,
            }
            for r in audience
        ],
        "competitor_scans": [
            {
                "id": str(r.id),
                "tenant_id": str(r.tenant_id),
                "tenant_name": r.tenant_name,
                "competitor_name": r.competitor_name,
                "website": r.website,
            }
            for r in competitor
        ],
    }


@router.get("/competitor-queue")
async def competitor_queue(
    _: SuperAdmin,
    db: AsyncSession = Depends(get_db),
    limit: int = Query(200, le=500),
) -> dict[str, Any]:
    """Detailed competitor intelligence report queue with extracted signals."""
    rows = (
        await db.execute(
            select(
                CompetitorIntelligenceReport.id,
                CompetitorIntelligenceReport.tenant_id,
                CompetitorIntelligenceReport.competitor_name,
                CompetitorIntelligenceReport.website,
                CompetitorIntelligenceReport.strengths_json,
                CompetitorIntelligenceReport.weaknesses_json,
                CompetitorIntelligenceReport.pricing_json,
                Tenant.name.label("tenant_name"),
            )
            .outerjoin(Tenant, Tenant.id == CompetitorIntelligenceReport.tenant_id)
            .limit(limit)
        )
    ).all()
    items = []
    fetch_errors = 0
    for r in rows:
        pricing = r.pricing_json or {}
        if isinstance(pricing, dict) and pricing.get("fetch_error"):
            fetch_errors += 1
        items.append({
            "id": str(r.id),
            "tenant_id": str(r.tenant_id),
            "tenant_name": r.tenant_name,
            "competitor_name": r.competitor_name,
            "website": r.website,
            "strengths": r.strengths_json or [],
            "weaknesses": r.weaknesses_json or [],
            "pricing_samples": (pricing.get("samples") if isinstance(pricing, dict) else []) or [],
            "positioning_gaps": (pricing.get("positioning_gaps") if isinstance(pricing, dict) else []) or [],
            "fetch_error": (pricing.get("fetch_error") if isinstance(pricing, dict) else None),
        })
    return {
        "items": items,
        "total": len(items),
        "fetch_errors": fetch_errors,
    }


@router.get("/tenants-list")
async def tenants_list(
    _: SuperAdmin,
    db: AsyncSession = Depends(get_db),
) -> list[dict[str, Any]]:
    """Tenants list for the quota-config picker."""
    rows = (
        await db.execute(select(Tenant.id, Tenant.name).order_by(Tenant.name))
    ).all()
    return [{"id": str(r.id), "name": r.name} for r in rows]
