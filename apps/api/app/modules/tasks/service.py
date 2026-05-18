"""Tasks service — CRUD, kanban moves, reminder scheduling, audit hooks."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Iterable

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundException, ValidationException
from app.modules.audit.models import AuditLog
from app.modules.tasks.models import TASK_STATUSES, Task
from app.modules.tasks.schemas import TaskCreate, TaskMove, TaskUpdate

# Kanban column labels users see in the UI.
COLUMN_LABELS: dict[str, str] = {
    "todo": "To do",
    "doing": "In progress",
    "blocked": "Blocked",
    "done": "Done",
    "cancelled": "Cancelled",
}


# ── Audit helper ─────────────────────────────────────────────────────────────

def _audit(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID | None,
    action: str,
    task_id: uuid.UUID,
    metadata: dict | None = None,
) -> None:
    db.add(
        AuditLog(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            user_id=user_id,
            action=action,
            resource="task",
            resource_id=str(task_id),
            extra_metadata=metadata or {},
        )
    )


# ── Reads ────────────────────────────────────────────────────────────────────

async def list_tasks(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    *,
    page: int = 1,
    page_size: int = 25,
    status: str | None = None,
    assigned_user_id: uuid.UUID | None = None,
    related_type: str | None = None,
    related_id: uuid.UUID | None = None,
    q: str | None = None,
) -> tuple[list[Task], int]:
    query = select(Task).where(
        Task.tenant_id == tenant_id,
        Task.deleted_at.is_(None),
    )
    if status:
        query = query.where(Task.status == status)
    if assigned_user_id:
        query = query.where(Task.assigned_user_id == assigned_user_id)
    if related_type:
        query = query.where(Task.related_type == related_type)
    if related_id:
        query = query.where(Task.related_id == related_id)
    if q:
        like = f"%{q.lower()}%"
        query = query.where(func.lower(Task.title).like(like))

    total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar_one()
    items = (
        await db.execute(
            query.order_by(
                Task.status,
                Task.position.asc(),
                Task.created_at.desc(),
            )
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
    ).scalars().all()
    return list(items), total


async def get_task(db: AsyncSession, tenant_id: uuid.UUID, task_id: uuid.UUID) -> Task:
    result = await db.execute(
        select(Task).where(
            Task.id == task_id,
            Task.tenant_id == tenant_id,
            Task.deleted_at.is_(None),
        )
    )
    task = result.scalar_one_or_none()
    if not task:
        raise NotFoundException("Task")
    return task


async def get_board(db: AsyncSession, tenant_id: uuid.UUID) -> dict:
    """Return tasks grouped by status, ordered by position then due date."""
    result = await db.execute(
        select(Task)
        .where(Task.tenant_id == tenant_id, Task.deleted_at.is_(None))
        .order_by(Task.position.asc(), Task.due_at.asc().nullslast(), Task.created_at.desc())
    )
    rows = result.scalars().all()
    grouped: dict[str, list[Task]] = {s: [] for s in TASK_STATUSES if s != "cancelled"}
    for t in rows:
        if t.status in grouped:
            grouped[t.status].append(t)
    return {
        "columns": [
            {"status": status, "label": COLUMN_LABELS.get(status, status.title()), "items": items}
            for status, items in grouped.items()
        ]
    }


# ── Writes ───────────────────────────────────────────────────────────────────

async def _next_position(db: AsyncSession, tenant_id: uuid.UUID, status: str) -> int:
    result = await db.execute(
        select(func.max(Task.position)).where(
            Task.tenant_id == tenant_id,
            Task.status == status,
            Task.deleted_at.is_(None),
        )
    )
    cur = result.scalar() or 0
    return cur + 1


async def create_task(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    data: TaskCreate,
    *,
    user_id: uuid.UUID | None,
) -> Task:
    if data.status not in TASK_STATUSES:
        raise ValidationException(f"Invalid status '{data.status}'")
    position = await _next_position(db, tenant_id, data.status)

    task = Task(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        created_by_user_id=user_id,
        position=position,
        **data.model_dump(),
    )
    db.add(task)
    await db.flush()
    _audit(db, tenant_id=tenant_id, user_id=user_id, action="task.created", task_id=task.id)
    await db.commit()
    await db.refresh(task)

    # Schedule a reminder job if applicable.
    if task.reminder_at:
        await _schedule_reminder(task)
    return task


async def update_task(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    task_id: uuid.UUID,
    data: TaskUpdate,
    *,
    user_id: uuid.UUID | None,
) -> Task:
    task = await get_task(db, tenant_id, task_id)
    payload = data.model_dump(exclude_unset=True)
    old_status = task.status
    for field, value in payload.items():
        setattr(task, field, value)

    # If status changed via update (not via move), append to the end of the new column.
    if "status" in payload and payload["status"] != old_status:
        task.position = await _next_position(db, tenant_id, payload["status"])

    # Auto-stamp completed_at.
    if task.status == "done" and not task.completed_at:
        task.completed_at = datetime.now(timezone.utc)
    elif task.status != "done" and task.completed_at and "status" in payload:
        task.completed_at = None

    # Reset reminded flag if the reminder time changed.
    if "reminder_at" in payload:
        task.reminded_at = None

    _audit(
        db,
        tenant_id=tenant_id,
        user_id=user_id,
        action="task.updated",
        task_id=task.id,
        metadata={"fields": list(payload.keys())},
    )
    db.add(task)
    await db.commit()
    await db.refresh(task)

    if "reminder_at" in payload and task.reminder_at:
        await _schedule_reminder(task)
    return task


async def move_task(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    task_id: uuid.UUID,
    move: TaskMove,
    *,
    user_id: uuid.UUID | None,
) -> Task:
    if move.status not in TASK_STATUSES:
        raise ValidationException(f"Invalid status '{move.status}'")
    task = await get_task(db, tenant_id, task_id)

    old_status, old_position = task.status, task.position
    task.status = move.status
    task.position = move.position
    if task.status == "done" and not task.completed_at:
        task.completed_at = datetime.now(timezone.utc)
    elif task.status != "done":
        task.completed_at = None

    # Re-sequence the affected columns to avoid duplicate positions.
    await _resequence_column(db, tenant_id, move.status, exclude_id=task.id, insert_at=move.position, insert_task_id=task.id)
    if old_status != move.status:
        await _resequence_column(db, tenant_id, old_status, exclude_id=task.id)

    _audit(
        db,
        tenant_id=tenant_id,
        user_id=user_id,
        action="task.moved",
        task_id=task.id,
        metadata={"from": old_status, "to": move.status, "position": move.position},
    )
    db.add(task)
    await db.commit()
    await db.refresh(task)
    return task


async def delete_task(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    task_id: uuid.UUID,
    *,
    user_id: uuid.UUID | None,
) -> None:
    task = await get_task(db, tenant_id, task_id)
    task.deleted_at = datetime.now(timezone.utc)
    _audit(db, tenant_id=tenant_id, user_id=user_id, action="task.deleted", task_id=task.id)
    db.add(task)
    await db.commit()


# ── Internals ────────────────────────────────────────────────────────────────

async def _resequence_column(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    status: str,
    *,
    exclude_id: uuid.UUID | None = None,
    insert_at: int | None = None,
    insert_task_id: uuid.UUID | None = None,
) -> None:
    """Pack all positions in a column to 0..N-1, inserting `insert_task_id` at
    `insert_at` if both supplied. Keeps the kanban deterministic.
    """
    query = select(Task).where(
        Task.tenant_id == tenant_id,
        Task.status == status,
        Task.deleted_at.is_(None),
    )
    if exclude_id is not None:
        query = query.where(Task.id != exclude_id)
    rows = (await db.execute(query.order_by(Task.position.asc(), Task.created_at.asc()))).scalars().all()

    ordered: list[Task] = list(rows)
    if insert_at is not None and insert_task_id is not None:
        target = await get_task(db, tenant_id, insert_task_id)
        insert_index = max(0, min(insert_at, len(ordered)))
        ordered.insert(insert_index, target)

    for i, t in enumerate(ordered):
        if t.position != i:
            t.position = i
            db.add(t)


async def _schedule_reminder(task: Task) -> None:
    """Enqueue a reminder ARQ job. No-op if Redis isn't available (e.g. tests)."""
    try:
        from app.workers.queue import enqueue

        delay = (task.reminder_at - datetime.now(timezone.utc)).total_seconds() if task.reminder_at else 0
        await enqueue(
            "send_task_reminder",
            task_id=str(task.id),
            tenant_id=str(task.tenant_id),
            _defer_by=max(int(delay), 0),
        )
    except Exception:
        # Best-effort: if the queue is down we still keep the task, the
        # periodic sweep worker will pick it up.
        pass


async def find_due_reminders(db: AsyncSession, limit: int = 100) -> Iterable[Task]:
    """Return tasks whose reminder_at has elapsed but have not been notified yet."""
    now = datetime.now(timezone.utc)
    result = await db.execute(
        select(Task)
        .where(
            and_(
                Task.deleted_at.is_(None),
                Task.reminder_at.is_not(None),
                Task.reminder_at <= now,
                Task.reminded_at.is_(None),
                Task.status.in_(("todo", "doing", "blocked")),
            )
        )
        .limit(limit)
    )
    return result.scalars().all()
