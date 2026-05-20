"""Tenant-facing trial status and lead source catalog."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.data.lead_source_catalog import CATALOG
from app.modules.ai_scraper.models import AiScraperCategory, AiScraperSource
from app.modules.lead_marketplace.geo import business_type_to_category_name
from app.modules.lead_marketplace.trial_assignment import _deliveries_today, _trial_window_start
from app.modules.lead_marketplace.trial_models import TrialLeadDelivery
from app.modules.tenants.models import Tenant


async def get_trial_lead_status(db: AsyncSession, tenant: Tenant) -> dict:
    now = datetime.now(timezone.utc)
    created = tenant.created_at.replace(tzinfo=timezone.utc)
    trial_ends = created + timedelta(days=settings.TRIAL_LEAD_DAYS)
    in_trial = created >= _trial_window_start() and now < trial_ends
    delivered_today = await _deliveries_today(db, tenant.id) if in_trial else 0
    total_delivered = int(
        (
            await db.execute(
                select(func.count(TrialLeadDelivery.id)).where(
                    TrialLeadDelivery.tenant_id == tenant.id
                )
            )
        ).scalar()
        or 0
    )
    days_elapsed = max(0, (now - created).days)
    return {
        "in_trial": in_trial,
        "trial_days_total": settings.TRIAL_LEAD_DAYS,
        "trial_day": min(days_elapsed + 1, settings.TRIAL_LEAD_DAYS),
        "trial_ends_at": trial_ends.isoformat(),
        "leads_per_day": settings.TRIAL_LEADS_PER_DAY,
        "delivered_today": delivered_today,
        "remaining_today": max(0, settings.TRIAL_LEADS_PER_DAY - delivered_today) if in_trial else 0,
        "total_delivered": total_delivered,
        "reminder_sent": tenant.trial_reminder_sent_at is not None,
    }


async def get_source_catalog_for_tenant(db: AsyncSession, tenant: Tenant) -> dict:
    """Return default + custom sources for the tenant's trade."""
    trade_label = business_type_to_category_name(tenant.business_type)
    cat = (
        await db.execute(
            select(AiScraperCategory).where(
                func.lower(AiScraperCategory.name) == trade_label.lower()
            )
        )
    ).scalar_one_or_none()

    sources: list[dict] = []
    if cat:
        rows = (
            await db.execute(
                select(AiScraperSource)
                .where(AiScraperSource.category_id == cat.id, AiScraperSource.active == True)  # noqa: E712
                .order_by(AiScraperSource.is_catalog_default.desc(), AiScraperSource.name)
            )
        ).scalars().all()
        for r in rows:
            sources.append({
                "id": str(r.id),
                "name": r.name,
                "url_pattern": r.url_pattern,
                "scraping_type": r.scraping_type,
                "source_platform": r.source_platform,
                "postcode_prefix": r.postcode_prefix,
                "region_label": r.region_label,
                "is_catalog_default": r.is_catalog_default,
                "notes": r.notes,
            })

    # Fallback static catalog if DB empty
    if not sources:
        for trade in CATALOG:
            if trade["marketplace_category"].lower() == trade_label.lower():
                for src in trade["sources"]:
                    sources.append({**src, "id": None, "is_catalog_default": True})
                break

    return {
        "business_type": tenant.business_type,
        "trade_label": trade_label,
        "postcode": tenant.postcode,
        "sources": sources,
    }
