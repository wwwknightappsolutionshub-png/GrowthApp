from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.db_types import JSONBType, UUIDType


class ReferralProgram(Base):
    __tablename__ = "referral_programs"

    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)
    type: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    owner_id: Mapped[uuid.UUID | None] = mapped_column(
        UUIDType, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    reward_amount: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False, default=0)
    reward_type: Mapped[str] = mapped_column(String(30), nullable=False)
    reward_delivery_method: Mapped[str] = mapped_column(String(30), nullable=False)
    rules: Mapped[dict] = mapped_column(JSONBType, nullable=False, default=dict)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="disabled", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ReferralLink(Base):
    __tablename__ = "referral_links"

    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUIDType, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    program_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("referral_programs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    ref_code: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    ref_link: Mapped[str] = mapped_column(Text, nullable=False)
    qr_code_url: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ReferralEvent(Base):
    __tablename__ = "referral_events"

    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)
    referrer_user_id: Mapped[uuid.UUID] = mapped_column(UUIDType, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    referral_program_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("referral_programs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    referred_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUIDType, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="clicked", index=True)
    reward_amount: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False, default=0)
    reward_status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ReferralPayout(Base):
    __tablename__ = "referral_payouts"

    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)
    event_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("referral_events.id", ondelete="CASCADE"), nullable=False, index=True
    )
    referrer_user_id: Mapped[uuid.UUID] = mapped_column(UUIDType, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    amount: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    payout_method: Mapped[str] = mapped_column(String(30), nullable=False)
    payout_status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
