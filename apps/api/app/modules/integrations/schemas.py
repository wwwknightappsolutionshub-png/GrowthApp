from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class GoogleConnectionStatus(BaseModel):
    connected: bool
    configured: bool
    location_title: str | None = None
    google_location_name: str | None = None
    google_account_name: str | None = None
    last_sync_at: str | None = None
    available_locations: list[dict] = Field(default_factory=list)


class GoogleLocationPick(BaseModel):
    location_name: str = Field(min_length=3, max_length=255)


class GoogleReviewResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    google_review_name: str
    reviewer_display_name: str | None
    star_rating: str | None
    comment: str | None
    reply_comment: str | None
    review_created_at: datetime | None
    reply_updated_at: datetime | None
    synced_at: datetime


class GoogleReviewReplyRequest(BaseModel):
    comment: str = Field(min_length=1, max_length=4000)


class GoogleSyncResponse(BaseModel):
    synced: int
    total_fetched: int


class TenantGoogleCredentialsStatus(BaseModel):
    registered: bool
    status: str | None = None
    redirect_uri: str
    google_client_id: str | None = None
    connected_at: str | None = None
    expires_at: str | None = None


class TenantGoogleCredentialsRegister(BaseModel):
    google_client_id: str = Field(min_length=10, max_length=512)
    google_client_secret: str = Field(min_length=10, max_length=512)


class GoogleAuthUrlResponse(BaseModel):
    url: str


class GoogleGenericSyncResponse(BaseModel):
    ok: bool = True
    detail: dict = Field(default_factory=dict)


class SocialChannelResponse(BaseModel):
    id: str
    channel_type: str
    webhook_url: str
    api_key: str
    zapier_integration_key: str | None = None
    make_integration_key: str | None = None
    status: str
    connected_at: str | None = None


class SocialPostRequest(BaseModel):
    platform: str = Field(min_length=3, max_length=30)
    content: str = Field(min_length=1, max_length=8000)
    media_url: str | None = None


class IntegrationsOnboardingState(BaseModel):
    google_connected: bool = False
    social_connected: bool = False
    skipped: bool = False


class IntegrationsOnboardingUpdate(BaseModel):
    google_connected: bool | None = None
    social_connected: bool | None = None
    skipped: bool | None = None
