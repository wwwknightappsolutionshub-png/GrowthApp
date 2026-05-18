"""Background worker: run a single AI scraper task end-to-end.

Pipeline (per spec):
    1. Fetch data from source.url_pattern
    2. Crawl pages based on aggression_level
    3. Extract text / HTML content
    4. Pass data to the AI extraction service
    5. Clean the data
    6. Convert into structured JSON
    7. Score the lead quality using AI
    8. Insert new leads into the leads table
    9. Log scraper results into ai_scraper_results
"""
from __future__ import annotations

import asyncio
import logging
import os
import re
import uuid
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urljoin, urlparse

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_context
from app.modules.ai_scraper.extractor import (
    ExtractedLead,
    extract_lead,
    standardise_text_payload,
)
from app.modules.ai_scraper.models import (
    AiScraperResult,
    AiScraperSource,
    AiScraperTask,
)
from app.modules.ai_scraper.service import aggression_to_pages, get_settings
from app.modules.auth.models import User  # noqa: F401  (ensure Base metadata)
from app.modules.leads.models import Lead
from app.modules.tenants.models import Tenant

logger = logging.getLogger(__name__)

_LINK_RE = re.compile(r"href=\"([^\"#?]+)\"", re.IGNORECASE)


async def _fetch(url: str, timeout: float = 15.0) -> tuple[int, str]:
    """Fetch a URL. Returns (status_code, body_text)."""
    try:
        import httpx

        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            resp = await client.get(url, headers={"User-Agent": "CustomerFlowAI-Scraper/1.0"})
            return resp.status_code, resp.text
    except Exception as exc:  # noqa: BLE001
        logger.warning("scraper fetch failed for %s: %s", url, exc)
        return 0, ""


def _harvest_links(base_url: str, html: str, cap: int) -> list[str]:
    if cap <= 0 or not html:
        return []
    out: list[str] = []
    seen: set[str] = set()
    parsed_base = urlparse(base_url)
    for m in _LINK_RE.finditer(html):
        href = (m.group(1) or "").strip()
        if not href:
            continue
        absolute = urljoin(base_url, href)
        if not absolute.startswith(("http://", "https://")):
            continue
        # Same-host crawling only — prevents drifting onto third-party sites.
        if urlparse(absolute).netloc != parsed_base.netloc:
            continue
        if absolute in seen:
            continue
        seen.add(absolute)
        out.append(absolute)
        if len(out) >= cap:
            break
    return out


async def _pick_target_tenant(db: AsyncSession) -> uuid.UUID | None:
    """Resolve a tenant id for inserted leads.

    Priority:
        1. AI_SCRAPER_DEFAULT_TENANT_ID env var
        2. First active tenant (deterministic by created_at)
    """
    env_tid = os.getenv("AI_SCRAPER_DEFAULT_TENANT_ID")
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


async def _insert_lead(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    extracted: ExtractedLead,
    source_name: str,
    category_hint: str | None,
) -> int:
    """Insert a row into the leads table if there's enough signal. Returns 0 or 1."""
    has_signal = bool(extracted.email or extracted.phone or extracted.name or extracted.business)
    if not has_signal:
        return 0

    first_name = extracted.name or extracted.business or "Unknown"
    last_name: str | None = None
    if extracted.name and " " in extracted.name:
        parts = extracted.name.split(" ", 1)
        first_name, last_name = parts[0], parts[1]

    tags: list[str] = ["ai_scraper"]
    if category_hint:
        tags.append(f"category:{category_hint}")
    if extracted.urgency:
        tags.append(f"urgency:{extracted.urgency}")
    if extracted.intent_level:
        tags.append(f"intent:{extracted.intent_level}")

    lead = Lead(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        first_name=first_name[:100] or "Unknown",
        last_name=(last_name[:100] if last_name else None),
        email=extracted.email[:255] if extracted.email else None,
        phone=extracted.phone[:50] if extracted.phone else None,
        message=extracted.service_need[:2000] if extracted.service_need else None,
        service_needed=extracted.service_need[:200] if extracted.service_need else None,
        postcode=extracted.location[:20] if extracted.location else None,
        source=f"ai_scraper:{source_name}"[:100],
        status="new",
        is_spam=False,
        tags=tags,
        extra_data={
            "business": extracted.business,
            "category": extracted.category,
            "revenue_estimate": extracted.revenue_estimate,
            "intent_level": extracted.intent_level,
            "urgency": extracted.urgency,
            "quality_score": extracted.quality_score,
        },
        score=extracted.quality_score,
    )
    db.add(lead)
    # Flush to get the lead.id, then auto-ingest into the lead marketplace.
    await db.flush()
    try:
        from app.modules.lead_marketplace.service import ingest_lead as _ingest_lead
        await _ingest_lead(
            db,
            lead_id=lead.id,
            ai_score=extracted.quality_score or 0,
            category_hint=category_hint,
            territory_hint=extracted.location,
            has_phone=bool(extracted.phone),
            has_email=bool(extracted.email),
            lead_age_days=0,
        )
    except Exception as _exc:  # noqa: BLE001
        logger.debug("lead_marketplace ingest skipped for lead %s: %s", lead.id, _exc)
    return 1


async def _run_one(db: AsyncSession, task_id: uuid.UUID) -> None:
    task = (
        await db.execute(select(AiScraperTask).where(AiScraperTask.id == task_id))
    ).scalar_one_or_none()
    if not task:
        logger.warning("run_ai_scraper_task: task %s not found", task_id)
        return
    source = (
        await db.execute(select(AiScraperSource).where(AiScraperSource.id == task.source_id))
    ).scalar_one_or_none()
    if not source or not source.active:
        task.status = "error"
        db.add(task)
        await db.commit()
        return

    settings_row = await get_settings(db)
    # Effective level = min(task.aggression_level, global_aggression_mode)
    order = {"low": 0, "medium": 1, "high": 2, "extreme": 3}
    eff_level = task.aggression_level
    if order.get(settings_row.global_aggression_mode, 0) < order.get(eff_level, 0):
        eff_level = settings_row.global_aggression_mode
    page_cap = aggression_to_pages(eff_level)
    parallel = max(1, int(settings_row.thread_count or 1))

    # 1. Fetch root URL
    root_status, root_body = await _fetch(source.url_pattern)
    pages: list[tuple[str, str]] = []
    if root_status and root_body:
        pages.append((source.url_pattern, root_body))

    # 2. Crawl additional pages up to the cap (same-host only).
    if page_cap > 1 and root_body:
        additional = _harvest_links(source.url_pattern, root_body, page_cap - 1)

        sem = asyncio.Semaphore(parallel)

        async def _bounded_fetch(u: str) -> tuple[str, str]:
            async with sem:
                _st, body = await _fetch(u)
                return u, body

        results = await asyncio.gather(*[_bounded_fetch(u) for u in additional], return_exceptions=False)
        for url, body in results:
            if body:
                pages.append((url, body))
            if len(pages) >= page_cap:
                break

    tenant_id = await _pick_target_tenant(db)

    # 3-9. For each page, extract, clean, structure, score, insert lead, log result.
    new_leads = 0
    cleaned_for_log: list[dict[str, Any]] = []
    extracted_for_log: list[dict[str, Any]] = []
    score_total = 0
    pages_processed = 0
    category_hint: str | None = None
    try:
        from app.modules.ai_scraper.models import AiScraperCategory

        cat = (
            await db.execute(
                select(AiScraperCategory).where(AiScraperCategory.id == task.category_id)
            )
        ).scalar_one_or_none()
        if cat:
            category_hint = cat.name
    except Exception:  # noqa: BLE001
        category_hint = None

    for url, body in pages:
        cleaned_text = standardise_text_payload(body)
        extracted = await extract_lead(body, category_hint=category_hint)
        cleaned_for_log.append({"url": url, "cleaned_text_preview": cleaned_text[:400]})
        extracted_for_log.append({"url": url, **extracted.model_dump()})
        score_total += extracted.quality_score
        pages_processed += 1
        if tenant_id is not None:
            new_leads += await _insert_lead(
                db, tenant_id, extracted, source_name=source.name, category_hint=category_hint
            )

    avg_score = int(score_total / pages_processed) if pages_processed else 0
    raw_payload = "\n\n".join(body for _u, body in pages)[:2_000_000]

    result = AiScraperResult(
        id=uuid.uuid4(),
        task_id=task.id,
        raw_payload=raw_payload or None,
        cleaned_payload={"pages": cleaned_for_log},
        ai_extracted_data={"pages": extracted_for_log},
        ai_score=avg_score,
        new_leads_created=new_leads,
    )
    db.add(result)

    task.status = "completed"
    task.last_run = datetime.now(timezone.utc)
    db.add(task)
    await db.commit()


async def run_ai_scraper_task(ctx: dict, *, task_id: str) -> None:
    """ARQ entry point."""
    tid = uuid.UUID(task_id)
    async with get_db_context() as db:
        try:
            await _run_one(db, tid)
        except Exception as exc:  # noqa: BLE001
            logger.error("run_ai_scraper_task failed for %s: %s", task_id, exc, exc_info=True)
            try:
                t = (
                    await db.execute(select(AiScraperTask).where(AiScraperTask.id == tid))
                ).scalar_one_or_none()
                if t is not None:
                    t.status = "error"
                    db.add(t)
                    await db.commit()
            except Exception:  # noqa: BLE001
                pass
            raise
