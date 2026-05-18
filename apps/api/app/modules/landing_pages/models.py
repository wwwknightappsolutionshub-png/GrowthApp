"""Landing pages persistence.

A `LandingPage` is a tenant-owned page composed of typed sections (hero, features,
testimonials, FAQ, CTA, …). Pages are published per `slug` and served either via
the public API for SSR / ISR consumers or rendered directly from JSON by the
frontend.

Sections are stored as a JSON list of `{type, props}` so we can render any new
section type without a schema change.
"""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.db_types import JSONBType, UUIDType


class LandingPage(Base):
    __tablename__ = "landing_pages"
    __table_args__ = (UniqueConstraint("tenant_id", "slug", name="uq_landing_pages_tenant_slug"),)

    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True
    )
    slug: Mapped[str] = mapped_column(String(120), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    meta_description: Mapped[str | None] = mapped_column(String(400))
    # Optional hero image URL; sections may also embed their own images.
    cover_image_url: Mapped[str | None] = mapped_column(Text)
    # Theme tokens applied at render time (primary colour, font, etc.).
    theme: Mapped[dict] = mapped_column(JSONBType, nullable=False, default=dict)
    # Ordered list of sections: [{ "type": "hero", "props": {...} }, ...].
    sections: Mapped[list] = mapped_column(JSONBType, nullable=False, default=list)
    is_published: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    # Convenience metadata stored for analytics & SEO audits.
    extra: Mapped[dict] = mapped_column(JSONBType, nullable=False, default=dict)
    ai_provider: Mapped[str | None] = mapped_column(String(20))
    ai_model: Mapped[str | None] = mapped_column(String(100))
    ai_prompt: Mapped[str | None] = mapped_column(Text)
    created_by_user_id: Mapped[uuid.UUID | None] = mapped_column(UUIDType, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
