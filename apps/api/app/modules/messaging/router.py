from uuid import UUID
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.dependencies import CurrentTenantContext
from app.modules.messaging import service
from app.modules.messaging.schemas import SendMessageRequest, MessageResponse, ConversationResponse

router = APIRouter(prefix="/messages", tags=["Messaging"])


@router.get("/conversations", response_model=dict)
async def list_conversations(ctx: CurrentTenantContext, db: AsyncSession = Depends(get_db), page: int = Query(1, ge=1)):
    _, tenant, _ = ctx
    items, total = await service.list_conversations(db, tenant.id, page)
    return {"items": items, "total": total}


@router.get("/conversations/{conv_id}", response_model=ConversationResponse)
async def get_conversation(conv_id: UUID, ctx: CurrentTenantContext, db: AsyncSession = Depends(get_db)):
    _, tenant, _ = ctx
    return await service.get_conversation(db, tenant.id, conv_id)


@router.post("/send", response_model=MessageResponse, status_code=201)
async def send_message(data: SendMessageRequest, ctx: CurrentTenantContext, db: AsyncSession = Depends(get_db)):
    _, tenant, _ = ctx
    return await service.send_message(db, tenant.id, data)
