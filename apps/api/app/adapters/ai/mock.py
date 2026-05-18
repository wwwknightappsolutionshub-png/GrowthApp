import logging
from app.adapters.ai.base import AIAdapter, SocialPostRequest

logger = logging.getLogger(__name__)


class MockAIAdapter(AIAdapter):
    async def generate_social_post(self, req: SocialPostRequest) -> str:
        logger.info("[MOCK AI] Generating social post for %s on %s", req.business_name, req.platform)
        return (
            f"Just completed another great {req.service_type} job! "
            f"Our team at {req.business_name} takes pride in delivering excellent service. "
            f"Need help? Give us a call today! #LocalBusiness #UK #{req.service_type.replace(' ', '')}"
        )

    async def generate_sms(self, context: dict, template_hint: str) -> str:
        logger.info("[MOCK AI] Generating SMS for context: %s", context)
        return f"Hi {context.get('first_name', 'there')}, thanks for contacting {context.get('business_name', 'us')}. We'll be in touch shortly!"
