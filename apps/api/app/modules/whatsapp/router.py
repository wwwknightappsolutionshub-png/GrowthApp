"""HTTP routes for the WhatsApp CRM inbox."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import CurrentTenantContext
from app.modules.messaging.schemas import SendMessageRequest
from app.modules.messaging import service as messaging_service
from app.modules.whatsapp import service as wa_service
from app.modules.whatsapp.schemas import (
    WhatsAppAIRequest,
    WhatsAppConversationDetail,
    WhatsAppConversationSummary,
    WhatsAppSendRequest,
    WhatsAppSentiment,
    WhatsAppSuggestedReply,
    WhatsAppSummary,
)

router = APIRouter(prefix="/whatsapp", tags=["WhatsApp"])


@router.get("/conversations", response_model=list[WhatsAppConversationSummary])
async def list_conversations(
    ctx: CurrentTenantContext,
    db: AsyncSession = Depends(get_db),
    page: int = 1,
    page_size: int = 30,
    status_filter: str | None = None,
):
    _, tenant, _role = ctx
    rows, _total = await wa_service.list_conversations(
        db, tenant.id, page=page, page_size=page_size, status=status_filter
    )
    return rows


@router.get("/conversations/{conv_id}", response_model=WhatsAppConversationDetail)
async def get_conversation(
    conv_id: uuid.UUID,
    ctx: CurrentTenantContext,
    db: AsyncSession = Depends(get_db),
):
    _, tenant, _role = ctx
    return await wa_service.get_conversation(db, tenant.id, conv_id)


@router.post("/send", status_code=status.HTTP_201_CREATED)
async def send_whatsapp(
    body: WhatsAppSendRequest,
    ctx: CurrentTenantContext,
    db: AsyncSession = Depends(get_db),
):
    _, tenant, _role = ctx
    msg = await messaging_service.send_message(
        db,
        tenant.id,
        SendMessageRequest(
            channel="whatsapp",
            to_address=body.to,
            body=body.body,
            customer_id=body.customer_id,
            deal_id=body.deal_id,
        ),
    )
    return {"id": str(msg.id), "status": msg.status}


@router.post("/conversations/{conv_id}/resolve")
async def resolve_conversation(
    conv_id: uuid.UUID,
    ctx: CurrentTenantContext,
    db: AsyncSession = Depends(get_db),
    resolved: bool = True,
):
    _, tenant, _role = ctx
    await wa_service.mark_resolved(db, tenant.id, conv_id, resolved=resolved)
    return {"ok": True}


# ── AI assist ────────────────────────────────────────────────────────────────


@router.post("/ai/suggest-reply", response_model=WhatsAppSuggestedReply)
async def ai_suggest_reply(
    body: WhatsAppAIRequest,
    ctx: CurrentTenantContext,
    db: AsyncSession = Depends(get_db),
):
    _, tenant, _role = ctx
    return await wa_service.suggest_reply(db, tenant.id, body.conversation_id)


@router.post("/ai/sentiment", response_model=WhatsAppSentiment)
async def ai_sentiment(
    body: WhatsAppAIRequest,
    ctx: CurrentTenantContext,
    db: AsyncSession = Depends(get_db),
):
    _, tenant, _role = ctx
    return await wa_service.analyse_sentiment(db, tenant.id, body.conversation_id)


@router.post("/ai/summarise", response_model=WhatsAppSummary)
async def ai_summarise(
    body: WhatsAppAIRequest,
    ctx: CurrentTenantContext,
    db: AsyncSession = Depends(get_db),
):
    _, tenant, _role = ctx
    return await wa_service.summarise(db, tenant.id, body.conversation_id)
