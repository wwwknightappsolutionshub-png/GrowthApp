from datetime import datetime
from uuid import UUID
from pydantic import BaseModel


class MessageTemplateCreate(BaseModel):
    name: str
    channel: str
    subject: str | None = None
    body: str


class MessageTemplateResponse(BaseModel):
    model_config = {"from_attributes": True}
    id: UUID
    tenant_id: UUID
    name: str
    channel: str
    subject: str | None
    body: str
    created_at: datetime


class AutomationStepIn(BaseModel):
    step_order: int
    action_type: str
    delay_minutes: int = 0
    config: dict = {}


class AutomationStepResponse(AutomationStepIn):
    model_config = {"from_attributes": True}
    id: UUID


class AutomationCreate(BaseModel):
    name: str
    trigger_event: str
    trigger_conditions: dict = {}
    is_active: bool = True
    steps: list[AutomationStepIn] = []


class AutomationUpdate(BaseModel):
    name: str | None = None
    is_active: bool | None = None
    trigger_conditions: dict | None = None


class AutomationResponse(BaseModel):
    model_config = {"from_attributes": True}
    id: UUID
    tenant_id: UUID
    name: str
    trigger_event: str
    trigger_conditions: dict
    is_active: bool
    created_at: datetime
    steps: list[AutomationStepResponse] = []
