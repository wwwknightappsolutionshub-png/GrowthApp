"""ARQ tasks for the outreach engine."""
from __future__ import annotations

import logging

from app.core.database import AsyncSessionLocal
from app.modules.outreach import service as outreach_service

logger = logging.getLogger(__name__)


async def process_outreach_dispatch(_ctx) -> int:
    """Pick the next batch of due outreach enrolments and send their step.

    Runs every 5 minutes. Returns the number of sends attempted.
    """
    sent = 0
    async with AsyncSessionLocal() as db:
        sent = await outreach_service.process_due_enrolments(db, limit=100)
        if sent:
            logger.info("outreach dispatch: %s send(s)", sent)
    return sent
