"""Industry add-on background jobs."""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from sqlalchemy import select

from app.core.database import get_db_context
from app.modules.addons.common.constants import FEATURE_INDUSTRY_CRM
from app.modules.addons.common.entitlement import tenant_has_addon
from app.modules.addons.industry_models import IndustryRebookReminder

logger = logging.getLogger(__name__)


async def process_industry_rebook_reminders(ctx: dict) -> int:
    now = datetime.now(timezone.utc)
    sent = 0
    async with get_db_context() as db:
        rows = (
            await db.execute(
                select(IndustryRebookReminder).where(
                    IndustryRebookReminder.status == "pending",
                    IndustryRebookReminder.due_at <= now,
                )
            )
        ).scalars().all()
        for row in rows:
            if await tenant_has_addon(db, row.tenant_id, FEATURE_INDUSTRY_CRM):
                row.status = "sent"
                row.sent_at = now
                sent += 1
        await db.commit()
    logger.info("industry_rebook_reminders sent=%s", sent)
    return sent


async def refresh_maintenance_prediction_alerts(ctx: dict) -> int:
    async with get_db_context() as db:
        from app.modules.addons.industry_models import MaintenancePrediction

        preds = (
            await db.execute(
                select(MaintenancePrediction).where(MaintenancePrediction.confidence >= 70)
            )
        ).scalars().all()
        count = sum(
            1 for p in preds if await tenant_has_addon(db, p.tenant_id, FEATURE_INDUSTRY_CRM)
        )
    return count
