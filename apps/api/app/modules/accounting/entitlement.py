from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Annotated

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import CurrentTenantContext
from app.core.exceptions import ForbiddenException
from app.modules.accounting.models import FEATURE_ACCOUNTING, TenantAddon


async def tenant_has_accounting(db: AsyncSession, tenant_id: uuid.UUID) -> bool:
    now = datetime.now(timezone.utc)
    row = (
        await db.execute(
            select(TenantAddon).where(
                TenantAddon.tenant_id == tenant_id,
                TenantAddon.feature_code == FEATURE_ACCOUNTING,
                TenantAddon.status == "active",
            )
        )
    ).scalar_one_or_none()
    if not row:
        return False
    if row.expires_at and row.expires_at < now:
        return False
    return True


async def require_accounting(
    ctx: CurrentTenantContext,
    db: AsyncSession = Depends(get_db),
) -> None:
    _, tenant, _ = ctx
    if not await tenant_has_accounting(db, tenant.id):
        raise ForbiddenException(
            "Accounting add-on required. Upgrade from Accounts → Accounting to unlock this feature."
        )


AccountingRequired = Annotated[None, Depends(require_accounting)]
