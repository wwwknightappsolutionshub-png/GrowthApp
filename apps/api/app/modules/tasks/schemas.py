from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.modules.tasks.models import TASK_LINK_TYPES, TASK_PRIORITIES, TASK_STATUSES

TaskStatus = Literal[TASK_STATUSES]  # type: ignore[valid-type]
TaskPriority = Literal[TASK_PRIORITIES]  # type: ignore[valid-type]
TaskLinkType = Literal[TASK_LINK_TYPES]  # type: ignore[valid-type]


class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = None
    status: TaskStatus = "todo"
    priority: TaskPriority = "normal"
    labels: list[str] = Field(default_factory=list)
    related_type: TaskLinkType | None = None
    related_id: UUID | None = None
    assigned_user_id: UUID | None = None
    due_at: datetime | None = None
    reminder_at: datetime | None = None


class TaskUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    status: TaskStatus | None = None
    priority: TaskPriority | None = None
    labels: list[str] | None = None
    related_type: TaskLinkType | None = None
    related_id: UUID | None = None
    assigned_user_id: UUID | None = None
    due_at: datetime | None = None
    reminder_at: datetime | None = None


class TaskMove(BaseModel):
    """Drag-and-drop reorder/move payload."""

    status: TaskStatus
    position: int = Field(ge=0)


class TaskResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    title: str
    description: str | None
    status: str
    priority: str
    position: int
    labels: list[str]
    related_type: str | None
    related_id: UUID | None
    assigned_user_id: UUID | None
    created_by_user_id: UUID | None
    due_at: datetime | None
    reminder_at: datetime | None
    reminded_at: datetime | None
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime


class TaskListResponse(BaseModel):
    items: list[TaskResponse]
    total: int
    page: int
    page_size: int


class TaskBoardColumn(BaseModel):
    status: str
    label: str
    items: list[TaskResponse]


class TaskBoardResponse(BaseModel):
    columns: list[TaskBoardColumn]
