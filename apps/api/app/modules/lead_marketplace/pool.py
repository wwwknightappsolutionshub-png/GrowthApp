"""System tenant that holds scraped leads before marketplace distribution."""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.modules.tenants.models import Tenant, TenantMember
from app.modules.auth.models import User
from app.core.security import hash_password

logger = logging.getLogger(__name__)

_POOL_EMAIL = "lead-pool@internal.customerflow.local"


async def get_marketplace_pool_tenant_id(db: AsyncSession) -> uuid.UUID | None:
    slug = (settings.MARKETPLACE_POOL_TENANT_SLUG or "lead-pool-system").strip()
    row = (
        await db.execute(select(Tenant.id).where(Tenant.slug == slug))
    ).scalar_one_or_none()
    if row:
        return row
    return await _create_pool_tenant(db, slug)


async def _create_pool_tenant(db: AsyncSession, slug: str) -> uuid.UUID:
    """Create internal pool tenant (idempotent by slug)."""
    existing = (
        await db.execute(select(Tenant).where(Tenant.slug == slug))
    ).scalar_one_or_none()
    if existing:
        return existing.id

    user = User(
        id=uuid.uuid4(),
        email=_POOL_EMAIL,
        password_hash=hash_password(uuid.uuid4().hex),
        full_name="Lead Pool System",
        user_type="tenant",
        is_superadmin=False,
        onboarding_completed=True,
    )
    tenant = Tenant(
        id=uuid.uuid4(),
        slug=slug,
        name="Lead Pool (System)",
        business_type="other",
        postcode="SW1A1AA",
        is_active=True,
        is_managed_client=False,
    )
    db.add(user)
    db.add(tenant)
    await db.flush()
    now = datetime.now(timezone.utc)
    db.add(
        TenantMember(
            id=uuid.uuid4(),
            tenant_id=tenant.id,
            user_id=user.id,
            role="owner",
            joined_at=now,
        )
    )
    await db.commit()
    logger.info("Created marketplace pool tenant slug=%s id=%s", slug, tenant.id)
    return tenant.id
