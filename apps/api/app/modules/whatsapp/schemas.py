"""Pydantic schemas for the WhatsApp CRM surface."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class WhatsAppMessageItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    direction: Literal["inbound", "outbound"]
    body: str
    from_address: str | None = None
    to_address: str | None = None
    status: str
    created_at: datetime


class WhatsAppConversationSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    customer_id: uuid.UUID | None = None
    customer_phone: str | None = None
    last_message_at: datetime | None = None
    is_resolved: bool
    unread_count: int = 0
    last_preview: str | None = None
    last_direction: str | None = None
    customer_name: str | None = None


class WhatsAppConversationDetail(WhatsAppConversationSummary):
    messages: list[WhatsAppMessageItem]


class WhatsAppSendRequest(BaseModel):
    to: str = Field(min_length=4, max_length=32)
    body: str = Field(min_length=1, max_length=4096)
    customer_id: uuid.UUID | None = None
    deal_id: uuid.UUID | None = None
    template: str | None = Field(default=None, max_length=64)


class WhatsAppAIRequest(BaseModel):
    conversation_id: uuid.UUID


class WhatsAppSuggestedReply(BaseModel):
    suggestion: str
    tone: str = "professional"
    requires_review: bool = True


class WhatsAppSentiment(BaseModel):
    label: Literal["positive", "neutral", "negative", "urgent"]
    score: float = Field(ge=-1.0, le=1.0)
    reason: str | None = None


class WhatsAppSummary(BaseModel):
    summary: str
    bullets: list[str] = Field(default_factory=list)
    next_action: str | None = None
