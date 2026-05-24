import logging

from app.core.database import get_db_context

logger = logging.getLogger(__name__)


async def sweep_pwa_install_reminders_task(ctx: dict) -> int:
    """Cron: send 30m / 1h / 3h PWA install reminder emails."""
    async with get_db_context() as db:
        from app.modules.membership_rewards.services.pwa_install_reminders import sweep_pwa_install_reminders

        count = await sweep_pwa_install_reminders(db)
        logger.info("pwa_install_reminders sent=%s", count)
        return count
