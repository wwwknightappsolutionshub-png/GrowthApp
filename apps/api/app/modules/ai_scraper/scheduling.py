"""Scheduling helpers for AI scraper tasks."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone


def next_run_from_frequency(frequency: str) -> datetime:
    """Parse frequency text into the next scheduled run (UTC)."""
    now = datetime.now(timezone.utc)
    f = (frequency or "").strip().lower()

    if "hour" in f:
        return now + timedelta(hours=1)
    if "day" in f or "daily" in f:
        return now + timedelta(days=1)
    if "week" in f or "weekly" in f:
        return now + timedelta(weeks=1)
    if "month" in f or "monthly" in f:
        return now + timedelta(days=30)

    return now + timedelta(hours=24)
