"""Enqueue AI scraper tasks when their next_run is due."""
from __future__ import annotations

import logging
from datetime import datetime, timezone

from sqlalchemy import or_, select

from app.core.database import get_db_context
from app.modules.ai_scraper.models import AiScraperTask
from app.workers.queue import enqueue

logger = logging.getLogger(__name__)


async def enqueue_due_scraper_tasks(ctx: dict) -> dict:
    """ARQ cron: enqueue crawler runs for tasks that are due."""
    now = datetime.now(timezone.utc)
    enqueued = 0
    skipped_running = 0

    async with get_db_context() as db:
        rows = (
            await db.execute(
                select(AiScraperTask).where(
                    AiScraperTask.status.in_(("pending", "completed", "paused")),
                    or_(
                        (AiScraperTask.next_run.isnot(None)) & (AiScraperTask.next_run <= now),
                        (AiScraperTask.next_run.is_(None))
                        & (AiScraperTask.last_run.is_(None))
                        & (AiScraperTask.status == "pending"),
                    ),
                )
            )
        ).scalars().all()

        for task in rows:
            if task.status == "running":
                skipped_running += 1
                continue
            try:
                task.status = "running"
                task.last_run = now
                db.add(task)
                await db.flush()
                await enqueue("run_crawler_task", task_id=str(task.id))
                enqueued += 1
            except Exception as exc:  # noqa: BLE001
                logger.error(
                    "enqueue_due_scraper_tasks: failed for task %s: %s",
                    task.id,
                    exc,
                )
                task.status = "error"
                db.add(task)

        await db.commit()

    logger.info(
        "enqueue_due_scraper_tasks: enqueued=%s skipped_running=%s checked=%s",
        enqueued,
        skipped_running,
        len(rows),
    )
    return {"enqueued": enqueued, "checked": len(rows)}
