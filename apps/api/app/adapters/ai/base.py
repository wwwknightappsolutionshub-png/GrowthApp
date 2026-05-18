from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class SocialPostRequest:
    business_name: str
    service_type: str
    job_description: str
    tone: str = "friendly"
    platform: str = "facebook"
    image_count: int = 0


class AIAdapter(ABC):
    @abstractmethod
    async def generate_social_post(self, req: SocialPostRequest) -> str: ...

    @abstractmethod
    async def generate_sms(self, context: dict, template_hint: str) -> str: ...
