import logging
import uuid
from datetime import datetime, timezone

from sqlalchemy import select

from app.adapters.sms.base import SMSMessage
from app.core.database import get_db_context
from app.modules.reputation.models import ReviewRequest, Review
from app.modules.crm.models import Deal, Customer
from app.modules.tenants.models import Tenant

logger = logging.getLogger(__name__)


async def send_review_request(ctx: dict, *, deal_id: str, tenant_id: str) -> None:
    """Triggered 2 hours after a deal is marked Completed."""
    async with get_db_context() as db:
        try:
            deal_uuid = uuid.UUID(deal_id)
            tenant_uuid = uuid.UUID(tenant_id)

            # Fetch deal + customer + tenant
            deal_result = await db.execute(select(Deal).where(Deal.id == deal_uuid))
            deal = deal_result.scalar_one_or_none()
            if not deal:
                logger.warning("send_review_request: deal %s not found", deal_id)
                return

            customer_result = await db.execute(select(Customer).where(Customer.id == deal.customer_id))
            customer = customer_result.scalar_one_or_none()

            tenant_result = await db.execute(select(Tenant).where(Tenant.id == tenant_uuid))
            tenant = tenant_result.scalar_one_or_none()
            if not tenant:
                return

            # Create ReviewRequest record
            rr = ReviewRequest(
                id=uuid.uuid4(),
                tenant_id=tenant_uuid,
                deal_id=deal_uuid,
                customer_id=customer.id if customer else None,
            )
            db.add(rr)
            await db.flush()

            import os
            frontend_url = os.getenv("FRONTEND_URL", "https://app.yourdomain.com")
            review_url = f"{frontend_url}/{tenant.slug}/review/{rr.token}"

            # Send SMS if phone available
            if customer and customer.phone:
                from app.adapters.sms import get_sms_adapter
                body = (
                    f"Hi {customer.first_name}, thank you for choosing {tenant.name}! "
                    f"Could you spare 30 seconds to rate your experience? {review_url}"
                )
                await get_sms_adapter().send(SMSMessage(to=customer.phone, body=body))
                rr.status = "sent"
                rr.sent_at = datetime.now(timezone.utc)

            # Send email if email available
            if customer and customer.email:
                from app.adapters.email import get_email_adapter
                from app.adapters.email.base import EmailMessage
                from app.templates.renderer import render_review_request

                html = render_review_request(
                    customer_name=f"{customer.first_name} {customer.last_name or ''}".strip(),
                    business_name=tenant.name,
                    review_url=review_url,
                    service_description=deal.service_type,
                )
                email_adapter = get_email_adapter()
                await email_adapter.send(EmailMessage(
                    to=customer.email,
                    to_name=f"{customer.first_name} {customer.last_name or ''}".strip(),
                    subject=f"How did we do? — {tenant.name} would love your feedback",
                    html_body=html,
                ))
                rr.status = "sent"
                rr.sent_at = datetime.now(timezone.utc)

            db.add(rr)
            await db.commit()
            logger.info("Review request sent deal=%s tenant=%s token=%s", deal_id, tenant_id, rr.token)

        except Exception as exc:
            logger.error("send_review_request failed deal=%s error=%s", deal_id, exc, exc_info=True)
            await db.rollback()
            raise
