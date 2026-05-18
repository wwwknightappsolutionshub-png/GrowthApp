"""Customer segments — saved filters with a cached size.

Rules are a simple JSON DSL:

    {
      "all": [
        {"field": "deals.total_value_pence", "op": "gte", "value": 50000},
        {"field": "deals.count", "op": "gte", "value": 1}
      ],
      "any": [],
      "none": []
    }

`compute_segment_membership` interprets these rules in SQL — see service.py.
"""
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.db_types import JSONBType, UUIDType


class CustomerSegment(Base):
    __tablename__ = "customer_segments"

    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    rules: Mapped[dict] = mapped_column(JSONBType, nullable=False, default=dict)
    size: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    computed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    is_system: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_by_user_id: Mapped[uuid.UUID | None] = mapped_column(UUIDType)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
