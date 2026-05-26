from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.accounting.models import TenantAddon
from app.modules.pwa.constants import FEATURE_PWA_WHITE_LABEL


async def tenant_has_pwa_white_label(db: AsyncSession, tenant_id: uuid.UUID) -> bool:
    now = datetime.now(timezone.utc)
    row = (
        await db.execute(
            select(TenantAddon).where(
                TenantAddon.tenant_id == tenant_id,
                TenantAddon.feature_code == FEATURE_PWA_WHITE_LABEL,
                TenantAddon.status == "active",
            )
        )
    ).scalar_one_or_none()
    if not row:
        return False
    if row.expires_at:
        exp = row.expires_at
        if exp.tzinfo is None:
            exp = exp.replace(tzinfo=timezone.utc)
        if exp < now:
            return False
    return True
