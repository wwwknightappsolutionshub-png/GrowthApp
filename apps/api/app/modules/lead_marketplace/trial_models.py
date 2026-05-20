"""ORM for trial lead auto-delivery tracking."""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.db_types import UUIDType


class TrialLeadDelivery(Base):
    """Records a marketplace lead delivered to a new tenant during their 7-day trial."""

    __tablename__ = "trial_lead_deliveries"

    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True
    )
    marketplace_item_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("lead_marketplace.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    pool_lead_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("leads.id", ondelete="CASCADE"), nullable=False
    )
    tenant_lead_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("leads.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    delivered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
