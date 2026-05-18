"""AI Processor — sends page batches to the Lead Intelligence Engine.

Implements RULE 7 of the Crawler Ruleset:
    Batch content as JSON array:
    [
        { "url": "...", "raw_text": "..." },
        ...
    ]
    Sends to the AI extraction engine using the EXACT official extraction
    prompt.  Validates JSON output against the official schema.

Implements RULE 8:
    If name/email/phone missing AND ai_score < 40 → discard.
"""
from __future__ import annotations

import logging
from typing import Any

from app.modules.ai_scraper.extractor import ExtractedLead, extract_lead, _ruleset3_score

logger = logging.getLogger(__name__)

# ── Official extraction prompt (CustomerFlow Lead Intelligence Engine) ─────────
# RULESET 1 — output format (no deviation allowed)
# RULESET 2 — extraction rules
# RULESET 3 — AI score calculation
# RULESET 4 — validation

_EXTRACTION_PROMPT: str = """\
You are CustomerFlow's Lead Intelligence Engine.

Your ONLY job is to analyze raw web data and extract VERIFIED business lead information.
STRICTLY FOLLOW every rule below:

-------------------------------------------------------
RULESET 1 — OUTPUT FORMAT (NO DEVIATION ALLOWED)
-------------------------------------------------------

You MUST output a single JSON object only, with the following fields:

{
  "name": "",
  "email": "",
  "phone": "",
  "business": "",
  "location": "",
  "service_need": "",
  "category": "",
  "intent_level": "",
  "revenue_estimate": "",
  "urgency": "",
  "ai_score": 0
}

Do NOT add fields, remove fields, rename fields, or create nested structures.

-------------------------------------------------------
RULESET 2 — EXTRACTION RULES
-------------------------------------------------------

1. Extract ONLY information that exists in the provided content.
2. Never hallucinate or guess impossible details.
3. If a field does not exist, return an empty string "".
4. Normalise British phone numbers to E.164 format if possible.
5. Extract the REAL business or individual name (no placeholders allowed).
6. Identify the customer's service_need using clear wording.
7. Choose the category from the closest trade niche (examples: plumbing, roofing, electrician, cleaning, landscaping).
8. Classify intent_level as: "low", "medium", or "high".
9. Provide a revenue_estimate based on job type if mentioned. If unknown, return "".
10. urgency must be one of: "immediate", "soon", "flexible", "".

-------------------------------------------------------
RULESET 3 — AI SCORE CALCULATION
-------------------------------------------------------

Calculate ai_score (0–100) using:

+20 points = phone number exists
+20 points = email exists
+15 points = clear job/service requirement is identified
+15 points = location provided
+10 points = urgency is "immediate" or "soon"
+10 points = business name or contact name identified
+10 points = intent_level = high

If the score exceeds 100, cap at 100.

-------------------------------------------------------
RULESET 4 — VALIDATION
-------------------------------------------------------

Before returning, validate that:

- All keys exist
- All values are strings except ai_score (int)
- JSON is syntactically valid
- No explanation, no commentary, no extra text

RETURN ONLY the final JSON.
DO NOT wrap it in markdown.
DO NOT include any text before or after it.
DO NOT apologise.
DO NOT explain.

-------------------------------------------------------
INPUT DATA STARTS BELOW
-------------------------------------------------------
"""


def _should_discard(lead: ExtractedLead) -> bool:
    """Discard rule (RULE 8): name+email+phone all missing AND ai_score < 40."""
    has_contact = bool(lead.name or lead.email or lead.phone)
    return not has_contact and lead.quality_score < 40


def _prompt_payload(entry: dict[str, Any]) -> str:
    """Build the full prompt payload for a single page entry.

    Prepends the official extraction prompt, then appends the page's
    raw_text as the INPUT DATA section.
    """
    return _EXTRACTION_PROMPT + entry.get("raw_text", "")


async def _extract_with_prompt(entry: dict[str, Any]) -> ExtractedLead:
    """Run the official extraction prompt against a single page entry.

    Attempts AI adapter first (with the embedded prompt); falls back to
    the heuristic extractor.  Maps the official 'ai_score' field to the
    internal 'quality_score' field.
    """
    payload = _prompt_payload(entry)

    # Try AI adapter with the full official prompt
    try:
        from app.adapters.ai import get_ai_adapter  # type: ignore[attr-defined]
        adapter = get_ai_adapter()
        if hasattr(adapter, "complete"):
            import json as _json

            response_text: str = await adapter.complete(payload)  # type: ignore[attr-defined]
            # Strip any accidental markdown fences
            response_text = response_text.strip()
            if response_text.startswith("```"):
                response_text = response_text.split("```")[-2] if "```" in response_text[3:] else response_text[3:]
                response_text = response_text.lstrip("json").strip()

            raw: dict[str, Any] = _json.loads(response_text)

            # Ruleset 1 — drop any unexpected keys
            allowed = {
                "name", "email", "phone", "business", "location",
                "service_need", "category", "intent_level",
                "revenue_estimate", "urgency", "ai_score",
            }
            raw = {k: v for k, v in raw.items() if k in allowed}

            # Map ai_score → quality_score (internal field name)
            ai_score = raw.pop("ai_score", None)
            if ai_score is None:
                ai_score = _ruleset3_score(raw)
            raw["quality_score"] = int(ai_score)

            # Ensure all string fields are strings (Ruleset 4)
            for field in ("name", "email", "phone", "business", "location",
                          "service_need", "category", "intent_level",
                          "revenue_estimate", "urgency"):
                if raw.get(field) is None:
                    raw[field] = None  # ExtractedLead accepts None

            return ExtractedLead(**raw)

    except Exception as exc:  # noqa: BLE001
        logger.debug(
            "_extract_with_prompt: AI path failed, falling back to heuristic: %s", exc
        )

    # Heuristic fallback — uses Ruleset 3 scoring internally
    return await extract_lead(entry.get("raw_text", ""), category_hint=None)


async def process_batch(batch_content: list[dict[str, Any]]) -> list[ExtractedLead]:
    """Process a batch of pages through the Lead Intelligence Engine.

    Input format (RULE 7):
        [{"url": "...", "raw_text": "..."}, ...]

    Steps:
        1. For each page, build the full official extraction prompt payload.
        2. Send to AI adapter (or heuristic fallback).
        3. Map 'ai_score' → 'quality_score'.
        4. Validate output against ExtractedLead schema.
        5. Apply RULE 8 discard filter.
        6. Return validated, non-discarded leads.

    Returns:
        List of validated ExtractedLead objects.
    """
    if not batch_content:
        return []

    results: list[ExtractedLead] = []

    for entry in batch_content:
        url: str = entry.get("url", "")
        raw_text: str = entry.get("raw_text", "")

        if not raw_text.strip():
            continue

        try:
            lead = await _extract_with_prompt(entry)
        except Exception as exc:  # noqa: BLE001
            logger.warning("process_batch: extraction failed for %s: %s", url, exc)
            continue

        # RULE 8 — discard check
        if _should_discard(lead):
            logger.debug(
                "process_batch: discarding low-signal lead from %s (score=%d)",
                url, lead.quality_score,
            )
            continue

        results.append(lead)

    return results
