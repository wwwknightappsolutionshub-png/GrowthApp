"""AI Scraper ORM models.

Tables (per spec):
    ai_scraper_categories
    ai_scraper_sources
    ai_scraper_tasks
    ai_scraper_results

Plus a singleton ai_scraper_settings row that backs the "Settings" UI tab
(thread count + global aggression mode). The spec explicitly requires those
fields to be configurable; this row is the persistence layer for the
required UI, not an additional feature.
"""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.db_types import JSONBType, UUIDType


SCRAPING_TYPES = ("html", "api", "directory", "social", "custom")
SOURCE_PLATFORMS = ("directory", "search_engine", "social", "review_site", "marketplace", "other")
AGGRESSION_LEVELS = ("low", "medium", "high", "extreme")
TASK_STATUSES = ("pending", "running", "paused", "completed", "error")


class AiScraperCategory(Base):
    __tablename__ = "ai_scraper_categories"

    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(160), nullable=False, unique=True, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class AiScraperSource(Base):
    __tablename__ = "ai_scraper_sources"

    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    url_pattern: Mapped[str] = mapped_column(Text, nullable=False)
    scraping_type: Mapped[str] = mapped_column(String(20), nullable=False, default="html")
    category_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType,
        ForeignKey("ai_scraper_categories.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    source_platform: Mapped[str] = mapped_column(String(40), nullable=False, default="directory")
    postcode_prefix: Mapped[str | None] = mapped_column(String(12), nullable=True)
    region_label: Mapped[str | None] = mapped_column(String(120), nullable=True)
    is_catalog_default: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class AiScraperTask(Base):
    __tablename__ = "ai_scraper_tasks"

    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)
    source_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType,
        ForeignKey("ai_scraper_sources.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    category_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType,
        ForeignKey("ai_scraper_categories.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    aggression_level: Mapped[str] = mapped_column(String(20), nullable=False, default="low")
    frequency: Mapped[str] = mapped_column(String(120), nullable=False)
    last_run: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    next_run: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending", index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class AiScraperResult(Base):
    __tablename__ = "ai_scraper_results"

    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)
    task_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType,
        ForeignKey("ai_scraper_tasks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    raw_payload: Mapped[str | None] = mapped_column(Text, nullable=True)
    cleaned_payload: Mapped[dict] = mapped_column(JSONBType, nullable=False, default=dict)
    ai_extracted_data: Mapped[dict] = mapped_column(JSONBType, nullable=False, default=dict)
    ai_score: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    new_leads_created: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class AiScraperSettings(Base):
    """Singleton row backing the Settings UI tab (thread count + global mode).

    Only the row where `id = 1` is ever read or written. This is required to
    persist the two spec-mandated configurable values that have no obvious
    home on the four primary tables.
    """

    __tablename__ = "ai_scraper_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    thread_count: Mapped[int] = mapped_column(Integer, nullable=False, default=2)
    global_aggression_mode: Mapped[str] = mapped_column(String(20), nullable=False, default="low")
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
