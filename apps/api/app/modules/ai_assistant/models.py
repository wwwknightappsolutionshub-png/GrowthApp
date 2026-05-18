"""AI assistant: chat threads + messages.

A thread is a per-user conversation with the AI. Messages capture the full
exchange including tool calls so we can replay context exactly.
"""
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.core.db_types import JSONBType, UUIDType


class AIAssistantThread(Base):
    __tablename__ = "ai_assistant_threads"

    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False, default="New conversation")
    pinned: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    last_message_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    messages: Mapped[list["AIAssistantMessage"]] = relationship(
        "AIAssistantMessage", back_populates="thread", cascade="all, delete-orphan",
    )


class AIAssistantMessage(Base):
    __tablename__ = "ai_assistant_messages"

    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True
    )
    thread_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("ai_assistant_threads.id", ondelete="CASCADE"), nullable=False, index=True
    )
    role: Mapped[str] = mapped_column(String(20), nullable=False)  # user|assistant|tool|system
    content: Mapped[str] = mapped_column(Text, nullable=False, default="")
    tool_calls: Mapped[list] = mapped_column(JSONBType, nullable=False, default=list)
    tool_call_id: Mapped[str | None] = mapped_column(String(100))
    provider: Mapped[str | None] = mapped_column(String(20))
    model: Mapped[str | None] = mapped_column(String(100))
    input_tokens: Mapped[int | None] = mapped_column(Integer)
    output_tokens: Mapped[int | None] = mapped_column(Integer)
    cost_pence: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )

    thread: Mapped["AIAssistantThread"] = relationship("AIAssistantThread", back_populates="messages")
