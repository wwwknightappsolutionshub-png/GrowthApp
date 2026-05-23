import logging

from app.core.database import get_db_context

logger = logging.getLogger(__name__)


async def run_accounting_recurring(ctx: dict) -> int:
    async with get_db_context() as db:
        from app.modules.accounting import service

        return await service.run_due_recurring(db)


async def sweep_invoice_reminders(ctx: dict) -> int:
    async with get_db_context() as db:
        from app.modules.accounting import service

        return await service.sweep_overdue_and_reminders(db)
