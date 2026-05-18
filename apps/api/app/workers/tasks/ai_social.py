"""AI Social scheduler — runs every minute.

Exact behaviour (Step 6):

    Scheduler checks SocialScheduleQueue every 1 minute.
    IF scheduled_time <= now AND posted_status = false:
        Execute publish()
        Update posted_status = true
        Log result.

In our schema, `posted_status` is a short string. The "false" state is
``"SCHEDULED"`` (not yet posted). After a successful publish, it is set to
``"PUBLISHED"``. Failures are recorded as ``"ERROR"``.
"""
from __future__ import annotations

import logging

from app.core.database import get_db_context
from app.modules.social.ai_service import publish_due_items

logger = logging.getLogger(__name__)


async def run_ai_social_scheduler(ctx: dict) -> dict:
    """ARQ cron entry-point — polled every 1 minute by the worker.

    Delegates to ``publish_due_items`` which:
      * SELECTs every SocialScheduleQueue row where posted_status='SCHEDULED'
        AND scheduled_time <= now,
      * calls the publish adapter for each, and
      * sets posted_status='PUBLISHED' (or 'ERROR' on failure).
    """
    async with get_db_context() as db:
        result = await publish_due_items(db)
    logger.info(
        "[ai_social_scheduler] checked=%s published=%s errors=%s",
        result.get("checked", 0),
        result.get("published", 0),
        result.get("errors", 0),
    )
    return result
