"""In-app + push delivery for loyalty wallet customers."""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundException
from app.modules.membership_rewards.models import MrCustomerNotification
from app.modules.membership_rewards.services.customer_push_service import send_loyalty_push

logger = logging.getLogger(__name__)


async def create_customer_notification(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    customer_id: uuid.UUID,
    title: str,
    body: str | None,
    kind: str = "loyalty.system",
    link: str | None = None,
    extra: dict[str, Any] | None = None,
) -> MrCustomerNotification:
    row = MrCustomerNotification(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        customer_id=customer_id,
        kind=kind,
        title=title,
        body=body,
        link=link,
        extra=extra or {},
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return row


async def notify_loyalty_customer(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    customer_id: uuid.UUID,
    title: str,
    body: str,
    path: str = "dashboard",
    kind: str = "loyalty.system",
    send_push: bool = True,
) -> dict[str, Any]:
    """Persist an in-app wallet notification and optionally deliver web push."""
    notif = await create_customer_notification(
        db,
        tenant_id=tenant_id,
        customer_id=customer_id,
        title=title,
        body=body,
        kind=kind,
        link=path,
    )

    push_sent = 0
    if send_push:
        try:
            push_sent = await send_loyalty_push(
                db,
                tenant_id=tenant_id,
                customer_id=customer_id,
                title=title,
                body=body,
                path=path,
                notification_id=notif.id,
            )
        except Exception:
            logger.exception(
                "loyalty push failed tenant=%s customer=%s notification=%s",
                tenant_id,
                customer_id,
                notif.id,
            )

    return {"notification_id": notif.id, "push_sent": push_sent}


async def unread_count(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    customer_id: uuid.UUID,
) -> int:
    return int(
        (
            await db.execute(
                select(func.count())
                .select_from(MrCustomerNotification)
                .where(
                    MrCustomerNotification.tenant_id == tenant_id,
                    MrCustomerNotification.customer_id == customer_id,
                    MrCustomerNotification.read_at.is_(None),
                )
            )
        ).scalar_one()
    )


async def list_customer_notifications(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    customer_id: uuid.UUID,
    limit: int = 25,
    offset: int = 0,
) -> tuple[list[MrCustomerNotification], int]:
    base = select(MrCustomerNotification).where(
        MrCustomerNotification.tenant_id == tenant_id,
        MrCustomerNotification.customer_id == customer_id,
    )
    unread = int(
        (
            await db.execute(
                select(func.count())
                .select_from(MrCustomerNotification)
                .where(
                    MrCustomerNotification.tenant_id == tenant_id,
                    MrCustomerNotification.customer_id == customer_id,
                    MrCustomerNotification.read_at.is_(None),
                )
            )
        ).scalar_one()
    )
    rows = list(
        (
            await db.execute(
                base.order_by(MrCustomerNotification.created_at.desc()).limit(limit).offset(offset)
            )
        ).scalars().all()
    )
    return rows, unread


async def mark_read(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    customer_id: uuid.UUID,
    notification_id: uuid.UUID,
) -> MrCustomerNotification:
    row = (
        await db.execute(
            select(MrCustomerNotification).where(
                MrCustomerNotification.id == notification_id,
                MrCustomerNotification.tenant_id == tenant_id,
                MrCustomerNotification.customer_id == customer_id,
            )
        )
    ).scalar_one_or_none()
    if not row:
        raise NotFoundException("Notification")
    if not row.read_at:
        row.read_at = datetime.now(timezone.utc)
        db.add(row)
        await db.commit()
        await db.refresh(row)
    return row


async def mark_all_read(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    customer_id: uuid.UUID,
) -> int:
    now = datetime.now(timezone.utc)
    result = await db.execute(
        update(MrCustomerNotification)
        .where(
            MrCustomerNotification.tenant_id == tenant_id,
            MrCustomerNotification.customer_id == customer_id,
            MrCustomerNotification.read_at.is_(None),
        )
        .values(read_at=now)
    )
    await db.commit()
    return int(result.rowcount or 0)
