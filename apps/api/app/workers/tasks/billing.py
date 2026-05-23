import logging
from app.core.database import get_db_context

logger = logging.getLogger(__name__)


async def sync_stripe_subscription(ctx: dict, *, stripe_subscription_id: str):
    """Sync Stripe subscription status to DB."""
    logger.info("Syncing Stripe subscription: %s", stripe_subscription_id)
    async with get_db_context() as db:
        from sqlalchemy import select
        from app.modules.billing.models import Subscription
        from datetime import datetime, timezone
        import stripe
        from app.core.config import settings

        stripe.api_key = settings.STRIPE_SECRET_KEY

        try:
            sub = stripe.Subscription.retrieve(stripe_subscription_id)
        except Exception as e:
            logger.error("Stripe API error: %s", e)
            return

        db_result = await db.execute(
            select(Subscription).where(Subscription.stripe_subscription_id == stripe_subscription_id)
        )
        db_sub = db_result.scalar_one_or_none()
        if not db_sub:
            logger.warning("Subscription not found in DB: %s", stripe_subscription_id)
            return

        db_sub.status = sub.status
        db_sub.current_period_start = datetime.fromtimestamp(sub.current_period_start, tz=timezone.utc)
        db_sub.current_period_end = datetime.fromtimestamp(sub.current_period_end, tz=timezone.utc)
        if sub.cancel_at:
            db_sub.cancel_at = datetime.fromtimestamp(sub.cancel_at, tz=timezone.utc)
        db.add(db_sub)
        await db.commit()
        logger.info("Subscription %s synced: status=%s", stripe_subscription_id, sub.status)
        if db_sub.status in ("active", "trialing"):
            from app.modules.referrals.service import on_subscription_active_for_tenant

            await on_subscription_active_for_tenant(
                db, tenant_id=db_sub.tenant_id, stripe_status=str(db_sub.status)
            )

        from app.modules.membership_rewards.billing import sync_addon_from_stripe_subscription

        stripe_sub_dict = sub.to_dict() if hasattr(sub, "to_dict") else dict(sub)
        await sync_addon_from_stripe_subscription(
            db, stripe_subscription_id=stripe_subscription_id, stripe_sub=stripe_sub_dict
        )
