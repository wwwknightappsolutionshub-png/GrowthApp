import logging

from app.core.database import get_db_context

logger = logging.getLogger(__name__)


async def sweep_loyalty_birthday_bonuses_task(ctx: dict) -> int:
    """Cron: award birthday bonus points for customers whose birthday is today."""
    async with get_db_context() as db:
        from app.modules.membership_rewards.services.loyalty_maintenance import sweep_birthday_bonuses

        return await sweep_birthday_bonuses(db)


async def sweep_loyalty_expiring_points_reminders_task(ctx: dict) -> int:
    """Cron: push reminders for points expiring within the next week."""
    async with get_db_context() as db:
        from app.modules.membership_rewards.services.loyalty_maintenance import (
            sweep_expiring_points_reminders,
        )

        return await sweep_expiring_points_reminders(db)
