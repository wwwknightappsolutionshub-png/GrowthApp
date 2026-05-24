"""Web push delivery for loyalty portal customers."""

from __future__ import annotations

import asyncio
import json
import logging
import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.modules.membership_rewards.landing import rewards_portal_url
from app.modules.membership_rewards.models import MrCustomerPushSubscription
from app.modules.notifications.service import push_is_configured
from app.modules.tenants.models import Tenant

logger = logging.getLogger(__name__)


async def _send_web_push(endpoint: str, p256dh: str, auth: str, payload: dict[str, Any]) -> bool:
    if not push_is_configured():
        return False
    try:
        from pywebpush import WebPushException, webpush
    except Exception:
        return False

    subscription_info = {"endpoint": endpoint, "keys": {"p256dh": p256dh, "auth": auth}}

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


async def send_loyalty_push(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    customer_id: uuid.UUID,
    title: str,
    body: str,
    path: str = "dashboard",
) -> int:
    """Send a push notification to all active loyalty portal subscriptions for a customer."""
    if not push_is_configured():
        return 0

    tenant = await db.get(Tenant, tenant_id)
    tenant_slug = tenant.slug if tenant else str(tenant_id)
    url = rewards_portal_url(tenant_slug, subpath=path)

    subscriptions = list(
        (
            await db.execute(
                select(MrCustomerPushSubscription).where(
                    MrCustomerPushSubscription.tenant_id == tenant_id,
                    MrCustomerPushSubscription.customer_id == customer_id,
                )
            )
        ).scalars().all()
    )
    if not subscriptions:
        return 0

    payload = {"title": title, "body": body, "data": {"url": url}}
    sent = 0
    for sub in subscriptions:
        ok = await _send_web_push(sub.endpoint, sub.p256dh, sub.auth, payload)
        if ok:
            sent += 1
        else:
            await db.delete(sub)
    if sent < len(subscriptions):
        await db.commit()
    return sent
