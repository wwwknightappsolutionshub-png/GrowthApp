"""Background sync for Google Business reviews."""
from __future__ import annotations

import logging

from sqlalchemy import select

from app.core.database import get_db_context
from app.modules.integrations.models import TenantGoogleConnection
from app.modules.integrations import service

logger = logging.getLogger(__name__)


async def sync_all_google_reviews(ctx: dict) -> None:
    """Cron: refresh cached Google reviews for every connected tenant."""
    async with get_db_context() as db:
        tenant_ids = (
            await db.execute(
                select(TenantGoogleConnection.tenant_id).where(
                    TenantGoogleConnection.google_location_name.is_not(None)
                )
            )
        ).scalars().all()

    for tenant_id in tenant_ids:
        try:
            async with get_db_context() as db:
                await service.sync_google_reviews(db, tenant_id)
        except Exception:  # noqa: BLE001
            logger.exception("Google review sync failed for tenant %s", tenant_id)
