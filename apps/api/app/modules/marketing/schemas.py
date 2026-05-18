"""Pydantic schemas for the marketing CMS, reviews and landing templates."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


# ── Sections ────────────────────────────────────────────────────────────────


class MarketingSectionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    key: str
    title: str | None = None
    description: str | None = None
    data: dict
    is_published: bool
    sort_order: int
    updated_at: datetime


class MarketingSectionUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    data: dict | None = None
    is_published: bool | None = None
    sort_order: int | None = None


class MarketingSectionCreate(MarketingSectionUpdate):
    key: str = Field(min_length=2, max_length=64)
    data: dict = Field(default_factory=dict)


class MarketingSectionReorderRequest(BaseModel):
    """Ordered list of section keys — `sort_order` is assigned from index (×10)."""

    keys: list[str] = Field(min_length=1)


class PublicMarketingBundle(BaseModel):
    """One blob the marketing site reads at request time."""

    sections: dict[str, dict]
    """Map of key -> data for all published sections."""

    reviews: list["PublicReviewResponse"]
    """Approved reviews for the carousel (already sanitised)."""


# ── Adaptive landing pages ──────────────────────────────────────────────────


class AdaptiveLandingPageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    niche_id: str
    label: str
    data: dict[str, Any]
    is_published: bool
    updated_at: datetime


class AdaptiveLandingPageUpsert(BaseModel):
    niche_id: str = Field(min_length=2, max_length=80)
    label: str = Field(min_length=2, max_length=180)
    data: dict[str, Any] = Field(default_factory=dict)
    is_published: bool = True


class AdaptiveLandingPageUpdate(BaseModel):
    label: str | None = Field(default=None, min_length=2, max_length=180)
    data: dict[str, Any] | None = None
    is_published: bool | None = None


# ── Reviews ─────────────────────────────────────────────────────────────────


class PublicReviewSubmit(BaseModel):
    """Body for `POST /public/marketing/reviews`."""

    author_name: str = Field(min_length=2, max_length=120)
    author_role: str | None = Field(default=None, max_length=180)
    author_location: str | None = Field(default=None, max_length=120)
    author_email: str | None = Field(default=None, max_length=255)
    author_company: str | None = Field(default=None, max_length=180)
    rating: int = Field(ge=1, le=5, default=5)
    quote: str = Field(min_length=12, max_length=1200)
    metric: str | None = Field(default=None, max_length=180)
    capture_source: Literal["exit_intent", "share_button", "footer_form", "manual"] = "exit_intent"


class PublicReviewResponse(BaseModel):
    """Shape returned to the public marketing site."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    author_name: str
    author_role: str | None = None
    author_location: str | None = None
    rating: int
    quote: str
    metric: str | None = None
    is_featured: bool
    created_at: datetime


class AdminReviewResponse(PublicReviewResponse):
    """Full review payload for the moderation queue."""

    author_email: str | None = None
    author_company: str | None = None
    quote_raw: str
    status: str
    is_carousel: bool
    sanitised: bool
    gmb_status: str
    gmb_pushed_at: datetime | None = None
    gmb_url: str | None = None
    trustpilot_status: str
    trustpilot_pushed_at: datetime | None = None
    trustpilot_url: str | None = None
    capture_source: str


class ReviewModerationAction(BaseModel):
    status: Literal["approved", "pending", "hidden", "rejected"] | None = None
    is_featured: bool | None = None
    is_carousel: bool | None = None
    quote: str | None = None
    author_role: str | None = None
    author_location: str | None = None
    metric: str | None = None


class ReviewPushRequest(BaseModel):
    """Payload for pushing a review to an external surface."""

    channel: Literal["gmb", "trustpilot"]
    target_url: str | None = None  # explicit URL override (otherwise pulled from settings)


# ── Landing-page templates ──────────────────────────────────────────────────


class LandingPageTemplateSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    slug: str
    name: str
    niche: str
    description: str | None = None
    preview_image_url: str | None = None


class LandingPageTemplateDetail(LandingPageTemplateSummary):
    theme: dict
    sections: list[dict[str, Any]]


class ApplyTemplateRequest(BaseModel):
    template_slug: str = Field(min_length=2, max_length=80)
    page_title: str = Field(min_length=2, max_length=200)
    page_slug: str | None = Field(default=None, max_length=80)


PublicMarketingBundle.model_rebuild()
