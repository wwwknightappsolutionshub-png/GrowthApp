"""PWA engagement email log."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.db_types import UUIDType


class PwaEngagementEmail(Base):
    __tablename__ = "pwa_engagement_emails"
    __table_args__ = (
        UniqueConstraint("tenant_id", "user_id", "kind", name="uq_pwa_engagement_once"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUIDType, nullable=False, index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(UUIDType, nullable=False, index=True)
    kind: Mapped[str] = mapped_column(String(40), nullable=False)
    sent_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
