"""ARQ cron jobs for Google Business Profile sync."""
from __future__ import annotations

import logging

from sqlalchemy import select

from app.core.database import get_db_context
from app.modules.integrations.google import service as google_service
from app.modules.integrations.models import TenantGoogleConnection, TenantGoogleCredentials

logger = logging.getLogger(__name__)

_SYNC_HANDLERS = {
    "reviews": google_service.sync_reviews,
    "messages": google_service.sync_messages,
    "posts": google_service.sync_posts,
    "photos": google_service.sync_photos,
    "analytics": google_service.sync_analytics,
}


async def _connected_tenant_ids() -> list:
    async with get_db_context() as db:
        conn_ids = (
            await db.execute(
                select(TenantGoogleConnection.tenant_id).where(
                    TenantGoogleConnection.google_location_name.is_not(None)
                )
            )
        ).scalars().all()
        cred_ids = (
            await db.execute(
                select(TenantGoogleCredentials.tenant_id).where(
                    TenantGoogleCredentials.status == "connected"
                )
            )
        ).scalars().all()
    return list({*conn_ids, *cred_ids})


async def _run_sync_for_all(data_type: str) -> None:
    handler = _SYNC_HANDLERS[data_type]
    for tenant_id in await _connected_tenant_ids():
        try:
            async with get_db_context() as db:
                await handler(db, tenant_id)
        except Exception:  # noqa: BLE001
            logger.exception("Google %s sync failed tenant=%s", data_type, tenant_id)


async def sync_google_reviews_job(ctx: dict) -> None:
    await _run_sync_for_all("reviews")


async def sync_google_messages_job(ctx: dict) -> None:
    await _run_sync_for_all("messages")


async def sync_google_posts_job(ctx: dict) -> None:
    await _run_sync_for_all("posts")


async def sync_google_photos_job(ctx: dict) -> None:
    await _run_sync_for_all("photos")


async def sync_google_analytics_job(ctx: dict) -> None:
    await _run_sync_for_all("analytics")
