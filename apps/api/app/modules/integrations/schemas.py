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
