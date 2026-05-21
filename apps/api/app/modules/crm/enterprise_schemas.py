"""Pydantic schemas for CRM enterprise APIs."""
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


# ── Pipelines & stages ────────────────────────────────────────────────────────

class StageCreate(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    position: int = 0
    color: str | None = None
    applies_to: str = "both"
    automation_event: str | None = None
    is_won: bool = False
    is_lost: bool = False


class StageUpdate(BaseModel):
    name: str | None = None
    position: int | None = None
    color: str | None = None
    applies_to: str | None = None
    automation_event: str | None = None
    is_won: bool | None = None
    is_lost: bool | None = None


class StageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    tenant_id: UUID
    pipeline_id: UUID
    name: str
    position: int
    color: str | None
    applies_to: str
    automation_event: str | None
    is_won: bool
    is_lost: bool
    created_at: datetime


class PipelineCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    description: str | None = None
    is_default: bool = False


class PipelineUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    is_default: bool | None = None
    is_active: bool | None = None


class PipelineResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    tenant_id: UUID
    name: str
    description: str | None
    is_default: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime
    stages: list[StageResponse] = []


class StageReorderItem(BaseModel):
    stage_id: UUID
    position: int


# ── Unified board ─────────────────────────────────────────────────────────────

class BoardCardLead(BaseModel):
    card_type: str = "lead"
    id: UUID
    title: str
    stage_id: UUID | None
    stage_order: int
    email: str | None
    phone: str | None
    source: str | None
    score: int | None
    score_label: str | None
    assigned_user_id: UUID | None
    created_at: datetime


class BoardCardDeal(BaseModel):
    card_type: str = "deal"
    id: UUID
    title: str
    stage_id: UUID | None
    stage_order: int
    stage: str
    customer_name: str | None
    value_pence: int
    assigned_user_id: UUID | None
    created_at: datetime


class BoardColumn(BaseModel):
    stage: StageResponse
    leads: list[BoardCardLead] = []
    deals: list[BoardCardDeal] = []


class BoardResponse(BaseModel):
    pipeline: PipelineResponse
    columns: list[BoardColumn]
    total_leads: int
    total_deals: int
    total_value_pence: int


class BoardMoveRequest(BaseModel):
    card_type: str = Field(pattern="^(lead|deal)$")
    card_id: UUID
    stage_id: UUID
    stage_order: int = 0


class MoveDealRequestV2(BaseModel):
    stage_id: UUID | None = None
    stage: str | None = None
    stage_order: int = 0


# ── Activities ────────────────────────────────────────────────────────────────

class ActivityCreate(BaseModel):
    entity_type: str
    entity_id: UUID
    activity_type: str
    title: str | None = None
    body: str | None = None
    metadata: dict = Field(default_factory=dict)


class ActivityResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    tenant_id: UUID
    entity_type: str
    entity_id: UUID
    activity_type: str
    title: str | None
    body: str | None
    user_id: UUID | None
    metadata: dict = Field(default_factory=dict, validation_alias="extra_metadata")
    created_at: datetime


# ── Tags ──────────────────────────────────────────────────────────────────────

class TagCreate(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    color: str | None = None


class TagResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    name: str
    color: str | None
    created_at: datetime


class TagAssignRequest(BaseModel):
    entity_type: str
    entity_id: UUID
    tag_ids: list[UUID]


# ── Custom fields ─────────────────────────────────────────────────────────────

class CustomFieldDefCreate(BaseModel):
    entity_type: str
    field_key: str
    label: str
    field_type: str = "text"
    options: dict = Field(default_factory=dict)
    is_required: bool = False
    position: int = 0


class CustomFieldDefResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    entity_type: str
    field_key: str
    label: str
    field_type: str
    options: dict
    is_required: bool
    position: int


class CustomFieldValueSet(BaseModel):
    definition_id: UUID
    entity_type: str
    entity_id: UUID
    value_text: str | None = None
    value_number: float | None = None
    value_bool: bool | None = None
    value_date: datetime | None = None
    value_json: dict | None = None


# ── Saved filters ─────────────────────────────────────────────────────────────

class SavedFilterCreate(BaseModel):
    name: str
    entity_type: str
    rules: dict = Field(default_factory=dict)
    is_default: bool = False


class SavedFilterResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    name: str
    entity_type: str
    rules: dict
    is_default: bool
    user_id: UUID | None
    created_at: datetime


# ── Score rules ───────────────────────────────────────────────────────────────

class ScoreRuleCreate(BaseModel):
    name: str
    priority: int = 100
    conditions: dict = Field(default_factory=dict)
    points: int = 0
    is_active: bool = True


class ScoreRuleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    name: str
    priority: int
    conditions: dict
    points: int
    is_active: bool
    created_at: datetime


# ── Bulk & merge ──────────────────────────────────────────────────────────────

class BulkUpdateRequest(BaseModel):
    entity_type: str
    ids: list[UUID]
    updates: dict = Field(default_factory=dict)


class MergeRequest(BaseModel):
    entity_type: str
    primary_id: UUID
    duplicate_id: UUID


class DuplicateCandidateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    entity_type: str
    primary_id: UUID
    duplicate_id: UUID
    match_score: float
    status: str
    created_at: datetime


# ── Dashboard ─────────────────────────────────────────────────────────────────

class DashboardResponse(BaseModel):
    new_leads_today: int
    deals_won_this_month: int
    total_pipeline_value_pence: int
    leads_by_source: dict[str, int]
    leads_by_stage: dict[str, int]
    deals_by_stage: dict[str, int]


# ── Attachments ───────────────────────────────────────────────────────────────

class AttachmentCreate(BaseModel):
    entity_type: str
    entity_id: UUID
    file_name: str
    mime_type: str | None = None
    size_bytes: int = 0
    storage_path: str


class AttachmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    entity_type: str
    entity_id: UUID
    file_name: str
    mime_type: str | None
    size_bytes: int
    storage_path: str
    created_at: datetime


# ── Assignments ───────────────────────────────────────────────────────────────

class AssignmentCreate(BaseModel):
    entity_type: str
    entity_id: UUID
    user_id: UUID
    role: str = "collaborator"
