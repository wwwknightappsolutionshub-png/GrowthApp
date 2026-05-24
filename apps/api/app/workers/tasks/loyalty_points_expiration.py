import logging

from app.core.database import get_db_context

logger = logging.getLogger(__name__)


async def sweep_loyalty_points_expiration_task(ctx: dict) -> int:
    """Cron: expire loyalty points past their expires_at timestamp."""
    async with get_db_context() as db:
        from app.modules.membership_rewards.engines.earning_engine import sweep_expired_points

        count = await sweep_expired_points(db)
        logger.info("loyalty_points_expiration expired=%s", count)
        return count
