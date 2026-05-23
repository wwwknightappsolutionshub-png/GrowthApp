"""Resolve tenant industry vertical from profile or business_type."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.addons.common.constants import BUSINESS_TYPE_VERTICAL_MAP, Vertical
from app.modules.addons.common.models import TenantIndustryProfile
from app.modules.tenants.models import Tenant


async def get_tenant_vertical(db: AsyncSession, tenant: Tenant) -> Vertical:
    row = (
        await db.execute(
            select(TenantIndustryProfile).where(TenantIndustryProfile.tenant_id == tenant.id)
        )
    ).scalar_one_or_none()
    if row and row.vertical:
        try:
            return Vertical(row.vertical)
        except ValueError:
            pass
    key = (tenant.business_type or "").strip().lower()
    if key in BUSINESS_TYPE_VERTICAL_MAP:
        return BUSINESS_TYPE_VERTICAL_MAP[key]
    for fragment, vertical in BUSINESS_TYPE_VERTICAL_MAP.items():
        if fragment in key:
            return vertical
    return Vertical.SALON


async def set_tenant_vertical(
    db: AsyncSession, tenant_id: uuid.UUID, vertical: Vertical
) -> TenantIndustryProfile:
    row = (
        await db.execute(
            select(TenantIndustryProfile).where(TenantIndustryProfile.tenant_id == tenant_id)
        )
    ).scalar_one_or_none()
    if row:
        row.vertical = vertical.value
        return row
    profile = TenantIndustryProfile(tenant_id=tenant_id, vertical=vertical.value, settings={})
    db.add(profile)
    return profile
