"""Deduplication helpers for AI scraper / crawler lead inserts."""
from __future__ import annotations

import re
import uuid

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.leads.models import Lead

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_PHONE_DIGITS_RE = re.compile(r"\D+")


def normalize_email(email: str | None) -> str | None:
    if not email:
        return None
    value = email.strip().lower()
    return value if _EMAIL_RE.match(value) else None


def normalize_phone(phone: str | None) -> str | None:
    """Normalize UK-oriented numbers to digits-only E.164-style key for comparison."""
    if not phone:
        return None
    digits = _PHONE_DIGITS_RE.sub("", phone.strip())
    if not digits:
        return None
    if digits.startswith("44") and len(digits) >= 11:
        return digits
    if digits.startswith("0") and len(digits) >= 10:
        return "44" + digits[1:]
    if len(digits) >= 10:
        return digits
    return None


def _scraper_source_filter():
    return or_(Lead.source.like("crawler:%"), Lead.source.like("ai_scraper:%"))


async def is_duplicate_scraper_lead(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    *,
    email: str | None,
    phone: str | None,
) -> bool:
    """Return True if this contact already exists from a prior scraper/crawler run."""
    norm_email = normalize_email(email)
    if norm_email:
        existing = (
            await db.execute(
                select(Lead.id)
                .where(
                    Lead.tenant_id == tenant_id,
                    Lead.deleted_at.is_(None),
                    _scraper_source_filter(),
                    func.lower(Lead.email) == norm_email,
                )
                .limit(1)
            )
        ).scalar_one_or_none()
        if existing:
            return True

    norm_phone = normalize_phone(phone)
    if not norm_phone:
        return False

    phones = (
        await db.execute(
            select(Lead.phone)
            .where(
                Lead.tenant_id == tenant_id,
                Lead.deleted_at.is_(None),
                Lead.phone.isnot(None),
                _scraper_source_filter(),
            )
            .limit(3000)
        )
    ).scalars().all()

    for existing_phone in phones:
        if existing_phone and normalize_phone(existing_phone) == norm_phone:
            return True
    return False
