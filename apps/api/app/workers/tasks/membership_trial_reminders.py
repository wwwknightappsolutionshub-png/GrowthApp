import logging

from app.core.database import get_db_context

logger = logging.getLogger(__name__)


async def sweep_membership_trial_reminders_task(ctx: dict) -> int:
    """Cron: day 3/6/15 membership & rewards trial emails and in-app reminders."""
    async with get_db_context() as db:
        from app.modules.membership_rewards.reminders import sweep_membership_trial_reminders

        count = await sweep_membership_trial_reminders(db)
        logger.info("membership_trial_reminders actions=%s", count)
        return count
