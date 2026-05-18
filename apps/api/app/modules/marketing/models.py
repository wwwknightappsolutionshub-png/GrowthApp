"""SQLAlchemy models for the marketing CMS + visitor review pipeline.

There are no tenant relationships here — these rows are platform-wide content.

Tables
------
- `marketing_sections` — keyed JSONB blobs (one row per page section like
  `hero`, `stats`, `pillars`, `pricing`, `faqs`, …).
- `adaptive_landing_pages` — editable niche-specific personalization payloads
  for the first-visit adaptive homepage demo.
- `marketing_reviews`  — visitor-submitted testimonials with a moderation
  workflow and per-channel publish state (GMB, Trustpilot).
"""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.db_types import JSONBType, UUIDType


class MarketingSection(Base):
    """A single editable section of the public marketing site.

    The `key` is the stable identifier the frontend looks up (e.g. `"hero"`,
    `"stats"`, `"pricing"`). The `data` JSON is the section payload — its shape
    is documented per-key in `seed.py`.
    """

    __tablename__ = "marketing_sections"

    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)
    key: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    title: Mapped[str | None] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text)
    data: Mapped[dict] = mapped_column(JSONBType, nullable=False, default=dict)
    is_published: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    updated_by_user_id: Mapped[uuid.UUID | None] = mapped_column(UUIDType, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class AdaptiveLandingPage(Base):
    """Super-admin editable content for the personalized homepage demo.

    `niche_id` matches the static frontend fallback config, while `data` stores
    the full editable payload used by the adaptive renderer.
    """

    __tablename__ = "adaptive_landing_pages"

    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)
    niche_id: Mapped[str] = mapped_column(String(80), unique=True, nullable=False, index=True)
    label: Mapped[str] = mapped_column(String(180), nullable=False)
    data: Mapped[dict] = mapped_column(JSONBType, nullable=False, default=dict)
    is_published: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    updated_by_user_id: Mapped[uuid.UUID | None] = mapped_column(UUIDType, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class MarketingReview(Base):
    """A visitor-submitted testimonial.

    Lifecycle:
        submitted → auto-displayed on the marketing site (status='approved' by
        default after sanitisation) → super-admin can demote (`hidden`),
        feature (`featured`), or push to external review surfaces
        (GMB / Trustpilot via dedicated push actions).
    """

    __tablename__ = "marketing_reviews"

    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)

    # Author identity
    author_name: Mapped[str] = mapped_column(String(120), nullable=False)
    author_role: Mapped[str | None] = mapped_column(String(180))
    author_location: Mapped[str | None] = mapped_column(String(120))
    author_email: Mapped[str | None] = mapped_column(String(255))
    author_company: Mapped[str | None] = mapped_column(String(180))

    # Review body
    rating: Mapped[int] = mapped_column(Integer, nullable=False, default=5)
    quote: Mapped[str] = mapped_column(Text, nullable=False)
    quote_raw: Mapped[str] = mapped_column(Text, nullable=False)  # before sanitisation
    metric: Mapped[str | None] = mapped_column(String(180))  # e.g. "68% quote acceptance"

    # State
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="approved", index=True)
    # one of: "approved" | "pending" | "hidden" | "rejected"
    is_featured: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_carousel: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    sanitised: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # External publishing state (GMB / Trustpilot)
    gmb_status: Mapped[str] = mapped_column(String(20), nullable=False, default="not_pushed")
    # "not_pushed" | "queued" | "pushed" | "failed"
    gmb_pushed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    gmb_url: Mapped[str | None] = mapped_column(String(500))
    trustpilot_status: Mapped[str] = mapped_column(String(20), nullable=False, default="not_pushed")
    trustpilot_pushed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    trustpilot_url: Mapped[str | None] = mapped_column(String(500))

    # Capture metadata
    capture_source: Mapped[str] = mapped_column(String(40), nullable=False, default="exit_intent")
    # "exit_intent" | "share_button" | "footer_form" | "manual"
    referrer_url: Mapped[str | None] = mapped_column(String(500))
    user_agent: Mapped[str | None] = mapped_column(String(500))
    ip_address: Mapped[str | None] = mapped_column(String(45))

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class LandingPageTemplate(Base):
    """A pre-built, niche-specific landing page template.

    These are platform-level "starter packs" that a tenant can clone into their
    own `landing_pages` row and customise. The actual content lives in `sections`
    as a list of `{type, props}` blocks compatible with `SectionRenderer`.
    """

    __tablename__ = "landing_page_templates"

    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)
    slug: Mapped[str] = mapped_column(String(80), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(180), nullable=False)
    niche: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    # "trades" | "hospitality" | "beauty" | "healthcare" | "real_estate" | "generic"
    description: Mapped[str | None] = mapped_column(Text)
    preview_image_url: Mapped[str | None] = mapped_column(String(500))
    theme: Mapped[dict] = mapped_column(JSONBType, nullable=False, default=dict)
    sections: Mapped[list] = mapped_column(JSONBType, nullable=False, default=list)
    is_published: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
