"""Background tasks that call the AI router.

Keeping AI work in background jobs lets the HTTP API stay fast and prevents
provider latency / rate limits from impacting interactive endpoints.
"""
from __future__ import annotations

import logging
import uuid

from sqlalchemy import select

from app.core.database import get_db_context
from app.modules.leads.models import Lead
from app.services.ai.lead_scoring import backfill_unscored, score_lead

logger = logging.getLogger(__name__)


async def score_lead_task(ctx: dict, *, lead_id: str, tenant_id: str) -> None:
    """Score a single lead. Triggered by lead creation hook."""
    async with get_db_context() as db:
        try:
            lead_uuid = uuid.UUID(lead_id)
            lead = (
                await db.execute(select(Lead).where(Lead.id == lead_uuid))
            ).scalar_one_or_none()
            if not lead or lead.deleted_at is not None:
                logger.info("score_lead_task: lead %s missing", lead_id)
                return
            if lead.score is not None:
                logger.info("score_lead_task: lead %s already scored", lead_id)
                return
            await score_lead(db, lead)
        except Exception as exc:
            logger.error("score_lead_task failed for %s: %s", lead_id, exc, exc_info=True)
            raise


async def backfill_lead_scores_task(ctx: dict, *, tenant_id: str | None = None, limit: int = 50) -> int:
    """Periodic sweep: score the oldest unscored leads. Cron-friendly."""
    async with get_db_context() as db:
        tid = uuid.UUID(tenant_id) if tenant_id else None
        n = await backfill_unscored(db, tenant_id=tid, limit=limit)
        logger.info("backfill_lead_scores_task: scored %d leads", n)
        return n
