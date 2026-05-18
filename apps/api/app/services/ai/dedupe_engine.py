"""AI Dedupe Engine — duplicate lead suppression."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.leads.models import Lead


async def is_duplicate(
    db: AsyncSession,
    fields: dict[str, Any],
    config: dict[str, Any] | None = None,
) -> bool:
    """Check whether a lead with the same phone/email already exists within the window."""
    cfg = config or {}
    if not cfg.get("enabled", True):
        return False

    window_days = cfg.get("window_days", 30)
    cutoff = datetime.now(timezone.utc) - timedelta(days=window_days)
    check_fields: list[str] = cfg.get("fields", ["email", "phone"])

    for field in check_fields:
        value = (fields.get(field) or "").strip()
        if not value:
            continue
        q = select(Lead).where(Lead.created_at >= cutoff)
        if field == "email":
            q = q.where(Lead.email == value)
        elif field == "phone":
            q = q.where(Lead.phone == value)
        else:
            continue
        existing = (await db.execute(q.limit(1))).scalar_one_or_none()
        if existing:
            return True
    return False


async def dedupe_batch(
    db: AsyncSession,
    leads: list[dict[str, Any]],
    config: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Filter out duplicates from a batch. Returns only unique leads."""
    unique: list[dict[str, Any]] = []
    for lead in leads:
        if not await is_duplicate(db, lead, config):
            unique.append(lead)
    return unique
