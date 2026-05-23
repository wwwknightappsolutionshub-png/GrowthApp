import logging

from app.core.database import get_db_context

logger = logging.getLogger(__name__)


async def sweep_service_renewal_reminders(ctx: dict) -> int:
    """Cron: email tenant owners 7 days before customer service renewal."""
    async with get_db_context() as db:
        from app.modules.quotes_invoices.recurrency import sweep_service_renewal_reminders as _sweep

        count = await _sweep(db)
        logger.info("service_renewal_reminders sent=%s", count)
        return count
