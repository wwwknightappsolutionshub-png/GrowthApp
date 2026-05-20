"""Scheduling helpers for AI scraper tasks."""
from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone

# minute hour day month weekday (5-field cron)
_CRON_EVERY_N_MINUTES = re.compile(
    r"^\*/(\d{1,2})\s+\*\s+\*\s+\*\s+\*$",
    re.IGNORECASE,
)
_CRON_EVERY_N_HOURS = re.compile(
    r"^0\s+\*/(\d{1,2})\s+\*\s+\*\s+\*$",
    re.IGNORECASE,
)
_CRON_HOURLY = re.compile(r"^0\s+\*\s+\*\s+\*\s+\*$", re.IGNORECASE)


def next_run_from_frequency(frequency: str) -> datetime:
    """Compute the next run time (UTC) from a cron expression or plain-English frequency."""
    now = datetime.now(timezone.utc)
    raw = (frequency or "").strip()
    lower = raw.lower()

    # Plain English
    if re.search(r"30\s*(min|minute)", lower):
        return now + timedelta(minutes=30)
    if re.search(r"15\s*(min|minute)", lower):
        return now + timedelta(minutes=15)
    if "hour" in lower:
        return now + timedelta(hours=1)
    if "day" in lower or "daily" in lower:
        return now + timedelta(days=1)
    if "week" in lower or "weekly" in lower:
        return now + timedelta(weeks=1)
    if "month" in lower or "monthly" in lower:
        return now + timedelta(days=30)

    # 5-field cron (min hour dom month dow)
    m = _CRON_EVERY_N_MINUTES.match(raw)
    if m:
        step = max(1, min(59, int(m.group(1))))
        return now + timedelta(minutes=step)

    m = _CRON_EVERY_N_HOURS.match(raw)
    if m:
        step = max(1, min(23, int(m.group(1))))
        return now + timedelta(hours=step)

    if _CRON_HOURLY.match(raw):
        return now + timedelta(hours=1)

    # Daily at a fixed hour, e.g. "0 2 * * *"
    daily = re.match(r"^(\d{1,2})\s+(\d{1,2})\s+\*\s+\*\s+\*$", raw)
    if daily:
        minute, hour = int(daily.group(1)), int(daily.group(2))
        candidate = now.replace(minute=minute % 60, second=0, microsecond=0)
        candidate = candidate.replace(hour=hour % 24)
        if candidate <= now:
            candidate += timedelta(days=1)
        return candidate

    return now + timedelta(hours=24)
