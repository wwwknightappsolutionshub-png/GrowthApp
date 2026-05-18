import httpx
from app.adapters.social.base import SocialAdapter, SocialPostPayload, SocialPostResult


class FacebookSocialAdapter(SocialAdapter):
    BASE_URL = "https://graph.facebook.com/v19.0"

    async def publish_post(self, account_id: str, payload: SocialPostPayload) -> SocialPostResult:
        # account_id should be the Facebook Page ID, access_token should be stored per account
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self.BASE_URL}/{account_id}/feed",
                json={"message": payload.message},
            )
            resp.raise_for_status()
            data = resp.json()
            return SocialPostResult(platform_post_id=data.get("id", ""))

    async def schedule_post(self, account_id: str, payload: SocialPostPayload) -> SocialPostResult:
        import time
        async with httpx.AsyncClient() as client:
            body = {
                "message": payload.message,
                "published": False,
            }
            if payload.scheduled_at:
                body["scheduled_publish_time"] = int(payload.scheduled_at.timestamp())
                body["published"] = False
            resp = await client.post(f"{self.BASE_URL}/{account_id}/feed", json=body)
            resp.raise_for_status()
            data = resp.json()
            return SocialPostResult(platform_post_id=data.get("id", ""))
