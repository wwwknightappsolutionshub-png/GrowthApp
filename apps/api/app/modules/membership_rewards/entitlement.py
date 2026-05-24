from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Annotated

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import CurrentTenantContext
from app.core.exceptions import ForbiddenException, NotFoundException
from app.modules.accounting.models import TenantAddon
from app.modules.membership_rewards.constants import FEATURE_MEMBERSHIP_REWARDS


async def tenant_has_membership_rewards(db: AsyncSession, tenant_id: uuid.UUID) -> bool:
    now = datetime.now(timezone.utc)
    row = (
        await db.execute(
            select(TenantAddon).where(
                TenantAddon.tenant_id == tenant_id,
                TenantAddon.feature_code == FEATURE_MEMBERSHIP_REWARDS,
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


async def require_public_membership_rewards(db: AsyncSession, tenant_id: uuid.UUID) -> None:
    """Block public MR surfaces when trial expired or add-on inactive."""
    if not await tenant_has_membership_rewards(db, tenant_id):
        raise NotFoundException("Membership page is not available")


async def require_membership_rewards(
    ctx: CurrentTenantContext,
    db: AsyncSession = Depends(get_db),
) -> None:
    _, tenant, _ = ctx
    if not await tenant_has_membership_rewards(db, tenant.id):
        raise ForbiddenException(
            "Membership & Rewards add-on required. Start your trial or upgrade to unlock this feature."
        )


MembershipRewardsRequired = Annotated[None, Depends(require_membership_rewards)]
