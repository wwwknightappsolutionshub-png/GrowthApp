"""Service-layer CRUD + run-enqueue helpers for the AI Scraper module."""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    BadRequestException,
    ConflictException,
    NotFoundException,
)
from app.modules.ai_scraper.models import (
    AGGRESSION_LEVELS,
    AiScraperCategory,
    AiScraperResult,
    AiScraperSettings,
    AiScraperSource,
    AiScraperTask,
)
from app.modules.ai_scraper.schemas import (
    CategoryCreate,
    CategoryUpdate,
    SettingsBody,
    SourceCreate,
    SourceUpdate,
    TaskCreate,
    TaskUpdate,
)

logger = logging.getLogger(__name__)


# ── Categories ──────────────────────────────────────────────────────────────


async def list_categories(db: AsyncSession) -> list[AiScraperCategory]:
    rows = await db.execute(
        select(AiScraperCategory).order_by(AiScraperCategory.name.asc())
    )
    return list(rows.scalars().all())


async def get_category(db: AsyncSession, category_id: uuid.UUID) -> AiScraperCategory:
    row = (
        await db.execute(select(AiScraperCategory).where(AiScraperCategory.id == category_id))
    ).scalar_one_or_none()
    if not row:
        raise NotFoundException("ai_scraper_category")
    return row


async def create_category(db: AsyncSession, data: CategoryCreate) -> AiScraperCategory:
    existing = (
        await db.execute(select(AiScraperCategory).where(AiScraperCategory.name == data.name))
    ).scalar_one_or_none()
    if existing:
        raise ConflictException("Category name already exists")
    cat = AiScraperCategory(id=uuid.uuid4(), name=data.name, description=data.description)
    db.add(cat)
    await db.commit()
    await db.refresh(cat)
    return cat


async def update_category(
    db: AsyncSession, category_id: uuid.UUID, data: CategoryUpdate
) -> AiScraperCategory:
    cat = await get_category(db, category_id)
    fields = data.model_dump(exclude_unset=True)
    for k, v in fields.items():
        setattr(cat, k, v)
    db.add(cat)
    await db.commit()
    await db.refresh(cat)
    return cat


async def delete_category(db: AsyncSession, category_id: uuid.UUID) -> None:
    cat = await get_category(db, category_id)
    in_use_src = (
        await db.execute(
            select(func.count()).select_from(AiScraperSource).where(AiScraperSource.category_id == cat.id)
        )
    ).scalar_one()
    in_use_task = (
        await db.execute(
            select(func.count()).select_from(AiScraperTask).where(AiScraperTask.category_id == cat.id)
        )
    ).scalar_one()
    if int(in_use_src) > 0 or int(in_use_task) > 0:
        raise BadRequestException("Category is in use by sources or tasks")
    await db.delete(cat)
    await db.commit()


# ── Sources ─────────────────────────────────────────────────────────────────


async def list_sources(
    db: AsyncSession, *, active: bool | None = None, category_id: uuid.UUID | None = None
) -> list[AiScraperSource]:
    stmt = select(AiScraperSource).order_by(AiScraperSource.created_at.desc())
    if active is not None:
        stmt = stmt.where(AiScraperSource.active == active)
    if category_id is not None:
        stmt = stmt.where(AiScraperSource.category_id == category_id)
    rows = await db.execute(stmt)
    return list(rows.scalars().all())


async def get_source(db: AsyncSession, source_id: uuid.UUID) -> AiScraperSource:
    row = (
        await db.execute(select(AiScraperSource).where(AiScraperSource.id == source_id))
    ).scalar_one_or_none()
    if not row:
        raise NotFoundException("ai_scraper_source")
    return row


async def create_source(db: AsyncSession, data: SourceCreate) -> AiScraperSource:
    await get_category(db, data.category_id)
    src = AiScraperSource(
        id=uuid.uuid4(),
        name=data.name,
        url_pattern=data.url_pattern,
        scraping_type=data.scraping_type,
        category_id=data.category_id,
        active=data.active,
        notes=data.notes,
    )
    db.add(src)
    await db.commit()
    await db.refresh(src)
    return src


async def update_source(
    db: AsyncSession, source_id: uuid.UUID, data: SourceUpdate
) -> AiScraperSource:
    src = await get_source(db, source_id)
    fields = data.model_dump(exclude_unset=True)
    if "category_id" in fields:
        await get_category(db, fields["category_id"])
    for k, v in fields.items():
        setattr(src, k, v)
    db.add(src)
    await db.commit()
    await db.refresh(src)
    return src


async def delete_source(db: AsyncSession, source_id: uuid.UUID) -> None:
    src = await get_source(db, source_id)
    has_tasks = (
        await db.execute(
            select(func.count()).select_from(AiScraperTask).where(AiScraperTask.source_id == src.id)
        )
    ).scalar_one()
    if int(has_tasks) > 0:
        raise BadRequestException("Source has tasks; delete those first")
    await db.delete(src)
    await db.commit()


# ── Tasks ───────────────────────────────────────────────────────────────────


async def list_tasks(
    db: AsyncSession,
    *,
    source_id: uuid.UUID | None = None,
    status: str | None = None,
) -> list[AiScraperTask]:
    stmt = select(AiScraperTask).order_by(AiScraperTask.created_at.desc())
    if source_id is not None:
        stmt = stmt.where(AiScraperTask.source_id == source_id)
    if status is not None:
        stmt = stmt.where(AiScraperTask.status == status)
    rows = await db.execute(stmt)
    return list(rows.scalars().all())


async def get_task(db: AsyncSession, task_id: uuid.UUID) -> AiScraperTask:
    row = (
        await db.execute(select(AiScraperTask).where(AiScraperTask.id == task_id))
    ).scalar_one_or_none()
    if not row:
        raise NotFoundException("ai_scraper_task")
    return row


async def create_task(db: AsyncSession, data: TaskCreate) -> AiScraperTask:
    await get_source(db, data.source_id)
    await get_category(db, data.category_id)
    from app.modules.ai_scraper.scheduling import next_run_from_frequency

    task = AiScraperTask(
        id=uuid.uuid4(),
        source_id=data.source_id,
        category_id=data.category_id,
        aggression_level=data.aggression_level,
        frequency=data.frequency,
        status=data.status,
        next_run=next_run_from_frequency(data.frequency),
    )
    db.add(task)
    await db.commit()
    await db.refresh(task)
    return task


async def update_task(
    db: AsyncSession, task_id: uuid.UUID, data: TaskUpdate
) -> AiScraperTask:
    task = await get_task(db, task_id)
    fields = data.model_dump(exclude_unset=True)
    if "source_id" in fields:
        await get_source(db, fields["source_id"])
    if "category_id" in fields:
        await get_category(db, fields["category_id"])
    for k, v in fields.items():
        setattr(task, k, v)
    db.add(task)
    await db.commit()
    await db.refresh(task)
    return task


async def delete_task(db: AsyncSession, task_id: uuid.UUID) -> None:
    task = await get_task(db, task_id)
    await db.delete(task)
    await db.commit()


async def task_with_lead_count(
    db: AsyncSession, task: AiScraperTask
) -> tuple[AiScraperTask, int]:
    total = (
        await db.execute(
            select(func.coalesce(func.sum(AiScraperResult.new_leads_created), 0))
            .where(AiScraperResult.task_id == task.id)
        )
    ).scalar_one()
    return task, int(total or 0)


async def trigger_task_run(db: AsyncSession, task_id: uuid.UUID) -> tuple[AiScraperTask, bool]:
    """Mark a task as running and enqueue the background worker."""
    task = await get_task(db, task_id)
    task.status = "running"
    task.last_run = datetime.now(timezone.utc)
    db.add(task)
    await db.commit()
    await db.refresh(task)
    try:
        from app.workers.queue import enqueue

        await enqueue("run_crawler_task", task_id=str(task.id))
        enqueued = True
    except Exception as exc:  # noqa: BLE001
        logger.error("Could not enqueue scraper task %s: %s", task.id, exc)
        enqueued = False
    return task, enqueued


# ── Results ─────────────────────────────────────────────────────────────────


async def list_results(
    db: AsyncSession,
    *,
    task_id: uuid.UUID | None = None,
    limit: int = 100,
) -> list[AiScraperResult]:
    stmt = (
        select(AiScraperResult)
        .order_by(AiScraperResult.created_at.desc())
        .limit(max(1, min(limit, 500)))
    )
    if task_id is not None:
        stmt = stmt.where(AiScraperResult.task_id == task_id)
    rows = await db.execute(stmt)
    return list(rows.scalars().all())


async def get_result(db: AsyncSession, result_id: uuid.UUID) -> AiScraperResult:
    row = (
        await db.execute(select(AiScraperResult).where(AiScraperResult.id == result_id))
    ).scalar_one_or_none()
    if not row:
        raise NotFoundException("ai_scraper_result")
    return row


# ── Settings ────────────────────────────────────────────────────────────────


async def get_settings(db: AsyncSession) -> AiScraperSettings:
    row = (
        await db.execute(select(AiScraperSettings).where(AiScraperSettings.id == 1))
    ).scalar_one_or_none()
    if row is None:
        row = AiScraperSettings(id=1, thread_count=2, global_aggression_mode="low")
        db.add(row)
        await db.commit()
        await db.refresh(row)
    return row


async def update_settings(db: AsyncSession, data: SettingsBody) -> AiScraperSettings:
    if data.global_aggression_mode not in AGGRESSION_LEVELS:
        raise BadRequestException("invalid global_aggression_mode")
    row = await get_settings(db)
    row.thread_count = data.thread_count
    row.global_aggression_mode = data.global_aggression_mode
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return row


def aggression_to_pages(level: str) -> int:
    """Map an aggression level to a hard page-crawl cap.

    Per spec:
        low     → 1-2 pages    (cap = 2)
        medium  → 3-6 pages    (cap = 6)
        high    → 7-15 pages   (cap = 15)
        extreme → unlimited    (cap = 9_999, "within rate limits")
    """
    mapping = {"low": 2, "medium": 6, "high": 15, "extreme": 9_999}
    return mapping.get(level, 2)
