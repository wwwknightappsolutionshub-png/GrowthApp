"""Landing-page CRUD + AI generator."""
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, status

from app.core.database import get_db
from app.core.dependencies import CurrentTenantContext
from app.modules.landing_pages import service
from app.modules.landing_pages.schemas import (
    GenerateRequest,
    GenerateResponse,
    LandingPageCreate,
    LandingPageResponse,
    LandingPageUpdate,
)
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/landing-pages", tags=["Landing Pages"])


@router.get("", response_model=list[LandingPageResponse])
async def list_pages(
    ctx: CurrentTenantContext,
    db: AsyncSession = Depends(get_db),
):
    _, tenant, _ = ctx
    return await service.list_pages(db, tenant.id)


@router.post("", response_model=LandingPageResponse, status_code=status.HTTP_201_CREATED)
async def create_page(
    body: LandingPageCreate,
    ctx: CurrentTenantContext,
    db: AsyncSession = Depends(get_db),
):
    user, tenant, _ = ctx
    return await service.create_page(db, tenant.id, user.id, body)


@router.get("/{page_id}", response_model=LandingPageResponse)
async def get_page(
    page_id: UUID,
    ctx: CurrentTenantContext,
    db: AsyncSession = Depends(get_db),
):
    _, tenant, _ = ctx
    return await service._get(db, tenant.id, page_id)


@router.patch("/{page_id}", response_model=LandingPageResponse)
async def update_page(
    page_id: UUID,
    body: LandingPageUpdate,
    ctx: CurrentTenantContext,
    db: AsyncSession = Depends(get_db),
):
    _, tenant, _ = ctx
    return await service.update_page(db, tenant.id, page_id, body)


@router.delete("/{page_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_page(
    page_id: UUID,
    ctx: CurrentTenantContext,
    db: AsyncSession = Depends(get_db),
):
    _, tenant, _ = ctx
    await service.delete_page(db, tenant.id, page_id)


@router.post("/generate", response_model=GenerateResponse)
async def generate_page(
    body: GenerateRequest,
    ctx: CurrentTenantContext,
    db: AsyncSession = Depends(get_db),
):
    user, tenant, _ = ctx
    page, payload = await service.generate_page(db, tenant, user.id, body)
    return payload
