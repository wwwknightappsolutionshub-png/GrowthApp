"""Tasks — kanban-style operational task manager.

Tasks are top-level work items that can be assigned to staff and optionally
linked to a deal / customer / lead. They power the Operations & Fulfilment
module of CustomerFlow AI and are surfaced as both a list view and a kanban
board.
"""
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.core.db_types import JSONBType, UUIDType


# Kanban statuses. Kept loose (String) so tenants can extend without a schema
# change, but the canonical four are: todo / doing / blocked / done.
TASK_STATUSES = ("todo", "doing", "blocked", "done", "cancelled")
TASK_PRIORITIES = ("low", "normal", "high", "urgent")
# Anything a task may be linked to. None means standalone.
TASK_LINK_TYPES = ("deal", "customer", "lead", "quote", "invoice", "booking")


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True
    )

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)

    status: Mapped[str] = mapped_column(String(20), nullable=False, default="todo", index=True)
    priority: Mapped[str] = mapped_column(String(20), nullable=False, default="normal")

    # Kanban-column ordering. Re-sequenced on drag/drop.
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Free-form labels (e.g. "callout", "warranty", "urgent-repair").
    labels: Mapped[list] = mapped_column(JSONBType, nullable=False, default=list)

    # Optional link to another CustomerFlow record. We store the type + id
    # rather than a hard FK so tasks can attach to any module without coupling.
    related_type: Mapped[str | None] = mapped_column(String(20), index=True)
    related_id: Mapped[uuid.UUID | None] = mapped_column(UUIDType, index=True)

    assigned_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUIDType, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    created_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUIDType, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    # When to fire a reminder notification. NULL = no reminder.
    reminder_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    # Set once the reminder worker has fired so we don't double-send.
    reminded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
