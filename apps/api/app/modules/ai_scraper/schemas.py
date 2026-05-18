"""Pydantic schemas for the AI Scraper API (super-admin only)."""
from __future__ import annotations

import re
import uuid
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.modules.ai_scraper.models import (
    AGGRESSION_LEVELS,
    SCRAPING_TYPES,
    TASK_STATUSES,
)

ScrapingType = Literal["html", "api", "directory", "social", "custom"]
AggressionLevel = Literal["low", "medium", "high", "extreme"]
TaskStatus = Literal["pending", "running", "paused", "completed", "error"]


_CRON_FIELD_RE = re.compile(r"^[\d\*\-,\/]+$")


def _validate_cron(expr: str) -> str:
    parts = expr.strip().split()
    if len(parts) not in (5, 6):
        raise ValueError("cron expression must have 5 or 6 fields")
    for p in parts:
        if not _CRON_FIELD_RE.match(p):
            raise ValueError(f"invalid cron field: {p!r}")
    return expr.strip()


# ── Categories ───────────────────────────────────────────────────────────────


class CategoryCreate(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    description: str | None = None


class CategoryUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=160)
    description: str | None = None


class CategoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    description: str | None
    created_at: datetime
    updated_at: datetime


# ── Sources ──────────────────────────────────────────────────────────────────


class SourceCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    url_pattern: str = Field(min_length=1)
    scraping_type: ScrapingType = "html"
    category_id: uuid.UUID
    active: bool = True
    notes: str | None = None

    @field_validator("scraping_type")
    @classmethod
    def _check_type(cls, v: str) -> str:
        if v not in SCRAPING_TYPES:
            raise ValueError("invalid scraping_type")
        return v


class SourceUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    url_pattern: str | None = None
    scraping_type: ScrapingType | None = None
    category_id: uuid.UUID | None = None
    active: bool | None = None
    notes: str | None = None


class SourceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    url_pattern: str
    scraping_type: str
    category_id: uuid.UUID
    active: bool
    notes: str | None
    created_at: datetime
    updated_at: datetime


# ── Tasks ────────────────────────────────────────────────────────────────────


class TaskCreate(BaseModel):
    source_id: uuid.UUID
    category_id: uuid.UUID
    aggression_level: AggressionLevel = "low"
    frequency: str
    status: TaskStatus = "pending"

    @field_validator("aggression_level")
    @classmethod
    def _check_level(cls, v: str) -> str:
        if v not in AGGRESSION_LEVELS:
            raise ValueError("invalid aggression_level")
        return v

    @field_validator("status")
    @classmethod
    def _check_status(cls, v: str) -> str:
        if v not in TASK_STATUSES:
            raise ValueError("invalid status")
        return v

    @field_validator("frequency")
    @classmethod
    def _cron(cls, v: str) -> str:
        return _validate_cron(v)


class TaskUpdate(BaseModel):
    source_id: uuid.UUID | None = None
    category_id: uuid.UUID | None = None
    aggression_level: AggressionLevel | None = None
    frequency: str | None = None
    status: TaskStatus | None = None

    @field_validator("frequency")
    @classmethod
    def _cron(cls, v: str | None) -> str | None:
        return _validate_cron(v) if v else v


class TaskResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    source_id: uuid.UUID
    category_id: uuid.UUID
    aggression_level: str
    frequency: str
    last_run: datetime | None
    next_run: datetime | None
    status: str
    created_at: datetime
    updated_at: datetime


class TaskRunResponse(BaseModel):
    task_id: uuid.UUID
    enqueued: bool
    message: str


class TaskRunnerRow(BaseModel):
    """Augmented task view for the "Task runner display"."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    source_id: uuid.UUID
    category_id: uuid.UUID
    aggression_level: str
    frequency: str
    last_run: datetime | None
    next_run: datetime | None
    status: str
    total_leads_extracted: int


# ── Results ──────────────────────────────────────────────────────────────────


class ResultResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    task_id: uuid.UUID
    raw_payload: str | None
    cleaned_payload: dict[str, Any]
    ai_extracted_data: dict[str, Any]
    ai_score: int
    new_leads_created: int
    created_at: datetime
    updated_at: datetime


# ── Settings ─────────────────────────────────────────────────────────────────


class SettingsBody(BaseModel):
    thread_count: int = Field(ge=1, le=64)
    global_aggression_mode: AggressionLevel

    @field_validator("global_aggression_mode")
    @classmethod
    def _check_level(cls, v: str) -> str:
        if v not in AGGRESSION_LEVELS:
            raise ValueError("invalid global_aggression_mode")
        return v


class SettingsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    thread_count: int
    global_aggression_mode: str
    updated_at: datetime
