"""RBAC management endpoints.

* `GET  /rbac/catalogue` — list all permission strings (for UI rendering)
* `GET  /rbac/templates` — list role -> permissions (super-admin)
* `PUT  /rbac/templates/{role}` — replace permissions for a role (super-admin)
* `GET  /rbac/me` — resolved permissions for the calling user in their tenant
* `GET  /rbac/overrides` — list tenant-specific overrides (owner)
* `POST /rbac/overrides` — grant or revoke a permission for a role (owner)
* `DELETE /rbac/overrides/{id}` — clear an override (owner)
"""
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import (
    CurrentTenantContext,
    OwnerContext,
    SuperAdmin,
    require_owner,
)
from app.modules.rbac import service
from app.modules.rbac.models import (
    DEFAULT_TEMPLATES,
    PERMISSION_CATALOGUE,
    PermissionTemplate,
    TenantPermissionOverride,
)

router = APIRouter(prefix="/rbac", tags=["RBAC"])


# ── Schemas (kept inline since they're admin-only) ──────────────────────────

class CatalogueResponse(BaseModel):
    permissions: list[str]


class TemplateResponse(BaseModel):
    role: str
    permissions: list[str]
    description: str | None = None
    is_system: bool


class UpdateTemplateRequest(BaseModel):
    permissions: list[str] = Field(default_factory=list)


class OverrideCreateRequest(BaseModel):
    role: str
    permission: str
    effect: str  # 'grant' | 'revoke'


class OverrideResponse(BaseModel):
    id: UUID
    role: str
    permission: str
    effect: str


class MePermissionsResponse(BaseModel):
    role: str
    permissions: list[str]


# ── Public-ish ───────────────────────────────────────────────────────────────

@router.get("/catalogue", response_model=CatalogueResponse)
async def get_catalogue():
    return {"permissions": list(PERMISSION_CATALOGUE)}


@router.get("/me", response_model=MePermissionsResponse)
async def get_my_permissions(
    ctx: CurrentTenantContext,
    db: AsyncSession = Depends(get_db),
):
    user, tenant, role = ctx
    if user.is_superadmin or role == "owner":
        # Owners see every permission their tenant could grant.
        perms = sorted(PERMISSION_CATALOGUE)
    else:
        perms = sorted(await service.get_permissions_for_role(db, tenant.id, role))
    return {"role": role, "permissions": perms}


# ── Super-admin: templates ───────────────────────────────────────────────────

@router.get("/templates", response_model=list[TemplateResponse])
async def list_templates(_admin: SuperAdmin, db: AsyncSession = Depends(get_db)):
    rows = (await db.execute(select(PermissionTemplate))).scalars().all()
    by_role = {r.role: r for r in rows}
    output: list[TemplateResponse] = []
    seen = set()
    for r in rows:
        seen.add(r.role)
        output.append(TemplateResponse(
            role=r.role,
            permissions=list(r.permissions),
            description=r.description,
            is_system=r.is_system,
        ))
    # Surface defaults that haven't been persisted yet.
    for role, perms in DEFAULT_TEMPLATES.items():
        if role in seen:
            continue
        output.append(TemplateResponse(
            role=role,
            permissions=list(perms),
            description=f"Default permission template for {role}",
            is_system=True,
        ))
    output.sort(key=lambda t: t.role)
    return output


@router.put("/templates/{role}", response_model=TemplateResponse)
async def update_template(
    role: str,
    body: UpdateTemplateRequest,
    admin: SuperAdmin,
    db: AsyncSession = Depends(get_db),
):
    tpl = await service.set_template_permissions(
        db, role, body.permissions, actor_user_id=admin.id
    )
    return TemplateResponse(
        role=tpl.role,
        permissions=list(tpl.permissions),
        description=tpl.description,
        is_system=tpl.is_system,
    )


# ── Owner: tenant overrides ──────────────────────────────────────────────────

@router.get("/overrides", response_model=list[OverrideResponse])
async def list_overrides(ctx: OwnerContext, db: AsyncSession = Depends(get_db)):
    _, tenant, _ = ctx
    rows = (
        await db.execute(
            select(TenantPermissionOverride).where(TenantPermissionOverride.tenant_id == tenant.id)
        )
    ).scalars().all()
    return [
        OverrideResponse(id=r.id, role=r.role, permission=r.permission, effect=r.effect)
        for r in rows
    ]


@router.post("/overrides", response_model=OverrideResponse, status_code=201)
async def create_override(
    body: OverrideCreateRequest,
    ctx: OwnerContext,
    db: AsyncSession = Depends(get_db),
):
    user, tenant, _ = ctx
    row = await service.set_tenant_override(
        db,
        tenant.id,
        role=body.role,
        permission=body.permission,
        effect=body.effect,
        actor_user_id=user.id,
    )
    return OverrideResponse(id=row.id, role=row.role, permission=row.permission, effect=row.effect)


@router.delete("/overrides/{override_id}", status_code=204)
async def delete_override(
    override_id: UUID,
    ctx: OwnerContext,
    db: AsyncSession = Depends(get_db),
):
    from app.core.audit import log_action

    user, tenant, _ = ctx
    row = (
        await db.execute(
            select(TenantPermissionOverride).where(
                TenantPermissionOverride.id == override_id,
                TenantPermissionOverride.tenant_id == tenant.id,
            )
        )
    ).scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="Override not found")
    await log_action(
        db,
        action="rbac.override_deleted",
        resource="permission_override",
        resource_id=row.id,
        tenant_id=tenant.id,
        user_id=user.id,
        metadata={"role": row.role, "permission": row.permission, "effect": row.effect},
    )
    await db.delete(row)
    await db.commit()
