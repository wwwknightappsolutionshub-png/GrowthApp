"""Validate inbound social webhook payloads."""
from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

SOCIAL_EVENT_TYPES = frozenset({
    "message",
    "comment",
    "lead",
    "mention",
    "post_status",
})

SOCIAL_PLATFORMS = frozenset({"facebook", "instagram", "linkedin", "tiktok"})


class SocialWebhookPayload(BaseModel):
    event_type: Literal["message", "comment", "lead", "mention", "post_status"]
    platform: Literal["facebook", "instagram", "linkedin", "tiktok"]
    sender_name: str | None = None
    sender_id: str | None = None
    sender_email: str | None = None
    sender_phone: str | None = None
    message: str | None = None
    content: str | None = None
    external_id: str | None = None
    post_id: str | None = None
    status: str | None = None
    tags: list[str] = Field(default_factory=list)
    raw: dict[str, Any] = Field(default_factory=dict)

    @field_validator("event_type", mode="before")
    @classmethod
    def normalize_event(cls, v: str) -> str:
        return (v or "message").lower().replace("-", "_")

    @field_validator("platform", mode="before")
    @classmethod
    def normalize_platform(cls, v: str) -> str:
        return (v or "").lower()

    def body_text(self) -> str:
        return (self.message or self.content or "").strip()
