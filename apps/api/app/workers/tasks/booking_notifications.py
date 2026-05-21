"""Process booking notification queue (reminders, confirmations, abandoned recovery)."""
from __future__ import annotations

import logging

from app.core.database import get_db_context
from app.modules.booking.enterprise.automation import process_due_notifications

logger = logging.getLogger(__name__)


async def process_booking_notification_queue(ctx: dict) -> dict:  # noqa: ARG001
    async with get_db_context() as db:
        return await process_due_notifications(db, limit=100)
