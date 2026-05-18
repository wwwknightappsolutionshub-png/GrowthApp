from openai import AsyncOpenAI
from app.adapters.ai.base import AIAdapter, SocialPostRequest
from app.core.config import settings


class OpenAIAdapter(AIAdapter):
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.OPENAI_MODEL

    async def generate_social_post(self, req: SocialPostRequest) -> str:
        prompt = (
            f"Write a {req.tone} social media post for a UK {req.service_type} business called '{req.business_name}'. "
            f"Job description: {req.job_description}. "
            f"Platform: {req.platform}. "
            f"{'Include mention of before/after photos.' if req.image_count > 0 else ''} "
            f"Keep it under 280 characters for Twitter compatibility. Include 2-3 relevant hashtags."
        )
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=200,
            temperature=0.7,
        )
        return response.choices[0].message.content.strip()

    async def generate_sms(self, context: dict, template_hint: str) -> str:
        prompt = (
            f"Write a short, friendly SMS message for a UK local service business. "
            f"Context: {context}. Tone hint: {template_hint}. "
            f"Keep under 160 characters. Be warm and professional."
        )
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=80,
            temperature=0.7,
        )
        return response.choices[0].message.content.strip()
