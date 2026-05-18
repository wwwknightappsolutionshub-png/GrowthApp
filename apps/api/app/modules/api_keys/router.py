"""API key management endpoints (owner-only)."""
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import OwnerContext
from app.modules.api_keys import service

router = APIRouter(prefix="/api-keys", tags=["API Keys"])


class ApiKeyCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    scopes: list[str] = Field(default_factory=list)
    expires_at: datetime | None = None
    is_live: bool = True


class ApiKeyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    name: str
    prefix: str
    scopes: list[str]
    last_used_at: datetime | None
    expires_at: datetime | None
    revoked_at: datetime | None
    created_at: datetime


class ApiKeyCreateResponse(ApiKeyResponse):
    """Includes the full raw key — shown ONCE on creation."""

    key: str


@router.get("", response_model=list[ApiKeyResponse])
async def list_api_keys(ctx: OwnerContext, db: AsyncSession = Depends(get_db)):
    _, tenant, _ = ctx
    return await service.list_api_keys(db, tenant.id)


@router.post("", response_model=ApiKeyCreateResponse, status_code=201)
async def create_api_key(
    data: ApiKeyCreate, ctx: OwnerContext, db: AsyncSession = Depends(get_db)
):
    user, tenant, _ = ctx
    row, raw = await service.create_api_key(
        db,
        tenant_id=tenant.id,
        user_id=user.id,
        name=data.name,
        scopes=data.scopes,
        expires_at=data.expires_at,
        is_live=data.is_live,
    )
    return ApiKeyCreateResponse(
        id=row.id,
        name=row.name,
        prefix=row.prefix,
        scopes=list(row.scopes),
        last_used_at=row.last_used_at,
        expires_at=row.expires_at,
        revoked_at=row.revoked_at,
        created_at=row.created_at,
        key=raw,
    )


@router.delete("/{key_id}", response_model=ApiKeyResponse)
async def revoke_api_key(
    key_id: UUID, ctx: OwnerContext, db: AsyncSession = Depends(get_db)
):
    user, tenant, _ = ctx
    return await service.revoke_api_key(db, tenant.id, key_id, user_id=user.id)
