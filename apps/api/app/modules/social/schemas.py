from datetime import datetime
from uuid import UUID
from pydantic import BaseModel


class SocialPostUpdate(BaseModel):
    content: str | None = None
    status: str | None = None
    scheduled_at: datetime | None = None


class SocialPostResponse(BaseModel):
    model_config = {"from_attributes": True}
    id: UUID
    tenant_id: UUID
    deal_id: UUID | None
    platform: str
    content: str
    image_urls: list
    status: str
    scheduled_at: datetime | None
    published_at: datetime | None
    platform_post_id: str | None
    error: str | None
    created_at: datetime


class SocialAccountResponse(BaseModel):
    model_config = {"from_attributes": True}
    id: UUID
    platform: str
    account_id: str
    page_id: str | None
    is_active: bool
    created_at: datetime
