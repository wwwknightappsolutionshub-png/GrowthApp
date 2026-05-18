from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field


class CustomerCreate(BaseModel):
    first_name: str
    last_name: str | None = None
    email: str | None = None
    phone: str | None = None
    address: str | None = None
    postcode: str | None = None
    notes: str | None = None
    source: str | None = None
    first_visit_date: datetime | None = None
    next_visit_date: datetime | None = None
    requires_followup: bool = False
    followup_reminder_at: datetime | None = None
    special_comments: str | None = None


class CustomerUpdate(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    email: str | None = None
    phone: str | None = None
    address: str | None = None
    postcode: str | None = None
    notes: str | None = None
    first_visit_date: datetime | None = None
    next_visit_date: datetime | None = None
    requires_followup: bool | None = None
    followup_reminder_at: datetime | None = None
    special_comments: str | None = None


class CustomerResponse(BaseModel):
    model_config = {"from_attributes": True}
    id: UUID
    tenant_id: UUID
    first_name: str
    last_name: str | None
    email: str | None
    phone: str | None
    address: str | None
    postcode: str | None
    notes: str | None
    source: str | None
    first_visit_date: datetime | None = None
    next_visit_date: datetime | None = None
    requires_followup: bool = False
    followup_reminder_at: datetime | None = None
    special_comments: str | None = None
    created_at: datetime


class DealCreate(BaseModel):
    customer_id: UUID
    title: str
    stage: str = "New"
    service_type: str | None = None
    description: str | None = None
    value_pence: int = 0
    location_id: UUID | None = None
    assigned_user_id: UUID | None = None


class DealUpdate(BaseModel):
    title: str | None = None
    stage: str | None = None
    stage_order: int | None = None
    service_type: str | None = None
    description: str | None = None
    value_pence: int | None = None
    lost_reason: str | None = None
    assigned_user_id: UUID | None = None


class DealActivityResponse(BaseModel):
    model_config = {"from_attributes": True}
    id: UUID
    type: str
    body: str | None
    metadata: dict = Field(default_factory=dict, validation_alias="extra_metadata")
    user_id: UUID | None
    created_at: datetime


class DealResponse(BaseModel):
    model_config = {"from_attributes": True}
    id: UUID
    tenant_id: UUID
    customer_id: UUID
    title: str
    stage: str
    stage_order: int
    service_type: str | None
    description: str | None
    value_pence: int
    source: str | None
    lost_reason: str | None
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime
    customer: CustomerResponse | None = None
    activities: list[DealActivityResponse] = []


class PipelineResponse(BaseModel):
    columns: dict[str, list[DealResponse]]
    total_deals: int
    total_value_pence: int


class MoveDealRequest(BaseModel):
    stage: str
    stage_order: int = 0
