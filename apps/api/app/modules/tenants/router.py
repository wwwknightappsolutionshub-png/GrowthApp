from uuid import UUID
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import CurrentTenantContext, OwnerContext
from app.modules.tenants import service
from app.modules.tenants.schemas import (
    TenantResponse, TenantUpdate,
    LocationCreate, LocationUpdate, LocationResponse,
    MemberResponse, InviteMemberRequest,
)
from app.modules.auth.schemas import MessageResponse
from app.modules.admin.tool_config import (
    get_config_for_category,
    classifyBusiness_py,
)

router = APIRouter(prefix="/tenants", tags=["Tenants"])


@router.get("/me", response_model=TenantResponse)
async def get_tenant(ctx: CurrentTenantContext):
    _, tenant, _ = ctx
    return tenant


@router.patch("/me", response_model=TenantResponse)
async def update_tenant(
    data: TenantUpdate,
    ctx: OwnerContext,
    db: AsyncSession = Depends(get_db),
):
    user, tenant, _ = ctx
    return await service.update_tenant(db, tenant, data, actor_user_id=user.id)


@router.get("/me/members", response_model=list[MemberResponse])
async def list_members(ctx: OwnerContext, db: AsyncSession = Depends(get_db)):
    _, tenant, _ = ctx
    return await service.list_members(db, tenant.id)


@router.post("/me/members/invite", response_model=MessageResponse, status_code=201)
async def invite_member(
    data: InviteMemberRequest,
    ctx: OwnerContext,
    db: AsyncSession = Depends(get_db),
):
    user, tenant, _ = ctx
    await service.invite_member(
        db, tenant, data.email, data.full_name, data.role, actor_user_id=user.id
    )
    return MessageResponse(message="Invitation sent")


@router.delete("/me/members/{user_id}", response_model=MessageResponse)
async def remove_member(
    user_id: UUID,
    ctx: OwnerContext,
    db: AsyncSession = Depends(get_db),
):
    user, tenant, _ = ctx
    await service.remove_member(db, tenant.id, user_id, actor_user_id=user.id)
    return MessageResponse(message="Member removed")


@router.get("/me/locations", response_model=list[LocationResponse])
async def list_locations(ctx: CurrentTenantContext, db: AsyncSession = Depends(get_db)):
    _, tenant, _ = ctx
    return await service.list_locations(db, tenant.id)


@router.post("/me/locations", response_model=LocationResponse, status_code=201)
async def create_location(
    data: LocationCreate,
    ctx: OwnerContext,
    db: AsyncSession = Depends(get_db),
):
    user, tenant, _ = ctx
    return await service.create_location(db, tenant, data, actor_user_id=user.id)


@router.patch("/me/locations/{loc_id}", response_model=LocationResponse)
async def update_location(
    loc_id: UUID,
    data: LocationUpdate,
    ctx: OwnerContext,
    db: AsyncSession = Depends(get_db),
):
    user, tenant, _ = ctx
    return await service.update_location(
        db, tenant.id, loc_id, data, actor_user_id=user.id
    )


@router.delete("/me/locations/{loc_id}", response_model=MessageResponse)
async def delete_location(
    loc_id: UUID,
    ctx: OwnerContext,
    db: AsyncSession = Depends(get_db),
):
    user, tenant, _ = ctx
    await service.delete_location(db, tenant.id, loc_id, actor_user_id=user.id)
    return MessageResponse(message="Location deleted")


@router.get("/me/tool-config")
async def get_tool_config(ctx: CurrentTenantContext, db: AsyncSession = Depends(get_db)):
    """Return the enabled tool hrefs for this tenant's business category."""
    _, tenant, _ = ctx
    category = classifyBusiness_py(tenant.business_type)
    enabled = await get_config_for_category(db, category)
    return {"category": category, "enabled_tools": enabled}


@router.get("/me/business-site")
async def get_business_site(ctx: CurrentTenantContext, db: AsyncSession = Depends(get_db)):
    from app.modules.tenants import site_service

    _, tenant, _ = ctx
    return await site_service.get_site_status(db, tenant)


@router.post("/me/business-site/bootstrap", status_code=201)
async def bootstrap_business_site(
    ctx: CurrentTenantContext,
    db: AsyncSession = Depends(get_db),
    template_slug: str | None = None,
):
    from app.modules.tenants import site_service

    user, tenant, _ = ctx
    page = await site_service.bootstrap_business_site(
        db, tenant, user.id, template_slug=template_slug
    )
    status = await site_service.get_site_status(db, tenant)
    return {**status, "redirect_to": f"/dashboard/landing-pages/{page.id}"}


@router.post("/me/business-site/publish")
async def publish_business_site(ctx: CurrentTenantContext, db: AsyncSession = Depends(get_db)):
    from app.modules.tenants import site_service

    user, tenant, _ = ctx
    return await site_service.publish_business_site(db, tenant, owner_email=user.email)


@router.get("/me/business-site/qr.png")
async def download_business_site_qr(ctx: CurrentTenantContext, db: AsyncSession = Depends(get_db)):
    from fastapi.responses import Response

    from app.modules.tenants import site_service

    _, tenant, _ = ctx
    url = site_service.business_site_public_url(tenant.slug)
    return Response(
        content=site_service.qr_png_bytes(url),
        media_type="image/png",
        headers={"Content-Disposition": f'attachment; filename="{tenant.slug}-qr.png"'},
    )
