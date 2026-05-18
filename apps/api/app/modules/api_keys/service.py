"""API key issuance and verification.

Key format: ``cf_<env>_<prefix><random>`` where:

  * ``cf_`` is a CustomerFlow brand prefix (makes leaked keys easy to scan for)
  * ``<env>`` is "live" or "test"
  * ``<prefix>`` is the first 8 chars of the random secret, also stored in the
    DB so the UI can render "cf_live_a1B2C3D4..." without revealing the full key
  * The remaining 40+ chars are the secret.

Only the SHA-256 of the full key is persisted. Verification recomputes the hash
and looks up by hash (constant-time DB lookup).
"""
from __future__ import annotations

import hashlib
import secrets
import string
import uuid
from datetime import datetime, timezone

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import log_action
from app.core.exceptions import NotFoundException, UnauthorizedException, ValidationException
from app.modules.auth.models import ApiKey
from app.modules.rbac.models import PERMISSION_CATALOGUE

_ALPHABET = string.ascii_letters + string.digits


def _random_string(length: int) -> str:
    return "".join(secrets.choice(_ALPHABET) for _ in range(length))


def _hash_key(raw: str) -> str:
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


# ── Issue ────────────────────────────────────────────────────────────────────

async def create_api_key(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID | None,
    name: str,
    scopes: list[str],
    expires_at: datetime | None = None,
    is_live: bool = True,
) -> tuple[ApiKey, str]:
    """Create an API key and return (row, raw_key). The raw key is shown ONCE."""
    if not name or not name.strip():
        raise ValidationException("API key name is required")

    invalid = [s for s in scopes if s not in PERMISSION_CATALOGUE]
    if invalid:
        raise ValidationException(f"Unknown scope(s): {sorted(invalid)}")

    prefix = _random_string(8)
    secret = _random_string(48)
    env = "live" if is_live else "test"
    raw = f"cf_{env}_{prefix}{secret}"

    row = ApiKey(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        user_id=user_id,
        name=name.strip(),
        prefix=prefix,
        key_hash=_hash_key(raw),
        scopes=list(scopes),
        expires_at=expires_at,
    )
    db.add(row)
    await log_action(
        db,
        action="api_key.created",
        resource="api_key",
        resource_id=row.id,
        tenant_id=tenant_id,
        user_id=user_id,
        metadata={"name": row.name, "scopes": list(scopes), "env": env},
    )
    await db.commit()
    await db.refresh(row)
    return row, raw


# ── List / revoke ────────────────────────────────────────────────────────────

async def list_api_keys(db: AsyncSession, tenant_id: uuid.UUID) -> list[ApiKey]:
    rows = (
        await db.execute(
            select(ApiKey)
            .where(ApiKey.tenant_id == tenant_id)
            .order_by(ApiKey.created_at.desc())
        )
    ).scalars().all()
    return list(rows)


async def revoke_api_key(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    key_id: uuid.UUID,
    *,
    user_id: uuid.UUID | None = None,
) -> ApiKey:
    row = (
        await db.execute(
            select(ApiKey).where(ApiKey.id == key_id, ApiKey.tenant_id == tenant_id)
        )
    ).scalar_one_or_none()
    if not row:
        raise NotFoundException("API key")
    if not row.revoked_at:
        row.revoked_at = datetime.now(timezone.utc)
        db.add(row)
        await log_action(
            db,
            action="api_key.revoked",
            resource="api_key",
            resource_id=row.id,
            tenant_id=tenant_id,
            user_id=user_id,
            metadata={"name": row.name},
        )
        await db.commit()
        await db.refresh(row)
    return row


# ── Verify (called by FastAPI dep) ───────────────────────────────────────────

async def resolve_api_key(db: AsyncSession, raw_key: str) -> ApiKey:
    """Return the ApiKey row for `raw_key` or raise 401.

    Also bumps last_used_at as a side-effect (fire-and-forget).
    """
    if not raw_key or not raw_key.startswith("cf_"):
        raise UnauthorizedException("Invalid API key")
    key_hash = _hash_key(raw_key)
    row = (
        await db.execute(select(ApiKey).where(ApiKey.key_hash == key_hash))
    ).scalar_one_or_none()
    if not row:
        raise UnauthorizedException("Invalid API key")
    if row.revoked_at:
        raise UnauthorizedException("API key has been revoked")
    if row.expires_at and row.expires_at <= datetime.now(timezone.utc):
        raise UnauthorizedException("API key has expired")

    # Best-effort last-used timestamp; ignore commit errors (RLS, conflict).
    try:
        await db.execute(
            update(ApiKey).where(ApiKey.id == row.id).values(last_used_at=datetime.now(timezone.utc))
        )
        await db.commit()
    except Exception:
        await db.rollback()
    return row
