"""Auto-reply approval queue.

When an inbound message arrives, the AI auto-reply worker drafts a response
and persists it here with status='pending'. A staff member then approves +
sends it, edits it, or rejects it. Approved replies are sent through the
appropriate channel adapter.
"""
import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.db_types import UUIDType


class AutoReply(Base):
    __tablename__ = "auto_replies"

    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True
    )
    conversation_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    inbound_message_id: Mapped[uuid.UUID | None] = mapped_column(UUIDType, nullable=True)
    channel: Mapped[str] = mapped_column(String(20), nullable=False)  # sms|email|whatsapp
    draft: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")  # pending|approved|rejected|sent
    rule: Mapped[str | None] = mapped_column(String(100))
    reviewed_by_user_id: Mapped[uuid.UUID | None] = mapped_column(UUIDType, nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    provider: Mapped[str | None] = mapped_column(String(20))
    model: Mapped[str | None] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )
