"""Outreach engine models.

An `OutreachCampaign` is a multi-channel sequence (1..n steps across SMS / email /
WhatsApp) sent to an audience defined either by a `CustomerSegment` or an inline
filter blob. Each customer pulled into the campaign becomes an `OutreachEnrolment`
that walks through the steps; each send is logged as an `OutreachSend` so we can
report opens / replies / conversions.

Campaign status:  draft  →  scheduled  →  running  →  paused | completed
Enrolment status: active → completed | replied | unsubscribed | failed
"""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.core.db_types import JSONBType, UUIDType


class OutreachCampaign(Base):
    __tablename__ = "outreach_campaigns"

    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    # 'broadcast'  – send once to entire audience at launch.
    # 'sequence'   – multi-step drip with delays + conditions.
    # 'winback'    – preset: customers without a deal in N days.
    kind: Mapped[str] = mapped_column(String(20), nullable=False, default="sequence")
    # Channels touched by any step. Used for capability checks and analytics.
    channels: Mapped[list] = mapped_column(JSONBType, nullable=False, default=list)
    # Audience config — either {"segment_id": "..."} OR {"filter": {...}}.
    audience: Mapped[dict] = mapped_column(JSONBType, nullable=False, default=dict)
    # Steps stored inline (channel, subject, body, delay_hours, condition, …).
    steps: Mapped[list] = mapped_column(JSONBType, nullable=False, default=list)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="draft", index=True)
    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    paused_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    # Counters denormalised for fast list views.
    enrolled_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    sent_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    replied_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    unsubscribed_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_by_user_id: Mapped[uuid.UUID | None] = mapped_column(UUIDType, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    enrolments: Mapped[list["OutreachEnrolment"]] = relationship(
        "OutreachEnrolment", back_populates="campaign", cascade="all, delete-orphan"
    )


class OutreachEnrolment(Base):
    __tablename__ = "outreach_enrolments"

    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True
    )
    campaign_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("outreach_campaigns.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    customer_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("customers.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    current_step: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active", index=True)
    next_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    last_sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    replied_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    unsubscribed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    error_message: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    campaign: Mapped["OutreachCampaign"] = relationship("OutreachCampaign", back_populates="enrolments")


class OutreachSend(Base):
    """One row per outbound message dispatched by the outreach engine."""
    __tablename__ = "outreach_sends"

    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True
    )
    campaign_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("outreach_campaigns.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    enrolment_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("outreach_enrolments.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    step_index: Mapped[int] = mapped_column(Integer, nullable=False)
    channel: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="sent")
    provider_message_id: Mapped[str | None] = mapped_column(String(255))
    subject: Mapped[str | None] = mapped_column(String(500))
    body: Mapped[str | None] = mapped_column(Text)
    error_message: Mapped[str | None] = mapped_column(Text)
    opened_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    sent_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )
