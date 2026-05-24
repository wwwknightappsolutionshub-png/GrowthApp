"""Dispatch super-admin Communication Hub broadcasts to tenants and freelancers."""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters import get_sms_adapter
from app.adapters.email import get_email_adapter
from app.adapters.email.base import EmailMessage
from app.adapters.sms.base import SMSMessage
from app.core.rbac import Broadcast
from app.modules.auth.models import User
from app.modules.notifications.models import PushSubscription
from app.modules.notifications.service import create_notification, push_is_configured
from app.modules.notifications.service import _send_web_push  # noqa: PLC2701
from app.modules.tenants.models import TenantMember

logger = logging.getLogger(__name__)

AUDIENCES = frozenset({"tenant_owners", "freelancers", "all_users", "tenant_staff"})


async def _resolve_recipients(
    db: AsyncSession,
    audience: str,
) -> list[tuple[uuid.UUID, uuid.UUID, User]]:
    """Return (tenant_id, user_id, user) tuples for delivery."""
    if audience not in AUDIENCES:
        audience = "tenant_owners"

    if audience == "freelancers":
        users = (
            await db.execute(
                select(User).where(
                    User.deleted_at.is_(None),
                    User.user_type == "freelancer",
                )
            )
        ).scalars().all()
        out: list[tuple[uuid.UUID, uuid.UUID, User]] = []
        for user in users:
            member = (
                await db.execute(
                    select(TenantMember).where(TenantMember.user_id == user.id).limit(1)
                )
            ).scalar_one_or_none()
            if member:
                out.append((member.tenant_id, user.id, user))
        return out

    q = (
        select(TenantMember, User)
        .join(User, TenantMember.user_id == User.id)
        .where(User.deleted_at.is_(None))
    )
    if audience == "tenant_owners":
        q = q.where(TenantMember.role == "owner")
    elif audience == "tenant_staff":
        pass  # all members
    elif audience == "all_users":
        pass

    rows = (await db.execute(q)).all()
    return [(member.tenant_id, user.id, user) for member, user in rows]


async def _send_push_to_user(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
    title: str,
    body: str,
    link: str,
) -> bool:
    if not push_is_configured():
        return False
    subscriptions = (
        await db.execute(
            select(PushSubscription).where(
                PushSubscription.tenant_id == tenant_id,
                PushSubscription.user_id == user_id,
                PushSubscription.is_active == True,  # noqa: E712
            )
        )
    ).scalars().all()
    sent = False
    for sub in subscriptions:
        ok = await _send_web_push(
            sub,
            {
                "title": title,
                "body": body,
                "url": link,
                "tag": f"cf:broadcast:{uuid.uuid4()}",
            },
        )
        if ok:
            sent = True
        else:
            sub.is_active = False
            db.add(sub)
    return sent


async def dispatch_broadcast(db: AsyncSession, broadcast_id: uuid.UUID) -> dict:
    """Send a pending Broadcast record. Updates status and recipient_count."""
    broadcast = await db.get(Broadcast, broadcast_id)
    if not broadcast:
        raise ValueError("Broadcast not found")
    if broadcast.status == "sent":
        return {"status": "sent", "recipient_count": broadcast.recipient_count}

    audience = (broadcast.target_filter or {}).get("audience", "tenant_owners")
    link = (broadcast.target_filter or {}).get("link", "/dashboard/notifications")
    title = broadcast.name
    body = broadcast.body
    channel = broadcast.channel

    recipients = await _resolve_recipients(db, audience)
    delivered = 0

    for tenant_id, user_id, user in recipients:
        try:
            ok = False
            if channel in ("in_app", "push"):
                await create_notification(
                    db,
                    tenant_id=tenant_id,
                    user_id=user_id,
                    kind="system",
                    title=title,
                    body=body,
                    link=link,
                    extra={"broadcast_id": str(broadcast_id)},
                )
                ok = True
            if channel in ("push", "push_only"):
                ok = (
                    await _send_push_to_user(
                        db,
                        tenant_id=tenant_id,
                        user_id=user_id,
                        title=title,
                        body=body,
                        link=link,
                    )
                ) or ok
            if channel == "email" and user.email:
                await get_email_adapter().send(
                    EmailMessage(
                        to=user.email,
                        to_name=user.full_name,
                        subject=title,
                        html_body=f"<p>{body}</p><p><a href=\"{link}\">Open CustomerFlow AI</a></p>",
                    )
                )
                ok = True
            if channel == "sms" and user.phone:
                await get_sms_adapter().send(SMSMessage(to=user.phone, body=f"{title}: {body}"))
                ok = True
            if ok:
                delivered += 1
        except Exception:
            logger.exception(
                "broadcast delivery failed broadcast=%s user=%s",
                broadcast_id,
                user_id,
            )

    broadcast.status = "sent"
    broadcast.sent_at = datetime.now(timezone.utc)
    broadcast.recipient_count = delivered
    await db.commit()
    return {"status": broadcast.status, "recipient_count": delivered}


async def preview_broadcast_recipients(db: AsyncSession, audience: str) -> int:
    rows = await _resolve_recipients(db, audience)
    return len(rows)
