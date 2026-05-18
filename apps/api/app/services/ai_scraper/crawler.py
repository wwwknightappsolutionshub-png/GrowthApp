"""CustomerFlow Official Crawler — main orchestrator.

MAIN FLOW (mandatory per spec):

crawl_task(task_id):
    1.  Validate task exists and is active
    2.  Load source object
    3.  Determine aggression depth
    4.  Generate initial target URLs from source.url_pattern
    5.  For each URL:
          a. Fetch page (with retry logic)
          b. Extract HTML/text content
          c. Clean and normalize content
          d. Store raw snapshot in memory buffer
          e. Extract child links when aggression_level > low
          f. Add new pages to queue following depth rules
    6.  After crawl, group content into batches (5–25 pages)
    7.  For each batch:
          a. Send to AI extraction (strict extraction prompt)
          b. Validate JSON output
          c. Insert new leads into leads table
          d. Insert marketplace entries
          e. Log results in ai_scraper_results
    8.  Update task.last_run and task.next_run
    9.  Mark task status as "completed" or "error"

All rules (RULE 1–10) are enforced here.
"""
from __future__ import annotations

import asyncio
import logging
import random
import uuid
from collections import deque
from datetime import datetime, timezone, timedelta
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_context
from app.modules.ai_scraper.models import AiScraperSource, AiScraperTask
from app.services.ai_scraper.ai_processor import process_batch
from app.services.ai_scraper.batcher import batch_content, PageEntry
from app.services.ai_scraper.cleaner import clean_content
from app.services.ai_scraper.fetcher import fetch_page
from app.services.ai_scraper.link_extractor import extract_links
from app.services.ai_scraper.parser import (
    DEPTH_MAP,
    PAGE_CAP_MAP,
    generate_initial_urls,
)
from app.services.ai_scraper.task_runner import insert_lead, store_result

logger = logging.getLogger(__name__)

# Rate-limiting: 1–2 second random wait between requests (Rule 6)
_RATE_LIMIT_MIN: float = 1.0
_RATE_LIMIT_MAX: float = 2.0

# Aggression levels that trigger child link extraction (Rule 5)
_LINK_EXTRACT_LEVELS: frozenset[str] = frozenset({"medium", "high", "extreme"})


def _next_run_from_frequency(frequency: str) -> datetime | None:
    """Parse a simple cron-like or plain-English frequency into next_run."""
    now = datetime.now(timezone.utc)
    f = (frequency or "").strip().lower()

    # Handle plain-English periods
    if "hour" in f:
        return now + timedelta(hours=1)
    if "day" in f or "daily" in f:
        return now + timedelta(days=1)
    if "week" in f or "weekly" in f:
        return now + timedelta(weeks=1)
    if "month" in f or "monthly" in f:
        return now + timedelta(days=30)

    # Default: 24 hours
    return now + timedelta(hours=24)


async def crawl_task(task_id: str) -> None:
    """Main crawl orchestrator (mandatory entry point).

    Steps 1–9 per spec. Opens its own DB session.

    Error handling (Rule 10):
        - Logs every exception.
        - Updates task.status = "error" on failure.
        - Individual page fetch failures are retried at fetch level;
          other pages continue processing (partial-failure resilience).
    """
    async with get_db_context() as db:
        # ── Step 1: Validate task ─────────────────────────────────────────
        try:
            tid = uuid.UUID(str(task_id))
        except ValueError:
            logger.error("crawl_task: invalid task_id format: %s", task_id)
            return

        task = (
            await db.execute(
                select(AiScraperTask).where(AiScraperTask.id == tid)
            )
        ).scalar_one_or_none()

        if not task:
            logger.error("crawl_task: task %s not found", task_id)
            return

        if task.status == "running":
            logger.warning("crawl_task: task %s is already running — skipping", task_id)
            return

        # ── Step 2: Load source ───────────────────────────────────────────
        source = (
            await db.execute(
                select(AiScraperSource).where(AiScraperSource.id == task.source_id)
            )
        ).scalar_one_or_none()

        if not source or not source.active:
            logger.error(
                "crawl_task: source for task %s is missing or inactive", task_id
            )
            task.status = "error"
            db.add(task)
            await db.commit()
            return

        task.status = "running"
        db.add(task)
        await db.commit()

        category_hint: str | None = None
        try:
            from app.modules.ai_scraper.models import AiScraperCategory

            cat_row = (
                await db.execute(
                    select(AiScraperCategory).where(
                        AiScraperCategory.id == task.category_id
                    )
                )
            ).scalar_one_or_none()
            if cat_row:
                category_hint = cat_row.name
        except Exception:  # noqa: BLE001
            pass

        # ── Step 3: Determine aggression depth ────────────────────────────
        level: str = task.aggression_level or "low"
        depth: int = DEPTH_MAP.get(level, 1)
        page_cap: int = PAGE_CAP_MAP.get(level, 2)

        # ── Step 4: Generate initial target URLs ──────────────────────────
        initial_urls = generate_initial_urls(source.url_pattern, depth)
        if not initial_urls:
            logger.warning(
                "crawl_task: no initial URLs generated for source %s", source.id
            )
            task.status = "error"
            db.add(task)
            await db.commit()
            return

        # ── Steps 5a–5f: BFS crawl with depth and page-cap limiting ───────
        # Queue entries: (url, current_depth)
        queue: deque[tuple[str, int]] = deque(
            (url, 0) for url in initial_urls
        )
        visited: set[str] = set(initial_urls)

        # In-memory buffer: list of PageEntry
        buffer: list[PageEntry] = []
        raw_pages: list[tuple[str, str]] = []  # (url, raw_html)
        cleaned_log: list[dict[str, Any]] = []

        try:
            while queue and len(buffer) < page_cap:
                url, current_depth = queue.popleft()

                # Step 5a: Fetch page (retries handled inside fetch_page)
                status_code, html = await fetch_page(url)

                # Rule 6: rate limiting between requests
                await asyncio.sleep(random.uniform(_RATE_LIMIT_MIN, _RATE_LIMIT_MAX))

                if not html or status_code == 0:
                    logger.warning(
                        "crawl_task: fetch failed or empty for %s (status=%d)",
                        url, status_code,
                    )
                    continue

                # Step 5b/5c: Clean and normalise
                cleaned_text = clean_content(html)
                if not cleaned_text.strip():
                    continue

                # Step 5d: Store raw snapshot in memory buffer
                buffer.append(PageEntry(url=url, raw_text=cleaned_text))
                raw_pages.append((url, html))
                cleaned_log.append({"url": url, "preview": cleaned_text[:400]})

                # Steps 5e/5f: Extract child links for medium/high/extreme
                if level in _LINK_EXTRACT_LEVELS and current_depth < depth:
                    child_links = extract_links(html, url)
                    for child_url in child_links:
                        if child_url not in visited and len(visited) < page_cap * 2:
                            visited.add(child_url)
                            queue.append((child_url, current_depth + 1))

        except Exception as exc:  # noqa: BLE001
            # Rule 10: log exception, mark task error
            logger.error(
                "crawl_task: crawl loop error for task %s: %s",
                task_id, exc, exc_info=True,
            )
            task.status = "error"
            task.last_run = datetime.now(timezone.utc)
            db.add(task)
            await db.commit()
            return

        if not buffer:
            logger.warning("crawl_task: no pages crawled for task %s", task_id)
            task.status = "completed"
            task.last_run = datetime.now(timezone.utc)
            task.next_run = _next_run_from_frequency(task.frequency)
            db.add(task)
            await db.commit()
            return

        # ── Step 6: Group content into batches ────────────────────────────
        batches = batch_content(buffer)

        # ── Step 7: Process each batch ────────────────────────────────────
        all_extracted: list[dict[str, Any]] = []
        total_leads = 0
        score_total = 0

        for batch in batches:
            # Step 7a: Send to AI extraction / validate JSON output
            try:
                leads_in_batch = await process_batch(batch)
            except Exception as exc:  # noqa: BLE001
                logger.error(
                    "crawl_task: process_batch failed for task %s: %s",
                    task_id, exc,
                )
                continue

            for lead_obj in leads_in_batch:
                lead_dict = lead_obj.model_dump()
                all_extracted.append(lead_dict)
                score_total += lead_obj.quality_score

                # Steps 7c/7d: Insert lead + marketplace entry
                try:
                    inserted = await insert_lead(
                        lead_dict,
                        db,
                        source_name=source.name,
                        category_hint=category_hint,
                    )
                    if inserted:
                        total_leads += 1
                except Exception as exc:  # noqa: BLE001
                    logger.error(
                        "crawl_task: insert_lead failed for task %s: %s",
                        task_id, exc,
                    )

        avg_score = int(score_total / len(all_extracted)) if all_extracted else 0
        raw_payload = "\n\n".join(html for _url, html in raw_pages)

        # Step 7e: Log results in ai_scraper_results
        try:
            await store_result(
                task_id=task.id,
                payload=raw_payload,
                extracted=all_extracted,
                score=avg_score,
                db=db,
                new_leads_created=total_leads,
                cleaned_payload={"pages": cleaned_log},
            )
        except Exception as exc:  # noqa: BLE001
            logger.error(
                "crawl_task: store_result failed for task %s: %s",
                task_id, exc,
            )

        # ── Steps 8–9: Update task timestamps and status ──────────────────
        task.last_run = datetime.now(timezone.utc)
        task.next_run = _next_run_from_frequency(task.frequency)
        task.status = "completed"
        db.add(task)
        await db.commit()

        logger.info(
            "crawl_task: task %s completed — %d pages, %d leads, avg_score=%d",
            task_id, len(buffer), total_leads, avg_score,
        )
