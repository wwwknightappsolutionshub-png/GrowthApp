from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class NotificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    user_id: UUID | None
    kind: str
    title: str
    body: str | None
    link: str | None
    extra: dict
    read_at: datetime | None
    archived_at: datetime | None
    created_at: datetime


class NotificationListResponse(BaseModel):
    items: list[NotificationResponse]
    unread: int
    total: int
    page: int
    page_size: int


class NotificationCreateInternal(BaseModel):
    """Used by other modules (not exposed via REST)."""

    user_id: UUID | None = None
    kind: str
    title: str
    body: str | None = None
    link: str | None = None
    extra: dict = {}


class PushSubscriptionIn(BaseModel):
    endpoint: str
    keys: dict[str, str]
    user_agent: str | None = None


class PushSubscriptionResponse(BaseModel):
    id: UUID
    endpoint: str
    is_active: bool


class NotificationPreferenceResponse(BaseModel):
    kind: str
    label: str
    in_app_enabled: bool = True
    push_enabled: bool = False


class NotificationPreferenceUpdate(BaseModel):
    kind: str
    in_app_enabled: bool = True
    push_enabled: bool = False


class NotificationPreferencesUpdate(BaseModel):
    preferences: list[NotificationPreferenceUpdate] = Field(default_factory=list)
