"""Super-admin soft-delete helpers for tenants and platform users."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import BadRequestException, NotFoundException
from app.modules.auth.models import RefreshToken, User
from app.modules.tenants.models import Tenant, TenantMember

ARCHIVED_SLUG_MARKER = "-deleted-"


def active_users_filter():
    """SQLAlchemy criterion: user has not been soft-deleted."""
    return User.deleted_at.is_(None)


def active_tenants_filter():
    """Exclude tenants archived by super-admin delete."""
    return ~Tenant.slug.contains(ARCHIVED_SLUG_MARKER)


async def _revoke_user_sessions(db: AsyncSession, user_id: uuid.UUID) -> None:
    now = datetime.now(timezone.utc)
    await db.execute(
        update(RefreshToken)
        .where(RefreshToken.user_id == user_id, RefreshToken.revoked_at.is_(None))
        .values(revoked_at=now)
    )


async def delete_tenant(db: AsyncSession, tenant_id: uuid.UUID) -> dict:
    """Archive a tenant: deactivate, free slug, revoke member sessions."""
    tenant = (
        await db.execute(select(Tenant).where(Tenant.id == tenant_id))
    ).scalar_one_or_none()
    if not tenant:
        raise NotFoundException("Tenant")

    pool_slug = (settings.MARKETPLACE_POOL_TENANT_SLUG or "lead-pool-system").strip()
    if tenant.slug == pool_slug:
        raise BadRequestException("Cannot delete the system lead pool tenant")

    tenant.is_active = False
    if "-deleted-" not in tenant.slug:
        tenant.slug = f"{tenant.slug[:80]}-deleted-{uuid.uuid4().hex[:8]}"
    db.add(tenant)

    member_rows = (
        await db.execute(
            select(TenantMember.user_id).where(TenantMember.tenant_id == tenant_id)
        )
    ).scalars().all()
    for uid in member_rows:
        await _revoke_user_sessions(db, uid)

    await db.commit()
    return {
        "id": str(tenant.id),
        "name": tenant.name,
        "slug": tenant.slug,
        "message": f"{tenant.name} has been deleted (archived). Members can no longer access this workspace.",
    }


async def delete_platform_user(db: AsyncSession, user_id: uuid.UUID) -> dict:
    """Soft-delete a tenant or freelancer account."""
    user = (
        await db.execute(
            select(User).where(User.id == user_id, User.deleted_at.is_(None))
        )
    ).scalar_one_or_none()
    if not user:
        raise NotFoundException("User")
    if user.is_superadmin:
        raise BadRequestException("Cannot delete a super-admin account")

    now = datetime.now(timezone.utc)
    user.deleted_at = now
    db.add(user)
    await _revoke_user_sessions(db, user.id)

    archived_tenants = 0
    if user.user_type == "freelancer":
        managed = (
            await db.execute(
                select(Tenant).where(Tenant.owner_user_id == user.id, Tenant.is_managed_client == True)
            )
        ).scalars().all()
        for t in managed:
            t.is_active = False
            if "-deleted-" not in t.slug:
                t.slug = f"{t.slug[:80]}-deleted-{uuid.uuid4().hex[:8]}"
            db.add(t)
            archived_tenants += 1
    elif user.user_type == "tenant":
        owned = (
            await db.execute(
                select(Tenant)
                .join(TenantMember, TenantMember.tenant_id == Tenant.id)
                .where(
                    TenantMember.user_id == user.id,
                    TenantMember.role == "owner",
                    Tenant.is_managed_client == False,
                )
            )
        ).scalars().all()
        pool_slug = (settings.MARKETPLACE_POOL_TENANT_SLUG or "lead-pool-system").strip()
        for t in owned:
            if t.slug == pool_slug:
                continue
            t.is_active = False
            if "-deleted-" not in t.slug:
                t.slug = f"{t.slug[:80]}-deleted-{uuid.uuid4().hex[:8]}"
            db.add(t)
            archived_tenants += 1

    await db.commit()
    kind = "freelancer" if user.user_type == "freelancer" else "user"
    return {
        "id": str(user.id),
        "email": user.email,
        "user_type": user.user_type,
        "archived_tenants": archived_tenants,
        "message": f"{kind.capitalize()} {user.email} deleted. They can no longer sign in.",
    }
