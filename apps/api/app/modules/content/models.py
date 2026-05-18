"""SQLAlchemy ORM models for CMS content: FAQ items, Blog posts, Static pages."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

from app.core.database import Base


def _now() -> datetime:
    return datetime.now(timezone.utc)


class FaqItem(Base):
    __tablename__ = "faq_items"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    sort_order = Column(Integer, default=0, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=_now, onupdate=_now, nullable=False)


class BlogPost(Base):
    __tablename__ = "blog_posts"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(300), nullable=False)
    slug = Column(String(300), unique=True, nullable=False, index=True)
    excerpt = Column(Text)
    content = Column(Text)
    category = Column(String(100), default="Guide")
    image_url = Column(Text)
    seo_title = Column(String(300))
    seo_description = Column(Text)
    author_name = Column(String(100), default="CustomerFlow Team")
    read_minutes = Column(Integer, default=5)
    is_published = Column(Boolean, default=False, nullable=False)
    published_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), default=_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=_now, onupdate=_now, nullable=False)


class StaticPage(Base):
    """Editable static pages: about, privacy, terms, gdpr-dpa, cookies, partners, contact."""

    __tablename__ = "static_pages"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    slug = Column(String(100), unique=True, nullable=False, index=True)
    title = Column(String(300), nullable=False)
    content = Column(Text)          # Rich text / HTML stored as HTML string
    meta_title = Column(String(300))
    meta_description = Column(Text)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=_now, onupdate=_now, nullable=False)
