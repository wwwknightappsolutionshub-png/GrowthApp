"""AI Processor — sends page batches to the Lead Intelligence Engine."""
from __future__ import annotations

import logging
from typing import Any

from app.modules.ai_scraper.extractor import ExtractedLead
from app.services.ai_scraper.extraction import extract_lead_from_page

logger = logging.getLogger(__name__)


def _should_discard(lead: ExtractedLead) -> bool:
    """Discard rule (RULE 8): name+email+phone all missing AND ai_score < 40."""
    has_contact = bool(lead.name or lead.email or lead.phone)
    return not has_contact and lead.quality_score < 40


async def process_batch(
    batch_content: list[dict[str, Any]],
    *,
    category_hint: str | None = None,
) -> list[tuple[ExtractedLead, str]]:
    """Process a batch of pages. Returns (lead, extraction_method) pairs."""
    if not batch_content:
        return []

    results: list[tuple[ExtractedLead, str]] = []

    for entry in batch_content:
        url: str = entry.get("url", "")
        raw_text: str = entry.get("raw_text", "")

        if not raw_text.strip():
            continue

        try:
            lead, method = await extract_lead_from_page(
                entry, category_hint=category_hint
            )
            logger.debug(
                "process_batch: extracted from %s via %s (score=%d)",
                url,
                method,
                lead.quality_score,
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning("process_batch: extraction failed for %s: %s", url, exc)
            continue

        if _should_discard(lead):
            logger.debug(
                "process_batch: discarding low-signal lead from %s (score=%d)",
                url,
                lead.quality_score,
            )
            continue

        results.append((lead, method))

    return results
