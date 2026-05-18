import logging
import uuid
from app.adapters.social.base import SocialAdapter, SocialPostPayload, SocialPostResult

logger = logging.getLogger(__name__)


class MockSocialAdapter(SocialAdapter):
    async def publish_post(self, account_id: str, payload: SocialPostPayload) -> SocialPostResult:
        pid = f"mock_post_{uuid.uuid4().hex[:8]}"
        logger.info("[MOCK SOCIAL] Published post to account %s: %s", account_id, payload.message[:60])
        return SocialPostResult(platform_post_id=pid, url=f"https://facebook.com/mock/{pid}")

    async def schedule_post(self, account_id: str, payload: SocialPostPayload) -> SocialPostResult:
        pid = f"mock_scheduled_{uuid.uuid4().hex[:8]}"
        logger.info("[MOCK SOCIAL] Scheduled post to account %s for %s", account_id, payload.scheduled_at)
        return SocialPostResult(platform_post_id=pid)
