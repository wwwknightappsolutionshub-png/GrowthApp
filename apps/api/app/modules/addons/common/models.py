"""Industry add-on shared models."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.db_types import JSONBType, UUIDType


class TenantIndustryProfile(Base):
    """Per-tenant vertical selection and industry-specific settings."""

    __tablename__ = "tenant_industry_profile"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("tenants.id", ondelete="CASCADE"), primary_key=True
    )
    vertical: Mapped[str] = mapped_column(String(30), nullable=False, default="salon")
    settings: Mapped[dict] = mapped_column(JSONBType, default=dict)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
