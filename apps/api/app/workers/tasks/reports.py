import logging
from app.core.database import get_db_context

logger = logging.getLogger(__name__)


async def weekly_performance_report(ctx: dict, *, tenant_id: str):
    """Generate and send the weekly performance email."""
    logger.info("Generating weekly report for tenant %s", tenant_id)
    async with get_db_context() as db:
        from sqlalchemy import select, func
        from app.modules.tenants.models import Tenant
        from app.modules.leads.models import Lead
        from app.modules.crm.models import Deal
        from app.modules.reputation.models import Review
        import uuid
        from datetime import datetime, timedelta, timezone

        tenant_result = await db.execute(select(Tenant).where(Tenant.id == uuid.UUID(tenant_id)))
        tenant = tenant_result.scalar_one_or_none()
        if not tenant or not tenant.email:
            return

        week_ago = datetime.now(timezone.utc) - timedelta(days=7)

        # Leads this week
        leads_result = await db.execute(
            select(func.count(Lead.id)).where(
                Lead.tenant_id == uuid.UUID(tenant_id),
                Lead.created_at >= week_ago,
            )
        )
        leads_count = leads_result.scalar_one() or 0

        # Reviews this week
        reviews_result = await db.execute(
            select(func.count(Review.id)).where(
                Review.tenant_id == uuid.UUID(tenant_id),
                Review.created_at >= week_ago,
            )
        )
        reviews_count = reviews_result.scalar_one() or 0

        # Avg rating
        avg_result = await db.execute(
            select(func.avg(Review.rating)).where(Review.tenant_id == uuid.UUID(tenant_id))
        )
        avg_rating = round(float(avg_result.scalar_one() or 0), 1)

        from app.adapters import get_email_adapter
        from app.adapters.email.base import EmailMessage
        from app.core.config import settings

        html = f"""
        <h2>Your Weekly CustomerFlow AI Report — {tenant.name}</h2>
        <table style="border-collapse:collapse;width:100%">
          <tr><td style="padding:8px;border:1px solid #ddd"><strong>New Leads</strong></td><td style="padding:8px;border:1px solid #ddd">{leads_count}</td></tr>
          <tr><td style="padding:8px;border:1px solid #ddd"><strong>New Reviews</strong></td><td style="padding:8px;border:1px solid #ddd">{reviews_count}</td></tr>
          <tr><td style="padding:8px;border:1px solid #ddd"><strong>Avg Rating</strong></td><td style="padding:8px;border:1px solid #ddd">{'⭐' * int(avg_rating)} ({avg_rating})</td></tr>
        </table>
        <p><a href="{settings.FRONTEND_URL}/dashboard">View your dashboard →</a></p>
        """

        adapter = get_email_adapter()
        await adapter.send(EmailMessage(
            to=tenant.email,
            to_name=tenant.name,
            subject=f"Your Weekly Report — {leads_count} new leads this week",
            html_body=html,
        ))
        logger.info("Weekly report sent to %s", tenant.email)
