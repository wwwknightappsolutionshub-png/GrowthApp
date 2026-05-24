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


class TenantGoogleCredentials(Base):
    """Tenant-owned Google Cloud OAuth app credentials and tokens."""

    __tablename__ = "tenant_google_credentials"

    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, unique=True, index=True
    )
    google_client_id: Mapped[str] = mapped_column(String(512), nullable=False)
    google_client_secret_encrypted: Mapped[str] = mapped_column(Text, nullable=False)
    access_token_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)
    refresh_token_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)
    scopes: Mapped[str | None] = mapped_column(Text, nullable=True)
    redirect_uri: Mapped[str] = mapped_column(String(1024), nullable=False)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    connected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending", server_default="pending")


class TenantSocialChannel(Base):
    """Zapier/Make webhook channel for a social platform."""

    __tablename__ = "tenant_social_channels"
    __table_args__ = (
        UniqueConstraint("tenant_id", "channel_type", name="uq_tenant_social_channel_type"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True
    )
    channel_type: Mapped[str] = mapped_column(String(30), nullable=False)
    webhook_url: Mapped[str] = mapped_column(String(1024), nullable=False)
    api_key: Mapped[str] = mapped_column(String(64), nullable=False)
    api_secret_encrypted: Mapped[str] = mapped_column(Text, nullable=False)
    zapier_integration_key: Mapped[str | None] = mapped_column(String(128), nullable=True)
    make_integration_key: Mapped[str | None] = mapped_column(String(128), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending", server_default="pending")
    connected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class TenantSocialWebhookLog(Base):
    """Audit log for inbound social webhooks."""

    __tablename__ = "tenant_social_webhook_logs"

    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True
    )
    channel_type: Mapped[str] = mapped_column(String(30), nullable=False)
    incoming_payload: Mapped[dict] = mapped_column(JSONBType, nullable=False, default=dict)
    processed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="received", server_default="received")


class TenantGoogleSyncLog(Base):
    """Audit log for Google Business Profile sync operations."""

    __tablename__ = "tenant_google_sync_logs"

    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True
    )
    data_type: Mapped[str] = mapped_column(String(30), nullable=False)
    payload: Mapped[dict] = mapped_column(JSONBType, nullable=False, default=dict)
    synced_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="success", server_default="success")
