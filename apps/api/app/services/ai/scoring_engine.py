"""AI Scoring Engine — computes ai_score per the Lead Intelligence Engine Ruleset 3."""
from __future__ import annotations

from typing import Any


def compute_score(fields: dict[str, Any], config: dict[str, Any] | None = None) -> int:
    """Compute ai_score from extracted lead fields.

    Default weights (Ruleset 3):
      +20 phone, +20 email, +15 service_need, +15 location,
      +10 urgency immediate/soon, +10 business/name, +10 intent high
      Cap at 100.
    """
    cfg = config or {}
    phone_pts = cfg.get("phone_points", 20)
    email_pts = cfg.get("email_points", 20)
    service_pts = cfg.get("service_need_points", 15)
    location_pts = cfg.get("location_points", 15)
    urgency_pts = cfg.get("urgency_points", 10)
    name_pts = cfg.get("name_points", 10)
    intent_pts = cfg.get("intent_high_points", 10)
    cap = cfg.get("cap", 100)

    score = 0
    if fields.get("phone"):
        score += phone_pts
    if fields.get("email"):
        score += email_pts
    if fields.get("service_need"):
        score += service_pts
    if fields.get("location"):
        score += location_pts
    urgency = (fields.get("urgency") or "").strip().lower()
    if urgency in ("immediate", "soon"):
        score += urgency_pts
    if fields.get("business") or fields.get("name"):
        score += name_pts
    if (fields.get("intent_level") or "").strip().lower() == "high":
        score += intent_pts
    return min(cap, score)


def score_batch(leads: list[dict[str, Any]], config: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    """Score a list of lead dicts in-place; returns the same list with ai_score set."""
    for lead in leads:
        lead["ai_score"] = compute_score(lead, config)
    return leads
