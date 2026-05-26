from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.core.db_types import JSONBType, UUIDType

if TYPE_CHECKING:
    from app.modules.tenants.models import TenantMember


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(50))
    avatar_url: Mapped[str | None] = mapped_column(Text)
    email_verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    is_superadmin: Mapped[bool] = mapped_column(Boolean, default=False)
    user_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        server_default="tenant",
        default="tenant",
    )
    estimated_client_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    phone_verified_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    onboarding_completed: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        server_default="0",
        nullable=False,
    )
    membership_rewards_opt_in: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        server_default="1",
        nullable=False,
    )

    # ── 2FA / TOTP ────────────────────────────────────────────────────────
    totp_secret: Mapped[str | None] = mapped_column(String(64), nullable=True)
    totp_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    # List of argon2-hashed backup codes (each used once, then removed)
    totp_backup_codes: Mapped[list] = mapped_column(JSONBType, default=list, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    tenant_memberships: Mapped[list[TenantMember]] = relationship(
        "TenantMember",
        back_populates="user",
    )


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUIDType, nullable=False, index=True)
    token_hash: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class MagicLinkToken(Base):
    """Single-use passwordless sign-in token.

    Issued via POST /auth/magic-link; redeemed via GET /auth/magic-link/verify.
    The raw token is emailed to the user; only the hash is persisted.
    """

    __tablename__ = "magic_link_tokens"

    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    token_hash: Mapped[str] = mapped_column(String(128), nullable=False, unique=True, index=True)
    # Optional: bind the token to a tenant when the user is already a member,
    # so multi-tenant users land in the right workspace.
    tenant_id: Mapped[uuid.UUID | None] = mapped_column(UUIDType, nullable=True)
    # Optional: redirect path after sign-in.
    next_path: Mapped[str | None] = mapped_column(String(500))
    issued_to_ip: Mapped[str | None] = mapped_column(String(45))
    issued_user_agent: Mapped[str | None] = mapped_column(Text)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    used_from_ip: Mapped[str | None] = mapped_column(String(45))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class ApiKey(Base):
    """Programmatic access key.

    Created at /settings/api-keys. The full key is shown ONCE on creation; only
    a SHA-256 prefix+hash is persisted. Scopes are stored as a JSON array of
    permission strings (e.g. ["leads:read", "tasks:write"]).
    """

    __tablename__ = "api_keys"

    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUIDType, nullable=False, index=True)
    user_id: Mapped[uuid.UUID | None] = mapped_column(UUIDType, nullable=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    # First 8 chars of the random secret, kept in plaintext for UI display
    # ("cf_live_abc12345..."). The full secret is hashed.
    prefix: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    key_hash: Mapped[str] = mapped_column(String(128), nullable=False, unique=True, index=True)
    scopes: Mapped[list] = mapped_column(JSONBType, nullable=False, default=list)
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
