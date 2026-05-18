"""Marketplace Engine — core lead intake and lifecycle management."""
from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.lead_marketplace.models import LeadMarketplace, LeadCategory, LeadTerritory
from app.modules.lead_marketplace import service as _svc


async def ingest_lead(
    db: AsyncSession,
    lead_id: uuid.UUID,
    ai_score: int,
    category_hint: str = "",
    territory_hint: str = "",
    has_phone: bool = False,
    has_email: bool = False,
    lead_age_days: int = 0,
) -> LeadMarketplace | None:
    """Ingest a freshly created Lead into the marketplace pipeline."""
    return await _svc.ingest_lead(
        db,
        lead_id=lead_id,
        ai_score=ai_score,
        category_hint=category_hint,
        territory_hint=territory_hint,
        has_phone=has_phone,
        has_email=has_email,
        lead_age_days=lead_age_days,
    )


async def get_marketplace_stats(db: AsyncSession) -> dict[str, Any]:
    from sqlalchemy import func
    total = (await db.execute(select(func.count()).select_from(LeadMarketplace))).scalar_one()
    available = (await db.execute(select(func.count()).select_from(LeadMarketplace).where(LeadMarketplace.status == "available"))).scalar_one()
    reserved = (await db.execute(select(func.count()).select_from(LeadMarketplace).where(LeadMarketplace.status == "reserved"))).scalar_one()
    sold = (await db.execute(select(func.count()).select_from(LeadMarketplace).where(LeadMarketplace.status == "sold"))).scalar_one()
    return {"total": total, "available": available, "reserved": reserved, "sold": sold}
