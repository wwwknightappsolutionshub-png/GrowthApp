"""Marketer Tools — tenant-facing endpoints.

POST /marketer/funnel/create
POST /marketer/audience-research/generate
POST /marketer/competitor/scan
GET  /marketer/quotas
"""
from __future__ import annotations

import uuid
from typing import Any, Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import CurrentTenantContext
from app.modules.marketer import service as marketer_service
from app.modules.marketer.models import (
    MarketerFunnelBlueprint,
    AudienceResearchReport,
    CompetitorIntelligenceReport,
    MarketerQuota,
)

router = APIRouter(prefix="/marketer", tags=["Marketer Tools"])


# ── Schemas ────────────────────────────────────────────────────────────────

class FunnelCreateIn(BaseModel):
    funnel_type: Optional[str] = None
    steps_json: list = []
    ai_notes: Optional[str] = None


class AudienceResearchIn(BaseModel):
    industry: Optional[str] = None


class CompetitorScanIn(BaseModel):
    competitor_name: Optional[str] = None
    website: Optional[str] = None


# ── Quota helper ───────────────────────────────────────────────────────────

async def _get_or_create_quota(db: AsyncSession, tenant_id: uuid.UUID) -> MarketerQuota:
    quota = (
        await db.execute(
            select(MarketerQuota).where(MarketerQuota.tenant_id == tenant_id)
        )
    ).scalar_one_or_none()
    if not quota:
        quota = MarketerQuota(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            max_reports_per_month=5,
            used_reports=0,
        )
        db.add(quota)
        await db.flush()
    return quota


async def _consume_quota(db: AsyncSession, tenant_id: uuid.UUID) -> dict[str, Any]:
    quota = await _get_or_create_quota(db, tenant_id)
    if quota.used_reports >= quota.max_reports_per_month:
        return {"allowed": False, "quota": quota}
    quota.used_reports += 1
    return {"allowed": True, "quota": quota}


# ── Endpoints ──────────────────────────────────────────────────────────────

@router.post("/funnel/create")
async def create_funnel(
    body: FunnelCreateIn,
    ctx: CurrentTenantContext,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    _, tenant, _ = ctx
    quota_check = await _consume_quota(db, tenant.id)
    if not quota_check["allowed"]:
        return {"ok": False, "error": "Monthly report quota exceeded"}

    blueprint = await marketer_service.build_funnel(
        db, tenant_id=tenant.id, funnel_type=body.funnel_type,
    )
    # Caller may override the AI-generated steps/notes if they want a custom blueprint.
    if body.steps_json:
        blueprint.steps_json = body.steps_json
    if body.ai_notes:
        blueprint.ai_notes = body.ai_notes

    await db.commit()
    return {
        "ok": True,
        "id": str(blueprint.id),
        "funnel_type": blueprint.funnel_type,
        "steps": blueprint.steps_json,
        "ai_notes": blueprint.ai_notes,
    }


@router.post("/audience-research/generate")
async def generate_audience_research(
    body: AudienceResearchIn,
    ctx: CurrentTenantContext,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    _, tenant, _ = ctx
    quota_check = await _consume_quota(db, tenant.id)
    if not quota_check["allowed"]:
        return {"ok": False, "error": "Monthly report quota exceeded"}

    report = await marketer_service.generate_audience_research(
        db, tenant_id=tenant.id, industry=body.industry,
    )
    await db.commit()
    return {
        "ok": True,
        "id": str(report.id),
        "industry": report.industry,
        "demographics": report.demographics_json,
        "pain_points": report.pain_points_json,
        "opportunities": report.opportunities_json,
    }


@router.post("/competitor/scan")
async def scan_competitor(
    body: CompetitorScanIn,
    ctx: CurrentTenantContext,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    _, tenant, _ = ctx
    quota_check = await _consume_quota(db, tenant.id)
    if not quota_check["allowed"]:
        return {"ok": False, "error": "Monthly report quota exceeded"}

    report = await marketer_service.scan_competitor(
        db,
        tenant_id=tenant.id,
        competitor_name=body.competitor_name,
        website=body.website,
    )
    await db.commit()
    return {
        "ok": True,
        "id": str(report.id),
        "competitor_name": report.competitor_name,
        "website": report.website,
        "strengths": report.strengths_json,
        "weaknesses": report.weaknesses_json,
        "pricing": report.pricing_json,
    }


@router.get("/quotas")
async def get_quotas(
    ctx: CurrentTenantContext,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    _, tenant, _ = ctx
    quota = await _get_or_create_quota(db, tenant.id)
    await db.commit()
    return {
        "tenant_id": str(tenant.id),
        "max_reports_per_month": quota.max_reports_per_month,
        "used_reports": quota.used_reports,
        "remaining": max(0, quota.max_reports_per_month - quota.used_reports),
    }
