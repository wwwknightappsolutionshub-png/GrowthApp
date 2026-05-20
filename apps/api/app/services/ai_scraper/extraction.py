"""LLM + heuristic lead extraction for the crawler."""
from __future__ import annotations

import json
import logging
import re
from typing import Any

from app.modules.ai_scraper.extractor import ExtractedLead, _ruleset3_score, extract_lead

logger = logging.getLogger(__name__)

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

_JSON_FENCE_RE = re.compile(r"^```(?:json)?\s*|\s*```$", re.IGNORECASE | re.MULTILINE)

_ALLOWED_KEYS = frozenset({
    "name", "email", "phone", "business", "location",
    "service_need", "category", "intent_level",
    "revenue_estimate", "urgency", "ai_score",
})


def build_extraction_prompt(entry: dict[str, Any], *, category_hint: str | None = None) -> str:
    prefix = ""
    if category_hint:
        prefix = f"Source category hint: {category_hint}\nPage URL: {entry.get('url', '')}\n\n"
    return prefix + _EXTRACTION_PROMPT + entry.get("raw_text", "")


def _strip_json_fences(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        text = _JSON_FENCE_RE.sub("", text).strip()
        if text.lower().startswith("json"):
            text = text[4:].strip()
    return text


def _parse_extraction_json(response_text: str) -> dict[str, Any]:
    text = _strip_json_fences(response_text)
    try:
        raw = json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1:
            raise
        raw = json.loads(text[start : end + 1])
    if not isinstance(raw, dict):
        raise ValueError("extraction response is not a JSON object")
    return {k: v for k, v in raw.items() if k in _ALLOWED_KEYS}


def _raw_to_extracted_lead(raw: dict[str, Any]) -> ExtractedLead:
    ai_score = raw.pop("ai_score", None)
    if ai_score is None:
        ai_score = _ruleset3_score(raw)
    for field in (
        "name", "email", "phone", "business", "location",
        "service_need", "category", "intent_level",
        "revenue_estimate", "urgency",
    ):
        val = raw.get(field)
        if val is None or val == "":
            raw[field] = None
        else:
            raw[field] = str(val).strip() or None
    raw["quality_score"] = int(ai_score)
    return ExtractedLead(**raw)


async def extract_lead_from_page(
    entry: dict[str, Any],
    *,
    category_hint: str | None = None,
) -> tuple[ExtractedLead, str]:
    """Extract a lead from a crawled page. Returns (lead, method). method is llm|heuristic."""
    from app.services.ai.router import get_ai_router
    from app.services.ai.types import AIRouterError

    prompt = build_extraction_prompt(entry, category_hint=category_hint)
    router = get_ai_router()
    if any(p.available() for p in router.providers):
        try:
            response = await router.chat(
                messages=[{"role": "user", "content": prompt}],
                purpose="scraper_extraction",
                max_tokens=700,
                temperature=0.1,
            )
            raw = _parse_extraction_json(response.content or "")
            return _raw_to_extracted_lead(raw), "llm"
        except (AIRouterError, json.JSONDecodeError, ValueError) as exc:
            logger.warning(
                "extract_lead_from_page: LLM failed for %s — %s",
                entry.get("url", ""),
                exc,
            )

    lead = await extract_lead(
        entry.get("raw_text", ""),
        category_hint=category_hint,
    )
    return lead, "heuristic"
