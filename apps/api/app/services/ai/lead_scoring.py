"""AI-driven lead scoring.

Given a Lead row, build a fact-only prompt and ask the AI router to return
a JSON score. Results are persisted directly back onto the Lead row.
"""
from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.leads.models import Lead
from app.modules.tenants.models import Tenant
from app.services.ai.prompts import LEAD_SCORING_SYSTEM
from app.services.ai.router import get_ai_router
from app.services.ai.types import AIRouterError

logger = logging.getLogger(__name__)

VALID_LABELS = {"unqualified", "cold", "warm", "hot", "blazing"}


def _label_from_score(score: int) -> str:
    if score < 20:
        return "unqualified"
    if score < 40:
        return "cold"
    if score < 70:
        return "warm"
    if score < 90:
        return "hot"
    return "blazing"


def _build_user_message(lead: Lead, tenant: Tenant | None) -> str:
    """Build a concise, fact-only prompt. PII is OK to include — the model
    won't echo it back to other tenants because each request is isolated.
    """
    biz = tenant.name if tenant else "the business"
    biz_type = (tenant.business_type if tenant else "general SMB").lower()
    lines = [
        f"Business: {biz} ({biz_type})",
        f"Source: {lead.source}",
        f"Name: {lead.first_name} {lead.last_name or ''}".strip(),
    ]
    if lead.email:
        lines.append(f"Email: {lead.email}")
    if lead.phone:
        lines.append(f"Phone: provided")
    if lead.postcode:
        lines.append(f"Postcode: {lead.postcode}")
    if lead.service_needed:
        lines.append(f"Service needed: {lead.service_needed}")
    if lead.message:
        msg = lead.message.strip()
        if len(msg) > 1500:
            msg = msg[:1500] + "…"
        lines.append(f"Enquiry message: {msg}")
    if lead.utm_source or lead.utm_campaign:
        lines.append(
            f"UTM: source={lead.utm_source or '?'} campaign={lead.utm_campaign or '?'}"
        )
    if lead.is_spam:
        lines.append("Heuristics flagged this lead as possibly spam.")
    lines.append("Return only the JSON object as specified.")
    return "\n".join(lines)


async def score_lead(
    db: AsyncSession,
    lead: Lead,
    *,
    tenant: Tenant | None = None,
) -> Lead:
    """Score a single lead and persist `score`, `score_label`, `score_reason`,
    `scored_at`. Returns the refreshed Lead.
    """
    if tenant is None:
        tenant = (
            await db.execute(select(Tenant).where(Tenant.id == lead.tenant_id))
        ).scalar_one_or_none()

    router = get_ai_router()
    user_message = _build_user_message(lead, tenant)

    try:
        response = await router.chat(
            messages=[
                {"role": "system", "content": LEAD_SCORING_SYSTEM},
                {"role": "user", "content": user_message},
            ],
            tenant_id=lead.tenant_id,
            purpose="lead_scoring",
            max_tokens=200,
            temperature=0.1,
        )
    except AIRouterError as exc:
        logger.warning("Lead scoring failed for %s: %s", lead.id, exc)
        return lead

    score, label, reason = _parse_scoring_response(response.content)
    lead.score = score
    lead.score_label = label
    lead.score_reason = reason
    lead.scored_at = datetime.now(timezone.utc)
    db.add(lead)
    await db.commit()
    await db.refresh(lead)
    return lead


def _parse_scoring_response(raw: str) -> tuple[int, str, str]:
    """Best-effort parser for the model's JSON. Falls back to a midpoint score."""
    raw = (raw or "").strip()
    # Strip markdown fences if present.
    if raw.startswith("```"):
        raw = raw.strip("`")
        # Drop leading "json" if present.
        if raw.lstrip().lower().startswith("json"):
            raw = raw.split("\n", 1)[1] if "\n" in raw else raw[4:]

    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        # Try to extract the first JSON object substring.
        start = raw.find("{")
        end = raw.rfind("}")
        if start != -1 and end != -1 and end > start:
            try:
                parsed = json.loads(raw[start : end + 1])
            except json.JSONDecodeError:
                return 50, "warm", "Unable to parse scoring response; defaulted to warm."
        else:
            return 50, "warm", "Unable to parse scoring response; defaulted to warm."

    try:
        score = int(parsed.get("score", 50))
    except (TypeError, ValueError):
        score = 50
    score = max(0, min(100, score))
    label = str(parsed.get("label") or "").strip().lower() or _label_from_score(score)
    if label not in VALID_LABELS:
        label = _label_from_score(score)
    reason = str(parsed.get("reason") or "").strip() or _label_from_score(score)
    if len(reason) > 500:
        reason = reason[:500] + "…"
    return score, label, reason


async def backfill_unscored(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID | None = None,
    limit: int = 50,
) -> int:
    """Score the oldest unscored leads. Returns the number processed."""
    q = select(Lead).where(
        Lead.score.is_(None),
        Lead.deleted_at.is_(None),
        Lead.is_spam.is_(False),
    )
    if tenant_id:
        q = q.where(Lead.tenant_id == tenant_id)
    rows = (await db.execute(q.order_by(Lead.created_at.asc()).limit(limit))).scalars().all()
    n = 0
    for lead in rows:
        await score_lead(db, lead)
        n += 1
    return n
