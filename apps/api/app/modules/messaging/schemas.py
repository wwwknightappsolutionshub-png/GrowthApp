from datetime import datetime
from uuid import UUID
from pydantic import BaseModel


class SendMessageRequest(BaseModel):
    deal_id: UUID | None = None
    customer_id: UUID | None = None
    channel: str
    to_address: str
    subject: str | None = None
    body: str


class MessageResponse(BaseModel):
    model_config = {"from_attributes": True}
    id: UUID
    direction: str
    channel: str
    from_address: str | None
    to_address: str | None
    subject: str | None
    body: str
    status: str
    created_at: datetime


class ConversationResponse(BaseModel):
    model_config = {"from_attributes": True}
    id: UUID
    tenant_id: UUID
    customer_id: UUID | None
    deal_id: UUID | None
    channel: str
    customer_phone: str | None
    customer_email: str | None
    last_message_at: datetime | None
    is_resolved: bool
    created_at: datetime
    messages: list[MessageResponse] = []
