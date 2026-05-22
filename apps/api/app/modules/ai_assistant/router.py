"""AI Assistant REST endpoints."""
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Body, Depends
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import CurrentTenantContext
from app.modules.ai_assistant import service

router = APIRouter(prefix="/ai/assistant", tags=["AI Assistant"])


class ThreadResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    title: str
    pinned: bool
    last_message_at: datetime | None
    archived_at: datetime | None
    created_at: datetime
    expires_at: datetime | None = None
    saved_at: datetime | None = None
    hours_until_expiry: float | None = None
    save_warning: bool = False


class MessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    thread_id: UUID
    role: str
    content: str
    tool_calls: list
    tool_call_id: str | None
    provider: str | None
    model: str | None
    input_tokens: int | None
    output_tokens: int | None
    cost_pence: int | None
    created_at: datetime


class SendMessageRequest(BaseModel):
    content: str = Field(min_length=1, max_length=4000)


class CreateThreadRequest(BaseModel):
    title: str | None = Field(default=None, max_length=255)


def _thread_to_response(thread) -> ThreadResponse:
    hours = service.hours_until_expiry(thread)
    warning_hours = service.save_warning_hours()
    return ThreadResponse(
        id=thread.id,
        title=thread.title,
        pinned=thread.pinned,
        last_message_at=thread.last_message_at,
        archived_at=thread.archived_at,
        created_at=thread.created_at,
        expires_at=thread.expires_at,
        saved_at=thread.saved_at,
        hours_until_expiry=hours,
        save_warning=hours is not None and hours <= warning_hours and thread.saved_at is None,
    )


@router.get("/threads", response_model=list[ThreadResponse])
async def list_threads(
    ctx: CurrentTenantContext,
    db: AsyncSession = Depends(get_db),
    include_archived: bool = False,
):
    user, tenant, _ = ctx
    rows = await service.list_threads(db, tenant.id, user.id, include_archived=include_archived)
    return [_thread_to_response(t) for t in rows]


@router.post("/threads", response_model=ThreadResponse, status_code=201)
async def create_thread(
    data: CreateThreadRequest,
    ctx: CurrentTenantContext,
    db: AsyncSession = Depends(get_db),
):
    user, tenant, _ = ctx
    thread = await service.create_thread(db, tenant.id, user.id, title=data.title or "New conversation")
    return _thread_to_response(thread)


@router.get("/threads/{thread_id}/messages", response_model=list[MessageResponse])
async def list_messages(
    thread_id: UUID,
    ctx: CurrentTenantContext,
    db: AsyncSession = Depends(get_db),
):
    user, tenant, _ = ctx
    await service.get_thread(db, tenant.id, user.id, thread_id)
    return await service.list_messages(db, tenant.id, thread_id)


@router.post("/threads/{thread_id}/messages", response_model=MessageResponse, status_code=201)
async def send_message(
    thread_id: UUID,
    data: SendMessageRequest,
    ctx: CurrentTenantContext,
    db: AsyncSession = Depends(get_db),
):
    user, tenant, _ = ctx
    thread = await service.get_thread(db, tenant.id, user.id, thread_id)
    return await service.send_message(db, tenant.id, user.id, thread, data.content)


@router.post("/threads/{thread_id}/save", response_model=ThreadResponse)
async def save_thread(
    thread_id: UUID,
    ctx: CurrentTenantContext,
    db: AsyncSession = Depends(get_db),
):
    user, tenant, _ = ctx
    thread = await service.save_thread(db, tenant.id, user.id, thread_id)
    return _thread_to_response(thread)
