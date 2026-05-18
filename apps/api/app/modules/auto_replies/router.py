"""Auto-reply queue REST endpoints."""
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import CurrentTenantContext
from app.modules.auto_replies import service
from app.modules.auto_replies.models import AutoReply

router = APIRouter(prefix="/auto-replies", tags=["Auto Replies"])


class AutoReplyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    conversation_id: UUID
    channel: str
    draft: str
    status: str
    rule: str | None
    provider: str | None
    model: str | None
    reviewed_at: datetime | None
    sent_at: datetime | None
    created_at: datetime


class ApproveRequest(BaseModel):
    text: str | None = Field(default=None, max_length=4000)


@router.get("", response_model=list[AutoReplyResponse])
async def list_auto_replies(
    ctx: CurrentTenantContext,
    db: AsyncSession = Depends(get_db),
    status: str | None = Query(default="pending"),
    limit: int = Query(50, ge=1, le=200),
):
    _, tenant, _ = ctx
    q = select(AutoReply).where(AutoReply.tenant_id == tenant.id)
    if status:
        q = q.where(AutoReply.status == status)
    rows = (await db.execute(q.order_by(AutoReply.created_at.desc()).limit(limit))).scalars().all()
    return rows


@router.post("/{reply_id}/approve", response_model=AutoReplyResponse)
async def approve(
    reply_id: UUID,
    data: ApproveRequest,
    ctx: CurrentTenantContext,
    db: AsyncSession = Depends(get_db),
):
    user, tenant, _ = ctx
    return await service.approve_and_send(
        db, tenant.id, reply_id, user_id=user.id, override_text=data.text
    )


@router.post("/{reply_id}/reject", response_model=AutoReplyResponse)
async def reject(
    reply_id: UUID,
    ctx: CurrentTenantContext,
    db: AsyncSession = Depends(get_db),
):
    user, tenant, _ = ctx
    return await service.reject(db, tenant.id, reply_id, user_id=user.id)
