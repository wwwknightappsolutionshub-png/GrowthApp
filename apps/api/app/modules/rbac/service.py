"""RBAC permission resolution + management."""
from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import log_action
from app.modules.auth.models import User
from app.modules.rbac.models import (
    DEFAULT_TEMPLATES,
    PERMISSION_CATALOGUE,
    PermissionTemplate,
    TenantPermissionOverride,
)


# ── Resolution ───────────────────────────────────────────────────────────────

async def get_permissions_for_role(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    role: str,
) -> set[str]:
    """Resolve the effective permission set for `role` in `tenant_id`."""
    # 1. Template (falls back to hard-coded defaults if not seeded yet).
    template_row = (
        await db.execute(select(PermissionTemplate).where(PermissionTemplate.role == role))
    ).scalar_one_or_none()
    base: set[str] = set(template_row.permissions if template_row else DEFAULT_TEMPLATES.get(role, []))

    # 2. Tenant overrides on top.
    overrides = (
        await db.execute(
            select(TenantPermissionOverride).where(
                TenantPermissionOverride.tenant_id == tenant_id,
                TenantPermissionOverride.role == role,
            )
        )
    ).scalars().all()
    for ov in overrides:
        if ov.effect == "grant":
            base.add(ov.permission)
        elif ov.effect == "revoke":
            base.discard(ov.permission)
    return base


async def can(
    db: AsyncSession,
    user: User,
    tenant_id: uuid.UUID,
    role: str,
    permission: str,
) -> bool:
    """True if the user has `permission` in the given tenant."""
    # Super-admins bypass tenant RBAC.
    if user.is_superadmin:
        return True
    perms = await get_permissions_for_role(db, tenant_id, role)
    return permission in perms


# ── Management ───────────────────────────────────────────────────────────────

async def seed_default_templates(db: AsyncSession) -> int:
    """Insert any missing default permission templates. Returns rows created."""
    created = 0
    for role, perms in DEFAULT_TEMPLATES.items():
        existing = (
            await db.execute(select(PermissionTemplate).where(PermissionTemplate.role == role))
        ).scalar_one_or_none()
        if existing:
            continue
        db.add(
            PermissionTemplate(
                id=uuid.uuid4(),
                role=role,
                permissions=list(perms),
                description=f"Default permission template for {role}",
                is_system=True,
            )
        )
        created += 1
    if created:
        await db.commit()
    return created


async def set_template_permissions(
    db: AsyncSession,
    role: str,
    permissions: list[str],
    *,
    actor_user_id: uuid.UUID | None = None,
) -> PermissionTemplate:
    invalid = [p for p in permissions if p not in PERMISSION_CATALOGUE]
    if invalid:
        from app.core.exceptions import ValidationException

        raise ValidationException(f"Unknown permissions: {sorted(invalid)}")

    template = (
        await db.execute(select(PermissionTemplate).where(PermissionTemplate.role == role))
    ).scalar_one_or_none()
    if template is None:
        template = PermissionTemplate(
            id=uuid.uuid4(),
            role=role,
            permissions=list(permissions),
            description=None,
            is_system=False,
        )
        db.add(template)
        action = "rbac.template_created"
    else:
        template.permissions = list(permissions)
        db.add(template)
        action = "rbac.template_updated"
    await log_action(
        db,
        action=action,
        resource="permission_template",
        resource_id=template.id,
        user_id=actor_user_id,
        metadata={"role": role, "permissions": list(permissions)},
    )
    await db.commit()
    await db.refresh(template)
    return template


async def set_tenant_override(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    *,
    role: str,
    permission: str,
    effect: str,
    actor_user_id: uuid.UUID | None = None,
) -> TenantPermissionOverride:
    if effect not in ("grant", "revoke"):
        from app.core.exceptions import ValidationException

        raise ValidationException("effect must be 'grant' or 'revoke'")
    if permission not in PERMISSION_CATALOGUE:
        from app.core.exceptions import ValidationException

        raise ValidationException(f"Unknown permission '{permission}'")
    existing = (
        await db.execute(
            select(TenantPermissionOverride).where(
                TenantPermissionOverride.tenant_id == tenant_id,
                TenantPermissionOverride.role == role,
                TenantPermissionOverride.permission == permission,
                TenantPermissionOverride.effect == effect,
            )
        )
    ).scalar_one_or_none()
    if existing:
        return existing
    row = TenantPermissionOverride(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        role=role,
        permission=permission,
        effect=effect,
    )
    db.add(row)
    await log_action(
        db,
        action="rbac.override_set",
        resource="permission_override",
        resource_id=row.id,
        tenant_id=tenant_id,
        user_id=actor_user_id,
        metadata={"role": role, "permission": permission, "effect": effect},
    )
    await db.commit()
    await db.refresh(row)
    return row


async def clear_tenant_override(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    *,
    role: str,
    permission: str,
    effect: str | None = None,
    actor_user_id: uuid.UUID | None = None,
) -> int:
    """Remove an override; returns rows deleted."""
    q = select(TenantPermissionOverride).where(
        TenantPermissionOverride.tenant_id == tenant_id,
        TenantPermissionOverride.role == role,
        TenantPermissionOverride.permission == permission,
    )
    if effect is not None:
        q = q.where(TenantPermissionOverride.effect == effect)
    rows = (await db.execute(q)).scalars().all()
    for row in rows:
        await db.delete(row)
    if rows:
        await log_action(
            db,
            action="rbac.override_cleared",
            resource="permission_override",
            tenant_id=tenant_id,
            user_id=actor_user_id,
            metadata={"role": role, "permission": permission, "effect": effect, "count": len(rows)},
        )
        await db.commit()
    return len(rows)
