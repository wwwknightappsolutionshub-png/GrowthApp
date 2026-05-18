import uuid
import secrets
from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, String, Text, Boolean, Integer, func
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base
from app.core.db_types import UUIDType, JSONBType


class ReviewRequest(Base):
    __tablename__ = "review_requests"
    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUIDType, ForeignKey("tenants.id"), nullable=False)
    deal_id: Mapped[uuid.UUID | None] = mapped_column(UUIDType, ForeignKey("deals.id"), nullable=True)
    customer_id: Mapped[uuid.UUID | None] = mapped_column(UUIDType, ForeignKey("customers.id"), nullable=True)
    token: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, default=lambda: secrets.token_urlsafe(32), index=True)
    status: Mapped[str] = mapped_column(String(30), default="pending")
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    opened_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    responded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Review(Base):
    __tablename__ = "reviews"
    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUIDType, ForeignKey("tenants.id"), nullable=False, index=True)
    review_request_id: Mapped[uuid.UUID | None] = mapped_column(UUIDType, ForeignKey("review_requests.id"), nullable=True)
    customer_id: Mapped[uuid.UUID | None] = mapped_column(UUIDType, ForeignKey("customers.id"), nullable=True)
    rating: Mapped[int] = mapped_column(Integer, nullable=False)
    feedback: Mapped[str | None] = mapped_column(Text)
    is_public: Mapped[bool] = mapped_column(Boolean, default=False)
    routed_to_google: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
