"""Pydantic schemas for the outreach engine."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

Channel = Literal["sms", "email", "whatsapp"]
Kind = Literal["broadcast", "sequence", "winback"]
StepCondition = Literal["always", "no_reply", "replied", "opened"]


class CampaignStep(BaseModel):
    """A single step in an outreach sequence."""
    channel: Channel
    subject: str | None = Field(default=None, max_length=200)
    body: str = Field(min_length=1, max_length=4000)
    # Delay AFTER the previous step (or after enrolment for step 0). Hours.
    delay_hours: int = Field(default=0, ge=0, le=24 * 365)
    condition: StepCondition = Field(default="always")
    label: str | None = Field(default=None, max_length=80)


class AudienceConfig(BaseModel):
    """Either select an existing segment, or build an inline filter."""
    segment_id: UUID | None = None
    filter: dict[str, Any] | None = None


class CampaignCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=1000)
    kind: Kind = "sequence"
    channels: list[Channel] = Field(default_factory=list)
    audience: AudienceConfig
    steps: list[CampaignStep] = Field(default_factory=list)
    scheduled_at: datetime | None = None


class CampaignUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=255)
    description: str | None = None
    channels: list[Channel] | None = None
    audience: AudienceConfig | None = None
    steps: list[CampaignStep] | None = None
    scheduled_at: datetime | None = None


class CampaignResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    tenant_id: UUID
    name: str
    description: str | None
    kind: str
    channels: list[str]
    audience: dict
    steps: list[dict]
    status: str
    scheduled_at: datetime | None
    started_at: datetime | None
    completed_at: datetime | None
    paused_at: datetime | None
    enrolled_count: int
    sent_count: int
    replied_count: int
    unsubscribed_count: int
    created_at: datetime
    updated_at: datetime


class CampaignStats(BaseModel):
    campaign_id: UUID
    enrolled: int
    active: int
    sent: int
    replied: int
    unsubscribed: int
    completed: int
    reply_rate_pct: float
    unsub_rate_pct: float


class AIStepDraftRequest(BaseModel):
    channel: Channel
    goal: str = Field(min_length=1, max_length=300)
    audience_hint: str | None = Field(default=None, max_length=300)
    tone: str = Field(default="friendly and helpful", max_length=80)


class AIStepDraftResponse(BaseModel):
    subject: str | None
    body: str
    provider: str
    model: str


class WinbackPresetRequest(BaseModel):
    inactive_days: int = Field(default=90, ge=14, le=730)
    channel: Channel = "email"
    offer: str = Field(min_length=1, max_length=300)
    name: str | None = Field(default=None, max_length=200)
