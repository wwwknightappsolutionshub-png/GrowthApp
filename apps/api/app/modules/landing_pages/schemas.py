"""Landing-page schemas + the canonical section catalogue."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

SectionType = Literal[
    "hero",
    "features",
    "testimonials",
    "trust_badges",
    "faq",
    "gallery",
    "cta",
    "pricing",
    "lead_form",
    "rich_text",
]


class Section(BaseModel):
    type: SectionType
    props: dict[str, Any] = Field(default_factory=dict)


class LandingPageCreate(BaseModel):
    slug: str = Field(min_length=1, max_length=120, pattern=r"^[a-z0-9][a-z0-9\-]*$")
    title: str = Field(min_length=1, max_length=255)
    meta_description: str | None = Field(default=None, max_length=400)
    cover_image_url: str | None = None
    theme: dict[str, Any] = Field(default_factory=dict)
    sections: list[Section] = Field(default_factory=list)


class LandingPageUpdate(BaseModel):
    title: str | None = Field(default=None, max_length=255)
    meta_description: str | None = Field(default=None, max_length=400)
    cover_image_url: str | None = None
    theme: dict[str, Any] | None = None
    sections: list[Section] | None = None
    is_published: bool | None = None


class LandingPageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    tenant_id: UUID
    slug: str
    title: str
    meta_description: str | None
    cover_image_url: str | None
    theme: dict
    sections: list
    is_published: bool
    published_at: datetime | None
    ai_provider: str | None
    ai_model: str | None
    created_at: datetime
    updated_at: datetime


class GenerateRequest(BaseModel):
    business_summary: str = Field(min_length=10, max_length=2000)
    primary_offer: str = Field(min_length=3, max_length=500)
    target_audience: str = Field(default="", max_length=300)
    tone: str = Field(default="confident, friendly, professional", max_length=80)
    cta_text: str = Field(default="Get a free quote", max_length=60)
    include_sections: list[SectionType] = Field(
        default_factory=lambda: ["hero", "features", "testimonials", "faq", "cta", "lead_form"]
    )
    slug: str | None = Field(default=None, max_length=120, pattern=r"^[a-z0-9][a-z0-9\-]*$")
    save: bool = Field(default=True)


class GenerateResponse(BaseModel):
    page_id: UUID | None
    slug: str
    title: str
    meta_description: str
    sections: list[Section]
    provider: str
    model: str
