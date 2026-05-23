"""Grant/revoke industry add-ons (shared tenant_addons table)."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.accounting.models import TenantAddon
from app.modules.addons.common.constants import INDUSTRY_FEATURE_CODES


async def grant_addon(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    feature_code: str,
    *,
    granted_by: uuid.UUID | None = None,
    expires_at: datetime | None = None,
) -> TenantAddon:
    if feature_code not in INDUSTRY_FEATURE_CODES:
        raise ValueError(f"Unknown industry feature_code: {feature_code}")
    now = datetime.now(timezone.utc)
    row = (
        await db.execute(
            select(TenantAddon).where(
                TenantAddon.tenant_id == tenant_id,
                TenantAddon.feature_code == feature_code,
            )
        )
    ).scalar_one_or_none()
    if row:
        row.status = "active"
        row.granted_by = granted_by
        row.granted_at = now
        row.expires_at = expires_at
    else:
        row = TenantAddon(
            tenant_id=tenant_id,
            feature_code=feature_code,
            status="active",
            granted_by=granted_by,
            granted_at=now,
            expires_at=expires_at,
        )
        db.add(row)
    await db.commit()
    await db.refresh(row)
    return row


async def revoke_addon(db: AsyncSession, tenant_id: uuid.UUID, feature_code: str) -> None:
    row = (
        await db.execute(
            select(TenantAddon).where(
                TenantAddon.tenant_id == tenant_id,
                TenantAddon.feature_code == feature_code,
            )
        )
    ).scalar_one_or_none()
    if row:
        row.status = "canceled"
        await db.commit()
