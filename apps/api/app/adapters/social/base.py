from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class SocialPostPayload:
    message: str
    image_urls: list[str] = field(default_factory=list)
    scheduled_at: datetime | None = None


@dataclass
class SocialPostResult:
    platform_post_id: str
    url: str | None = None


class SocialAdapter(ABC):
    @abstractmethod
    async def publish_post(self, account_id: str, payload: SocialPostPayload) -> SocialPostResult: ...

    @abstractmethod
    async def schedule_post(self, account_id: str, payload: SocialPostPayload) -> SocialPostResult: ...
