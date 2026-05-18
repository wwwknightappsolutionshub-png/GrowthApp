"""Background tasks for the Tasks module.

`send_task_reminder` is enqueued when a task gets a `reminder_at` value or
when the task is updated. The worker:
  1. Loads the task (skip if cancelled / done / deleted / already reminded)
  2. Resolves the assignee or task creator's contact details
  3. Sends an in-app Notification (Phase 1) + email (best-effort)
  4. Stamps `reminded_at` so we don't double-send
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone

from sqlalchemy import select

from app.adapters import get_email_adapter
from app.adapters.email.base import EmailMessage
from app.core.database import get_db_context
from app.modules.auth.models import User
from app.modules.tasks.models import Task
from app.modules.tenants.models import Tenant

logger = logging.getLogger(__name__)


async def send_task_reminder(ctx: dict, *, task_id: str, tenant_id: str) -> None:
    """Send a reminder for a Task whose reminder_at has elapsed."""
    async with get_db_context() as db:
        try:
            task_uuid = uuid.UUID(task_id)
            tenant_uuid = uuid.UUID(tenant_id)

            task = (
                await db.execute(
                    select(Task).where(
                        Task.id == task_uuid,
                        Task.tenant_id == tenant_uuid,
                        Task.deleted_at.is_(None),
                    )
                )
            ).scalar_one_or_none()

            if not task:
                logger.info("send_task_reminder: task %s missing", task_id)
                return
            if task.status in ("done", "cancelled"):
                logger.info("send_task_reminder: task %s already %s", task_id, task.status)
                return
            if task.reminded_at:
                logger.info("send_task_reminder: task %s already reminded", task_id)
                return

            recipient_id = task.assigned_user_id or task.created_by_user_id
            if not recipient_id:
                logger.info("send_task_reminder: task %s has no recipient", task_id)
                return

            recipient = (
                await db.execute(select(User).where(User.id == recipient_id))
            ).scalar_one_or_none()
            tenant = (
                await db.execute(select(Tenant).where(Tenant.id == tenant_uuid))
            ).scalar_one_or_none()
            if not recipient or not tenant:
                logger.info("send_task_reminder: recipient/tenant missing for task %s", task_id)
                return

            # In-app notification (best-effort — Notification module is added in Phase 1)
            try:
                from app.modules.notifications import service as notif_service

                await notif_service.create_notification(
                    db,
                    tenant_id=tenant_uuid,
                    user_id=recipient.id,
                    kind="task.reminder",
                    title=f"Reminder: {task.title}",
                    body=task.description or "",
                    link=f"/tasks/{task.id}",
                    extra={"task_id": str(task.id), "due_at": task.due_at.isoformat() if task.due_at else None},
                )
            except Exception as exc:
                logger.warning("send_task_reminder: in-app notification failed: %s", exc)

            # Email reminder (best-effort)
            if recipient.email:
                try:
                    subject = f"[{tenant.name}] Task reminder: {task.title}"
                    html = f"""
                    <p>Hi {recipient.full_name.split(' ')[0]},</p>
                    <p>This is your reminder for the task <strong>{task.title}</strong>{
                      f" — due {task.due_at.strftime('%a %d %b at %H:%M')}" if task.due_at else ''
                    }.</p>
                    {f'<p>{task.description}</p>' if task.description else ''}
                    <p>Open the task in CustomerFlow AI to update its status.</p>
                    """
                    await get_email_adapter().send(EmailMessage(
                        to=recipient.email,
                        to_name=recipient.full_name,
                        subject=subject,
                        html_body=html,
                    ))
                except Exception as exc:
                    logger.warning("send_task_reminder: email failed for %s: %s", recipient.email, exc)

            task.reminded_at = datetime.now(timezone.utc)
            db.add(task)
            await db.commit()
            logger.info("send_task_reminder: delivered task=%s user=%s", task_id, recipient.email)

        except Exception as exc:
            logger.error("send_task_reminder failed task=%s err=%s", task_id, exc, exc_info=True)
            raise


async def sweep_overdue_task_reminders(ctx: dict) -> int:
    """Cron-style sweep that picks up any reminders missed due to worker downtime.

    Returns the number of reminders dispatched.
    """
    from app.modules.tasks import service as tasks_service

    async with get_db_context() as db:
        due = list(await tasks_service.find_due_reminders(db, limit=200))

    for task in due:
        try:
            await send_task_reminder(ctx, task_id=str(task.id), tenant_id=str(task.tenant_id))
        except Exception:
            # send_task_reminder already logs the error
            continue
    return len(due)
