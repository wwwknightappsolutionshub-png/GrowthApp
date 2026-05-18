from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class ProgramCreateBody(BaseModel):
    type: Literal["tradesman", "global_saas"]
    reward_amount: float = 0
    reward_type: str
    reward_delivery_method: str
    rules: dict[str, Any] = Field(default_factory=dict)


class ProgramResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    type: str
    owner_id: uuid.UUID | None
    reward_amount: float
    reward_type: str
    reward_delivery_method: str
    rules: dict
    status: str
    created_at: datetime


class ApproveBody(BaseModel):
    reward_amount: float | None = None
    reason: str | None = None


class RejectBody(BaseModel):
    reason: str | None = None


class LinkGenerateBody(BaseModel):
    program_id: uuid.UUID


class LinkResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    program_id: uuid.UUID
    ref_code: str
    ref_link: str
    qr_code_url: str
    created_at: datetime


class EventLogBody(BaseModel):
    ref_code: str
    referrer_user_id: uuid.UUID | None = None


class EventUpdateStatusBody(BaseModel):
    event_id: uuid.UUID
    status: str


class EventRewardBody(BaseModel):
    event_id: uuid.UUID


class PayoutRequestBody(BaseModel):
    event_id: uuid.UUID
    amount: float
    payout_method: str


class PayoutResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    event_id: uuid.UUID
    referrer_user_id: uuid.UUID
    amount: float
    payout_method: str
    payout_status: str
    created_at: datetime


class ReferrerDashboardResponse(BaseModel):
    clicks: int
    signups: int
    paid_users: int
    commission_earned: float
    events: list[dict]


class EventLogResponse(BaseModel):
    id: uuid.UUID
    status: str
