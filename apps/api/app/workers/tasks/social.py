import logging
from app.core.database import get_db_context

logger = logging.getLogger(__name__)


async def generate_social_post(ctx: dict, *, deal_id: str, tenant_id: str, platform: str = "facebook"):
    """Generate a social post draft using AI after job completion."""
    logger.info("Generating social post for deal=%s tenant=%s platform=%s", deal_id, tenant_id, platform)
    async with get_db_context() as db:
        from sqlalchemy import select
        from app.modules.crm.models import Deal
        from app.modules.social.models import SocialPost
        from app.modules.tenants.models import Tenant
        import uuid

        deal_result = await db.execute(select(Deal).where(Deal.id == uuid.UUID(deal_id)))
        deal = deal_result.scalar_one_or_none()
        if not deal:
            return

        tenant_result = await db.execute(select(Tenant).where(Tenant.id == uuid.UUID(tenant_id)))
        tenant = tenant_result.scalar_one_or_none()
        if not tenant:
            return

        from app.adapters import get_ai_adapter
        from app.adapters.ai.base import SocialPostRequest
        ai = get_ai_adapter()
        content = await ai.generate_social_post(SocialPostRequest(
            business_name=tenant.name,
            service_type=deal.service_type or "service",
            job_description=deal.title,
            platform=platform,
        ))

        post = SocialPost(
            id=uuid.uuid4(),
            tenant_id=uuid.UUID(tenant_id),
            deal_id=deal.id,
            platform=platform,
            content=content,
            status="pending_approval",
        )
        db.add(post)
        await db.commit()
        logger.info("Social post draft created: %s", post.id)


async def publish_social_post(ctx: dict, *, post_id: str, tenant_id: str):
    """Publish an approved social post."""
    logger.info("Publishing social post %s", post_id)
    async with get_db_context() as db:
        from sqlalchemy import select
        from app.modules.social.models import SocialPost, SocialAccount
        import uuid
        from datetime import datetime, timezone

        post_result = await db.execute(select(SocialPost).where(SocialPost.id == uuid.UUID(post_id)))
        post = post_result.scalar_one_or_none()
        if not post or post.status not in ("scheduled", "pending_approval"):
            return

        account_result = await db.execute(
            select(SocialAccount).where(
                SocialAccount.tenant_id == uuid.UUID(tenant_id),
                SocialAccount.platform == post.platform,
                SocialAccount.is_active == True,
            ).limit(1)
        )
        account = account_result.scalar_one_or_none()
        if not account:
            logger.warning("No active social account for tenant %s platform %s", tenant_id, post.platform)
            post.status = "failed"
            post.error = "No connected social account"
            db.add(post)
            await db.commit()
            return

        from app.adapters import get_social_adapter
        from app.adapters.social.base import SocialPostPayload
        adapter = get_social_adapter()
        result = await adapter.publish_post(
            account_id=account.page_id or account.account_id,
            payload=SocialPostPayload(message=post.content, image_urls=post.image_urls or []),
        )

        post.status = "published"
        post.published_at = datetime.now(timezone.utc)
        post.platform_post_id = result.platform_post_id
        db.add(post)
        await db.commit()
