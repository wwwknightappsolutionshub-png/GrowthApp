"""Task Runner — persistence layer for the CustomerFlow Crawler."""
from __future__ import annotations

import logging
import os
import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.ai_scraper.dedup import is_duplicate_scraper_lead, normalize_email, normalize_phone
from app.modules.ai_scraper.extractor import ExtractedLead
from app.modules.ai_scraper.insert_types import InsertLeadResult
from app.modules.ai_scraper.models import AiScraperResult
from app.modules.leads.models import Lead
from app.modules.tenants.models import Tenant

logger = logging.getLogger(__name__)


async def store_result(
    task_id: uuid.UUID,
    payload: str,
    extracted: list[dict[str, Any]],
    score: int,
    db: AsyncSession,
    *,
    new_leads_created: int = 0,
    cleaned_payload: dict[str, Any] | None = None,
    marketplace_ingest: list[dict[str, Any]] | None = None,
) -> AiScraperResult:
    """Insert a record into ai_scraper_results (Rule 9)."""
    cleaned = dict(cleaned_payload or {})
    if marketplace_ingest is not None:
        cleaned["marketplace_ingest"] = marketplace_ingest

    result = AiScraperResult(
        id=uuid.uuid4(),
        task_id=task_id,
        raw_payload=payload[:2_000_000] if payload else None,
        cleaned_payload=cleaned,
        ai_extracted_data={"leads": extracted},
        ai_score=max(0, min(100, score)),
        new_leads_created=new_leads_created,
    )
    db.add(result)
    await db.flush()
    return result


async def _resolve_tenant(db: AsyncSession) -> uuid.UUID | None:
    """Resolve a tenant id for newly inserted leads."""
    env_tid = os.getenv("CRAWLER_DEFAULT_TENANT_ID") or os.getenv("AI_SCRAPER_DEFAULT_TENANT_ID")
    if env_tid:
        try:
            tid = uuid.UUID(env_tid)
            exists = (
                await db.execute(select(Tenant.id).where(Tenant.id == tid))
            ).scalar_one_or_none()
            if exists:
                return tid
        except Exception:  # noqa: BLE001
            pass

    row = (
        await db.execute(
            select(Tenant.id)
            .where(Tenant.is_active == True)  # noqa: E712
            .order_by(Tenant.created_at.asc())
            .limit(1)
        )
    ).scalar_one_or_none()
    return row


async def insert_lead(
    extracted_json: dict[str, Any],
    db: AsyncSession,
    *,
    source_name: str = "crawler",
    category_hint: str | None = None,
    extraction_method: str | None = None,
) -> InsertLeadResult:
    """Create a leads row and attempt marketplace ingest. Returns structured outcome."""
    try:
        lead_obj = ExtractedLead(**{
            k: extracted_json.get(k)
            for k in (
                "name", "email", "phone", "business", "location",
                "service_need", "category", "intent_level",
                "revenue_estimate", "urgency",
            )
        })
        lead_obj = lead_obj.model_copy(
            update={"quality_score": int(extracted_json.get("quality_score") or 0)}
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("insert_lead: schema validation failed: %s", exc)
        return InsertLeadResult(inserted=False, skip_reason="validation_failed")

    has_signal = bool(lead_obj.name or lead_obj.email or lead_obj.phone)
    if not has_signal and lead_obj.quality_score < 40:
        return InsertLeadResult(inserted=False, skip_reason="low_signal")

    tenant_id = await _resolve_tenant(db)
    if not tenant_id:
        logger.warning("insert_lead: no tenant resolved — skipping lead")
        return InsertLeadResult(inserted=False, skip_reason="no_tenant")

    if await is_duplicate_scraper_lead(
        db, tenant_id, email=lead_obj.email, phone=lead_obj.phone
    ):
        return InsertLeadResult(
            inserted=False,
            skip_reason="duplicate",
            extraction_method=extraction_method,
        )

    first_name = lead_obj.name or lead_obj.business or "Unknown"
    last_name: str | None = None
    if lead_obj.name and " " in lead_obj.name:
        parts = lead_obj.name.split(" ", 1)
        first_name, last_name = parts[0], parts[1]

    tags: list[str] = ["crawler", "ai_scraper"]
    if category_hint:
        tags.append(f"category:{category_hint}")
    if lead_obj.urgency:
        tags.append(f"urgency:{lead_obj.urgency}")
    if lead_obj.intent_level:
        tags.append(f"intent:{lead_obj.intent_level}")

    norm_email = normalize_email(lead_obj.email)
    norm_phone = normalize_phone(lead_obj.phone)

    lead = Lead(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        first_name=first_name[:100],
        last_name=(last_name[:100] if last_name else None),
        email=lead_obj.email[:255] if lead_obj.email else None,
        phone=lead_obj.phone[:50] if lead_obj.phone else None,
        message=lead_obj.service_need[:2000] if lead_obj.service_need else None,
        service_needed=lead_obj.service_need[:200] if lead_obj.service_need else None,
        postcode=lead_obj.location[:20] if lead_obj.location else None,
        source=f"crawler:{source_name}"[:100],
        status="new",
        is_spam=False,
        tags=tags,
        extra_data={
            "business": lead_obj.business,
            "category": lead_obj.category,
            "revenue_estimate": lead_obj.revenue_estimate,
            "intent_level": lead_obj.intent_level,
            "urgency": lead_obj.urgency,
            "quality_score": lead_obj.quality_score,
            "scraper_email_normalized": norm_email,
            "scraper_phone_normalized": norm_phone,
            "extraction_method": extraction_method,
        },
        score=lead_obj.quality_score,
    )
    db.add(lead)
    await db.flush()

    marketplace_status: str | None = None
    marketplace_detail: str | None = None
    try:
        from app.modules.lead_marketplace.service import ingest_lead_detailed

        ingest = await ingest_lead_detailed(
            db,
            lead_id=lead.id,
            ai_score=lead_obj.quality_score,
            category_hint=category_hint or lead_obj.category,
            territory_hint=lead_obj.location,
            has_phone=bool(lead_obj.phone),
            has_email=bool(lead_obj.email),
            lead_age_days=0,
        )
        marketplace_status = ingest.status
        marketplace_detail = ingest.detail
        if ingest.status != "ingested":
            logger.info(
                "insert_lead: marketplace skip lead=%s status=%s detail=%s",
                lead.id,
                ingest.status,
                ingest.detail,
            )
    except Exception as exc:  # noqa: BLE001
        marketplace_status = "error"
        marketplace_detail = str(exc)[:300]
        logger.warning("insert_lead: marketplace ingest error for %s: %s", lead.id, exc)

    return InsertLeadResult(
        inserted=True,
        lead_id=lead.id,
        extraction_method=extraction_method,
        marketplace_status=marketplace_status,
        marketplace_detail=marketplace_detail,
    )


async def run_crawler_task(ctx: dict, *, task_id: str) -> None:
    """ARQ worker entry point for the CustomerFlow Crawler."""
    from app.services.ai_scraper.crawler import crawl_task

    logger.info("run_crawler_task: starting task_id=%s", task_id)
    try:
        await crawl_task(task_id)
        logger.info("run_crawler_task: completed task_id=%s", task_id)
    except Exception as exc:  # noqa: BLE001
        logger.error("run_crawler_task: unhandled error for task_id=%s: %s", task_id, exc)
        raise
