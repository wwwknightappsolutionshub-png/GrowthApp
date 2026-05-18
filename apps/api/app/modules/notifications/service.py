"""Notification service.

Two paths:

  1. `create_notification` — internal; called by other modules (tasks, leads,
     billing, etc). Persists a row + best-effort WebSocket push.
  2. List/mark-read/archive — exposed via REST for the in-app bell.
"""
from __future__ import annotations

import asyncio
import json
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import NotFoundException
from app.modules.notifications.models import (
    Notification,
    NotificationPreference,
    PushSubscription,
)


PUSH_ENABLED_KINDS = {
    "lead.new",
    "booking.reminder",
    "task.reminder",
    "invoice.paid",
    "invoice.overdue",
    "quote.accepted",
}

PREFERENCE_LABELS = {
    "lead.new": "New leads",
    "booking.reminder": "Booking reminders",
    "task.reminder": "Overdue tasks and reminders",
    "invoice.paid": "Invoice paid",
    "invoice.overdue": "Invoice overdue",
    "quote.accepted": "Quote accepted",
    "message.inbound": "Inbound messages",
    "review.received": "New reviews",
    "system": "System notices",
}

PRIVACY_SAFE_PUSH = {
    "lead.new": ("New lead", "You have a new lead in CustomerFlow AI."),
    "booking.reminder": ("Booking reminder", "A booking reminder is due."),
    "task.reminder": ("Task reminder", "A task needs your attention."),
    "invoice.paid": ("Invoice paid", "An invoice has been paid."),
    "invoice.overdue": ("Invoice overdue", "An invoice is overdue."),
    "quote.accepted": ("Quote accepted", "A customer accepted a quote."),
}


# ── In-process WebSocket fan-out ─────────────────────────────────────────────
# Per-(tenant_id, user_id) subscribers. Each subscriber is an asyncio.Queue
# the router writes Notification dicts into. The router consumes from this
# queue and emits over the WebSocket.
#
# In a multi-replica deploy this should be backed by Redis pub/sub; for a
# single-process FastAPI dev/preview deployment the in-process registry is
# sufficient. The interface (`subscribe`/`publish`) is identical so swapping
# in a Redis adapter is a one-file change.
_subscribers: dict[tuple[str, str], set[asyncio.Queue]] = {}


def subscribe(tenant_id: uuid.UUID, user_id: uuid.UUID) -> asyncio.Queue:
    key = (str(tenant_id), str(user_id))
    queue: asyncio.Queue = asyncio.Queue()
    _subscribers.setdefault(key, set()).add(queue)
    return queue


def unsubscribe(tenant_id: uuid.UUID, user_id: uuid.UUID, queue: asyncio.Queue) -> None:
    key = (str(tenant_id), str(user_id))
    if key in _subscribers:
        _subscribers[key].discard(queue)
        if not _subscribers[key]:
            del _subscribers[key]


def _publish(notif: Notification) -> None:
    """Push a serialised notification to every subscribed WebSocket queue.

    Tenant-wide (user_id IS NULL) notifications go to every subscriber for the
    tenant; user-specific notifications go only to that user's queues.
    """
    payload = {
        "id": str(notif.id),
        "tenant_id": str(notif.tenant_id),
        "user_id": str(notif.user_id) if notif.user_id else None,
        "kind": notif.kind,
        "title": notif.title,
        "body": notif.body,
        "link": notif.link,
        "extra": notif.extra or {},
        "read_at": notif.read_at.isoformat() if notif.read_at else None,
        "created_at": notif.created_at.isoformat() if notif.created_at else None,
    }
    for (tid, _uid), queues in list(_subscribers.items()):
        if tid != str(notif.tenant_id):
            continue
        if notif.user_id is not None and _uid != str(notif.user_id):
            continue
        for q in list(queues):
            try:
                q.put_nowait(payload)
            except asyncio.QueueFull:
                pass


def push_public_key() -> str:
    return settings.VAPID_PUBLIC_KEY


def push_is_configured() -> bool:
    return bool(settings.VAPID_PUBLIC_KEY and settings.VAPID_PRIVATE_KEY and settings.VAPID_SUBJECT)


async def upsert_push_subscription(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
    endpoint: str,
    p256dh: str,
    auth: str,
    user_agent: str | None = None,
) -> PushSubscription:
    row = (
        await db.execute(select(PushSubscription).where(PushSubscription.endpoint == endpoint))
    ).scalar_one_or_none()
    if row:
        row.tenant_id = tenant_id
        row.user_id = user_id
        row.p256dh = p256dh
        row.auth = auth
        row.user_agent = user_agent
        row.is_active = True
    else:
        row = PushSubscription(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            user_id=user_id,
            endpoint=endpoint,
            p256dh=p256dh,
            auth=auth,
            user_agent=user_agent,
            is_active=True,
        )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return row


async def delete_push_subscription(db: AsyncSession, *, user_id: uuid.UUID, endpoint: str) -> int:
    result = await db.execute(
        delete(PushSubscription).where(
            PushSubscription.user_id == user_id,
            PushSubscription.endpoint == endpoint,
        )
    )
    await db.commit()
    return result.rowcount or 0


async def list_preferences(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
) -> list[dict[str, Any]]:
    rows = (
        await db.execute(
            select(NotificationPreference).where(
                NotificationPreference.tenant_id == tenant_id,
                NotificationPreference.user_id == user_id,
            )
        )
    ).scalars().all()
    by_kind = {row.kind: row for row in rows}
    kinds = sorted(set(PREFERENCE_LABELS) | {row.kind for row in rows})
    return [
        {
            "kind": kind,
            "label": PREFERENCE_LABELS.get(kind, kind.replace(".", " ").title()),
            "in_app_enabled": by_kind[kind].in_app_enabled if kind in by_kind else True,
            "push_enabled": by_kind[kind].push_enabled if kind in by_kind else kind in PUSH_ENABLED_KINDS,
        }
        for kind in kinds
    ]


async def update_preferences(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
    preferences: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    existing = (
        await db.execute(
            select(NotificationPreference).where(
                NotificationPreference.tenant_id == tenant_id,
                NotificationPreference.user_id == user_id,
            )
        )
    ).scalars().all()
    by_kind = {row.kind: row for row in existing}
    for pref in preferences:
        kind = str(pref["kind"])
        row = by_kind.get(kind)
        if row:
            row.in_app_enabled = bool(pref.get("in_app_enabled", True))
            row.push_enabled = bool(pref.get("push_enabled", False))
        else:
            row = NotificationPreference(
                id=uuid.uuid4(),
                tenant_id=tenant_id,
                user_id=user_id,
                kind=kind,
                in_app_enabled=bool(pref.get("in_app_enabled", True)),
                push_enabled=bool(pref.get("push_enabled", False)),
            )
        db.add(row)
    await db.commit()
    return await list_preferences(db, tenant_id=tenant_id, user_id=user_id)


async def _push_allowed(db: AsyncSession, *, tenant_id: uuid.UUID, user_id: uuid.UUID, kind: str) -> bool:
    pref = (
        await db.execute(
            select(NotificationPreference).where(
                NotificationPreference.tenant_id == tenant_id,
                NotificationPreference.user_id == user_id,
                NotificationPreference.kind == kind,
            )
        )
    ).scalar_one_or_none()
    if pref:
        return pref.push_enabled
    return kind in PUSH_ENABLED_KINDS


async def _send_web_push(subscription: PushSubscription, payload: dict[str, Any]) -> bool:
    if not push_is_configured():
        return False
    try:
        from pywebpush import WebPushException, webpush
    except Exception:
        return False

    subscription_info = {
        "endpoint": subscription.endpoint,
        "keys": {"p256dh": subscription.p256dh, "auth": subscription.auth},
    }

    def _send() -> bool:
        try:
            webpush(
                subscription_info=subscription_info,
                data=json.dumps(payload),
                vapid_private_key=settings.VAPID_PRIVATE_KEY,
                vapid_claims={"sub": settings.VAPID_SUBJECT},
                ttl=60 * 60,
            )
            return True
        except WebPushException as exc:
            status = getattr(getattr(exc, "response", None), "status_code", None)
            return status not in (404, 410)
        except Exception:
            return True

    return await asyncio.to_thread(_send)


async def send_push_for_notification(db: AsyncSession, notif: Notification) -> None:
    safe = PRIVACY_SAFE_PUSH.get(notif.kind)
    if not safe or not push_is_configured():
        return

    title, body = safe
    query = select(PushSubscription).where(
        PushSubscription.tenant_id == notif.tenant_id,
        PushSubscription.is_active == True,  # noqa: E712
    )
    if notif.user_id is not None:
        query = query.where(PushSubscription.user_id == notif.user_id)

    subscriptions = (await db.execute(query)).scalars().all()
    for subscription in subscriptions:
        if not await _push_allowed(
            db,
            tenant_id=subscription.tenant_id,
            user_id=subscription.user_id,
            kind=notif.kind,
        ):
            continue
        still_valid = await _send_web_push(
            subscription,
            {
                "title": title,
                "body": body,
                "url": notif.link or "/dashboard",
                "tag": f"cf:{notif.kind}:{notif.id}",
                "notification_id": str(notif.id),
            },
        )
        if not still_valid:
            subscription.is_active = False
            db.add(subscription)
    await db.commit()


# ── Writes ───────────────────────────────────────────────────────────────────

async def create_notification(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID | None,
    kind: str,
    title: str,
    body: str | None = None,
    link: str | None = None,
    extra: dict | None = None,
) -> Notification:
    notif = Notification(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        user_id=user_id,
        kind=kind,
        title=title,
        body=body,
        link=link,
        extra=extra or {},
    )
    db.add(notif)
    await db.commit()
    await db.refresh(notif)
    _publish(notif)
    await send_push_for_notification(db, notif)
    return notif


async def mark_read(db: AsyncSession, tenant_id: uuid.UUID, user_id: uuid.UUID, notification_id: uuid.UUID) -> Notification:
    notif = (
        await db.execute(
            select(Notification).where(
                Notification.id == notification_id,
                Notification.tenant_id == tenant_id,
            )
        )
    ).scalar_one_or_none()
    if not notif:
        raise NotFoundException("Notification")
    if notif.user_id is not None and notif.user_id != user_id:
        raise NotFoundException("Notification")
    if not notif.read_at:
        notif.read_at = datetime.now(timezone.utc)
        db.add(notif)
        await db.commit()
        await db.refresh(notif)
    return notif


async def mark_all_read(db: AsyncSession, tenant_id: uuid.UUID, user_id: uuid.UUID) -> int:
    now = datetime.now(timezone.utc)
    result = await db.execute(
        update(Notification)
        .where(
            Notification.tenant_id == tenant_id,
            (Notification.user_id == user_id) | (Notification.user_id.is_(None)),
            Notification.read_at.is_(None),
        )
        .values(read_at=now)
    )
    await db.commit()
    return result.rowcount or 0


async def archive(db: AsyncSession, tenant_id: uuid.UUID, user_id: uuid.UUID, notification_id: uuid.UUID) -> Notification:
    notif = (
        await db.execute(
            select(Notification).where(
                Notification.id == notification_id,
                Notification.tenant_id == tenant_id,
            )
        )
    ).scalar_one_or_none()
    if not notif:
        raise NotFoundException("Notification")
    if notif.user_id is not None and notif.user_id != user_id:
        raise NotFoundException("Notification")
    notif.archived_at = datetime.now(timezone.utc)
    db.add(notif)
    await db.commit()
    await db.refresh(notif)
    return notif


# ── Reads ────────────────────────────────────────────────────────────────────

async def list_notifications(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
    *,
    page: int = 1,
    page_size: int = 25,
    unread_only: bool = False,
    include_archived: bool = False,
) -> tuple[list[Notification], int, int]:
    base = select(Notification).where(
        Notification.tenant_id == tenant_id,
        (Notification.user_id == user_id) | (Notification.user_id.is_(None)),
    )
    if not include_archived:
        base = base.where(Notification.archived_at.is_(None))

    list_q = base
    if unread_only:
        list_q = list_q.where(Notification.read_at.is_(None))

    total = (await db.execute(select(func.count()).select_from(base.subquery()))).scalar_one()
    unread = (
        await db.execute(
            select(func.count()).select_from(
                base.where(Notification.read_at.is_(None)).subquery()
            )
        )
    ).scalar_one()
    items = (
        await db.execute(
            list_q.order_by(Notification.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
    ).scalars().all()
    return list(items), int(total), int(unread)
