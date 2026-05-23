"""Tenant-gated access for industry add-ons (uses tenant_addons table)."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Annotated, Callable

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import CurrentTenantContext
from app.core.exceptions import ForbiddenException
from app.modules.accounting.models import TenantAddon
from app.modules.addons.common.constants import INDUSTRY_FEATURE_CODES

UPGRADE_MESSAGES: dict[str, str] = {
    "industry_booking": (
        "Industry Booking add-on required. Upgrade to unlock enhanced scheduling for your vertical."
    ),
    "industry_billing": (
        "Industry Billing add-on required. Upgrade to unlock specialized invoicing for your vertical."
    ),
    "industry_crm": (
        "Industry CRM add-on required. Upgrade to unlock smart customer and job history for your vertical."
    ),
}


async def tenant_has_addon(
    db: AsyncSession, tenant_id: uuid.UUID, feature_code: str
) -> bool:
    if feature_code not in INDUSTRY_FEATURE_CODES:
        return False
    now = datetime.now(timezone.utc)
    row = (
        await db.execute(
            select(TenantAddon).where(
                TenantAddon.tenant_id == tenant_id,
                TenantAddon.feature_code == feature_code,
                TenantAddon.status == "active",
            )
        )
    ).scalar_one_or_none()
    if not row:
        return False
    if row.expires_at and row.expires_at < now:
        return False
    return True


def require_addon(feature_code: str) -> Callable:
    async def _check(
        ctx: CurrentTenantContext,
        db: AsyncSession = Depends(get_db),
    ) -> None:
        _, tenant, _ = ctx
        if not await tenant_has_addon(db, tenant.id, feature_code):
            msg = UPGRADE_MESSAGES.get(
                feature_code,
                f"Add-on '{feature_code}' required. Visit Dashboard → Industry Add-ons to upgrade.",
            )
            raise ForbiddenException(msg)

    return _check


def addon_dependency(feature_code: str) -> Annotated[None, Depends(require_addon(feature_code))]:
    return Annotated[None, Depends(require_addon(feature_code))]
