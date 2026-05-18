"""AI Extraction Service — CustomerFlow Lead Intelligence Engine.

Official output schema (RULESET 1 — NO DEVIATION):
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

Hallucination guard (RULESET 2):
    Every field is populated ONLY from values found in the input.
    Missing fields are returned as "". Fields outside the schema are dropped.

Scoring formula (RULESET 3 — exact):
    +20  phone number exists
    +20  email exists
    +15  service_need identified
    +15  location provided
    +10  urgency is "immediate" or "soon"
    +10  business name or contact name identified
    +10  intent_level = "high"
    Cap at 100.

Validation (RULESET 4):
    All keys present; all values strings except ai_score (int).
"""
from __future__ import annotations

import logging
import re
from html import unescape
from typing import Any

from pydantic import BaseModel, Field, ValidationError, field_validator

logger = logging.getLogger(__name__)


_ALLOWED_FIELDS: tuple[str, ...] = (
    "name",
    "email",
    "phone",
    "business",
    "location",
    "service_need",
    "category",
    "intent_level",
    "revenue_estimate",
    "urgency",
)

_INTENT_LEVELS = ("low", "medium", "high")
_URGENCY_LEVELS = ("low", "medium", "high", "immediate")

_EMAIL_RE = re.compile(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", re.IGNORECASE)
_PHONE_RE = re.compile(r"(?:\+?\d[\d\s().-]{7,}\d)")
_HTML_TAG_RE = re.compile(r"<[^>]+>")
_WHITESPACE_RE = re.compile(r"\s+")
_UK_POSTCODE_RE = re.compile(
    r"\b(GIR\s?0AA|[A-PR-UWYZ]([0-9]{1,2}|([A-HK-Y][0-9]([0-9]|[ABEHMNPRV-Y])?)|[0-9][A-HJKPS-UW])\s?[0-9][ABD-HJLNP-UW-Z]{2})\b",
    re.IGNORECASE,
)


class ExtractedLead(BaseModel):
    """Strict output schema. Extra fields are rejected."""

    model_config = {"extra": "forbid"}

    name: str | None = None
    email: str | None = None
    phone: str | None = None
    business: str | None = None
    location: str | None = None
    service_need: str | None = None
    category: str | None = None
    intent_level: str | None = None
    revenue_estimate: str | None = None
    urgency: str | None = None
    quality_score: int = Field(ge=0, le=100, default=0)

    @field_validator("intent_level")
    @classmethod
    def _intent(cls, v: str | None) -> str | None:
        if v is None:
            return v
        v = v.strip().lower()
        return v if v in _INTENT_LEVELS else None

    @field_validator("urgency")
    @classmethod
    def _urgency(cls, v: str | None) -> str | None:
        if v is None:
            return v
        v = v.strip().lower()
        return v if v in _URGENCY_LEVELS else None


def _clean_text(value: str) -> str:
    """Strip HTML, decode entities, collapse whitespace, trim."""
    if not value:
        return ""
    no_tags = _HTML_TAG_RE.sub(" ", value)
    decoded = unescape(no_tags)
    return _WHITESPACE_RE.sub(" ", decoded).strip()


def _coerce_text(payload: Any) -> str:
    if isinstance(payload, bytes):
        try:
            return payload.decode("utf-8", errors="replace")
        except Exception:  # noqa: BLE001
            return ""
    if isinstance(payload, str):
        return payload
    if isinstance(payload, (dict, list)):
        import json

        try:
            return json.dumps(payload, default=str)
        except Exception:  # noqa: BLE001
            return ""
    return str(payload or "")


def _ruleset3_score(fields: dict[str, Any]) -> int:
    """Compute ai_score per the official RULESET 3 formula.

    +20  phone exists
    +20  email exists
    +15  service_need identified
    +15  location provided
    +10  urgency is "immediate" or "soon"
    +10  business or name identified
    +10  intent_level = "high"
    Cap at 100.
    """
    score = 0
    if fields.get("phone"):
        score += 20
    if fields.get("email"):
        score += 20
    if fields.get("service_need"):
        score += 15
    if fields.get("location"):
        score += 15
    urgency = (fields.get("urgency") or "").strip().lower()
    if urgency in ("immediate", "soon"):
        score += 10
    if fields.get("business") or fields.get("name"):
        score += 10
    if (fields.get("intent_level") or "").strip().lower() == "high":
        score += 10
    return min(100, score)


def _first_match(pattern: re.Pattern[str], text: str) -> str | None:
    m = pattern.search(text)
    return m.group(0).strip() if m else None


def _heuristic_extract(text: str, category_hint: str | None) -> dict[str, Any]:
    """Deterministic fallback extractor (never hallucinates)."""
    clean = _clean_text(text)
    out: dict[str, Any] = {k: None for k in _ALLOWED_FIELDS}

    email = _first_match(_EMAIL_RE, clean)
    phone_raw = _first_match(_PHONE_RE, clean)
    postcode = _first_match(_UK_POSTCODE_RE, clean)

    if email:
        out["email"] = email.lower()
    if phone_raw:
        out["phone"] = re.sub(r"[^\d+]", "", phone_raw)
    if postcode:
        out["location"] = postcode.upper()

    # Try to find a business / contact name near "Contact:" / "Business:".
    for label_key, target in (
        ("business", "business"),
        ("company", "business"),
        ("contact", "name"),
        ("name", "name"),
        ("location", "location"),
        ("service", "service_need"),
        ("urgency", "urgency"),
    ):
        m = re.search(rf"{label_key}\s*[:\-]\s*([^\n\r,;|]+)", clean, re.IGNORECASE)
        if m and not out.get(target):
            out[target] = _clean_text(m.group(1))[:200]

    if category_hint and not out.get("category"):
        out["category"] = category_hint

    out["quality_score"] = _ruleset3_score(out)
    return out


def _filter_to_schema(raw: dict[str, Any]) -> dict[str, Any]:
    """Drop any keys that aren't in the allowed schema (no hallucinations)."""
    return {k: raw[k] for k in (*_ALLOWED_FIELDS, "quality_score") if k in raw}


async def extract_lead(payload: Any, *, category_hint: str | None = None) -> ExtractedLead:
    """Run the extraction pipeline and return a validated ExtractedLead."""
    text = _coerce_text(payload)

    try:
        from app.adapters.ai import get_ai_adapter  # type: ignore[attr-defined]

        adapter = get_ai_adapter()
        if hasattr(adapter, "extract_lead_fields"):
            raw = await adapter.extract_lead_fields(text=text, category_hint=category_hint)  # type: ignore[attr-defined]
            if isinstance(raw, dict):
                # The official prompt returns "ai_score"; map to quality_score.
                if "ai_score" in raw and "quality_score" not in raw:
                    raw["quality_score"] = raw.pop("ai_score")
                filtered = _filter_to_schema(raw)
                # Apply Ruleset 3 scoring if not already calculated.
                if "quality_score" not in filtered:
                    filtered["quality_score"] = _ruleset3_score(filtered)
                try:
                    return ExtractedLead(**filtered)
                except ValidationError as exc:
                    logger.warning("AI adapter output failed validation: %s", exc)
    except Exception as exc:  # noqa: BLE001
        logger.debug("AI adapter unavailable, using heuristic: %s", exc)

    return ExtractedLead(**_heuristic_extract(text, category_hint))


def standardise_text_payload(payload: Any) -> str:
    """Public helper for callers that just want the cleaned text."""
    return _clean_text(_coerce_text(payload))


__all__ = ["extract_lead", "ExtractedLead", "standardise_text_payload"]
