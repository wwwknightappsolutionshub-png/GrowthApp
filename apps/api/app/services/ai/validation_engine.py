"""AI Validation Engine — Ruleset 4 enforcement and fraud/spam filtering."""
from __future__ import annotations

import re
from typing import Any

REQUIRED_KEYS = (
    "name", "email", "phone", "business", "location",
    "service_need", "category", "intent_level",
    "revenue_estimate", "urgency", "ai_score",
)

_DISPOSABLE_DOMAINS = frozenset({
    "mailinator.com", "guerrillamail.com", "tempmail.com", "throwaway.email",
    "yopmail.com", "10minutemail.com", "dispostable.com", "trashmail.com",
})

_SPAM_KEYWORDS = re.compile(
    r"\b(test|dummy|fake|example|asdf|qwerty|lorem|ipsum)\b", re.IGNORECASE
)


def validate_lead(lead: dict[str, Any], fraud_config: dict[str, Any] | None = None) -> tuple[bool, str]:
    """Validate a lead dict against Ruleset 4.

    Returns (is_valid, reason). reason is empty string when valid.
    """
    cfg = fraud_config or {}

    # Ruleset 4 — all keys must exist
    for key in REQUIRED_KEYS:
        if key not in lead:
            return False, f"Missing required key: {key}"

    # All values strings except ai_score (int)
    for key in REQUIRED_KEYS:
        if key == "ai_score":
            if not isinstance(lead[key], int):
                return False, f"ai_score must be int, got {type(lead[key])}"
        else:
            if not isinstance(lead[key], str):
                return False, f"Field '{key}' must be str, got {type(lead[key])}"

    if not cfg.get("enabled", True):
        return True, ""

    # Minimum score threshold
    min_score = cfg.get("min_score_threshold", 10)
    if lead.get("ai_score", 0) < min_score:
        return False, f"ai_score {lead['ai_score']} below threshold {min_score}"

    # Disposable email check
    email = (lead.get("email") or "").strip().lower()
    if email and cfg.get("block_disposable_emails", True):
        domain = email.split("@")[-1] if "@" in email else ""
        if domain in _DISPOSABLE_DOMAINS:
            return False, f"Disposable email domain: {domain}"

    # Spam keyword check
    block_keywords = cfg.get("block_keywords", ["test", "dummy", "fake"])
    combined_text = " ".join(str(v) for v in lead.values() if isinstance(v, str))
    for kw in block_keywords:
        if re.search(r"\b" + re.escape(kw) + r"\b", combined_text, re.IGNORECASE):
            return False, f"Spam keyword detected: {kw}"

    return True, ""


def validate_batch(
    leads: list[dict[str, Any]],
    fraud_config: dict[str, Any] | None = None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Split batch into (valid_leads, rejected_leads)."""
    valid, rejected = [], []
    for lead in leads:
        ok, _ = validate_lead(lead, fraud_config)
        (valid if ok else rejected).append(lead)
    return valid, rejected
