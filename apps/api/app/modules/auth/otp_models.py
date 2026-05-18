"""ORM models for signup OTP flow (pre-registration verification)."""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.db_types import JSONBType, UUIDType


class OtpCode(Base):
    """Short-lived OTP for signup verification.

    purpose: 'signup_email' | 'signup_phone'
    channel: 'email' | 'sms' | 'whatsapp'
    destination: the email address or E.164 phone number the code was sent to
    code_hash: SHA-256 of the 6-digit code (we never store plaintext)
    """

    __tablename__ = "otp_codes"

    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)
    purpose: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    destination: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    channel: Mapped[str] = mapped_column(String(20), nullable=False)
    code_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    max_attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=5, server_default="5")
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class PendingSignup(Base):
    """Form data parked while the user verifies OTPs.

    Auto-expires after 15 minutes; cleaned up on next signup initiation for the
    same email.
    """

    __tablename__ = "pending_signups"

    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    phone: Mapped[str] = mapped_column(String(50), nullable=False)
    user_type: Mapped[str] = mapped_column(String(20), nullable=False)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    payload: Mapped[dict] = mapped_column(JSONBType, default=dict, nullable=False, server_default="{}")
    phone_channel_attempted: Mapped[str | None] = mapped_column(String(20), nullable=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
