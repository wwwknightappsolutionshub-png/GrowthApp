"""ORM models for tenant integrations."""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.db_types import JSONBType, UUIDType


class TenantGoogleConnection(Base):
    """OAuth connection to Google Business Profile for one tenant."""

    __tablename__ = "tenant_google_connections"

    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, unique=True, index=True
    )
    google_account_name: Mapped[str] = mapped_column(String(255), nullable=False)
    google_location_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    location_title: Mapped[str | None] = mapped_column(String(500), nullable=True)
    access_token_encrypted: Mapped[str] = mapped_column(Text, nullable=False)
    refresh_token_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)
    token_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    connection_metadata: Mapped[dict] = mapped_column(JSONBType, nullable=False, default=dict)
    connected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    last_sync_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class GoogleBusinessReview(Base):
    """Cached Google review pulled via Business Profile API."""

    __tablename__ = "google_business_reviews"
    __table_args__ = (
        UniqueConstraint("tenant_id", "google_review_name", name="uq_google_review_tenant_name"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True
    )
    google_review_name: Mapped[str] = mapped_column(String(512), nullable=False)
    reviewer_display_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    star_rating: Mapped[str | None] = mapped_column(String(20), nullable=True)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    reply_comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    review_created_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    reply_updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    raw_data: Mapped[dict] = mapped_column(JSONBType, nullable=False, default=dict)
    synced_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
