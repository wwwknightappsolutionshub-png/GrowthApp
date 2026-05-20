"""Seed default categories, sources, marketplace metadata, and overnight tasks."""
from __future__ import annotations

import logging
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.data.lead_source_catalog import CATALOG, UK_TERRITORY_SEEDS
from app.modules.ai_scraper.models import AiScraperCategory, AiScraperSource, AiScraperTask
from app.modules.ai_scraper.scheduling import next_run_from_frequency
from app.modules.lead_marketplace.models import (
    LeadCategory,
    LeadPricing,
    LeadQualityRule,
    LeadTerritory,
)

logger = logging.getLogger(__name__)

OVERNIGHT_CRON = "0 2 * * *"


async def seed_lead_factory_catalog(db: AsyncSession, *, force: bool = False) -> dict[str, int]:
    """Idempotent seed of scraper + marketplace catalog."""
    stats = {
        "scraper_categories": 0,
        "sources": 0,
        "marketplace_categories": 0,
        "territories": 0,
        "tasks": 0,
    }

    for trade in CATALOG:
        sc_name = trade["scraper_category"]
        sc_cat = (
            await db.execute(
                select(AiScraperCategory).where(AiScraperCategory.name == sc_name)
            )
        ).scalar_one_or_none()
        if not sc_cat:
            sc_cat = AiScraperCategory(
                id=uuid.uuid4(),
                name=sc_name,
                description=f"Default catalog — {sc_name}",
            )
            db.add(sc_cat)
            await db.flush()
            stats["scraper_categories"] += 1

        mk_name = trade["marketplace_category"]
        mk_cat = (
            await db.execute(select(LeadCategory).where(LeadCategory.name == mk_name))
        ).scalar_one_or_none()
        if not mk_cat:
            mk_cat = LeadCategory(
                id=uuid.uuid4(),
                name=mk_name,
                description=f"Marketplace category for {mk_name}",
            )
            db.add(mk_cat)
            await db.flush()
            stats["marketplace_categories"] += 1
            db.add(
                LeadPricing(
                    id=uuid.uuid4(),
                    category_id=mk_cat.id,
                    base_price=15.0,
                    high_quality_multiplier=1.5,
                    exclusive_multiplier=2.0,
                )
            )
            db.add(
                LeadQualityRule(
                    id=uuid.uuid4(),
                    name=f"Default — {mk_name}",
                    min_ai_score=30,
                    max_age_days=30,
                    requires_phone=False,
                    requires_email=False,
                    apply_to_category=mk_cat.id,
                )
            )

        for src in trade["sources"]:
            existing = (
                await db.execute(
                    select(AiScraperSource).where(
                        AiScraperSource.name == src["name"],
                        AiScraperSource.category_id == sc_cat.id,
                    )
                )
            ).scalar_one_or_none()
            if existing and not force:
                continue
            if existing and force:
                await db.delete(existing)
                await db.flush()
            db.add(
                AiScraperSource(
                    id=uuid.uuid4(),
                    name=src["name"],
                    url_pattern=src["url_pattern"],
                    scraping_type=src["scraping_type"],
                    source_platform=src.get("source_platform", "directory"),
                    category_id=sc_cat.id,
                    active=True,
                    is_catalog_default=True,
                    notes=src.get("notes"),
                )
            )
            stats["sources"] += 1

        # One overnight pipeline task per trade (first catalog source)
        first_source = (
            await db.execute(
                select(AiScraperSource)
                .where(AiScraperSource.category_id == sc_cat.id)
                .limit(1)
            )
        ).scalar_one_or_none()
        if first_source:
            task_row = (
                await db.execute(
                    select(AiScraperTask).where(
                        AiScraperTask.source_id == first_source.id,
                        AiScraperTask.frequency == OVERNIGHT_CRON,
                    )
                )
            ).scalar_one_or_none()
            if not task_row:
                db.add(
                    AiScraperTask(
                        id=uuid.uuid4(),
                        source_id=first_source.id,
                        category_id=sc_cat.id,
                        aggression_level="medium",
                        frequency=OVERNIGHT_CRON,
                        status="pending",
                        next_run=next_run_from_frequency(OVERNIGHT_CRON),
                    )
                )
                stats["tasks"] += 1

    for t_name, t_code in UK_TERRITORY_SEEDS:
        exists = (
            await db.execute(
                select(LeadTerritory).where(LeadTerritory.region_code == t_code)
            )
        ).scalar_one_or_none()
        if exists:
            continue
        db.add(
            LeadTerritory(
                id=uuid.uuid4(),
                name=t_name,
                region_code=t_code,
                country="GB",
            )
        )
        stats["territories"] += 1

    await db.commit()
    logger.info("seed_lead_factory_catalog: %s", stats)
    return stats
