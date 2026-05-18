import uuid
from datetime import datetime, timezone
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.core.exceptions import NotFoundException
from app.modules.messaging.models import Conversation, Message
from app.modules.messaging.schemas import SendMessageRequest


async def list_conversations(db: AsyncSession, tenant_id: uuid.UUID, page: int = 1, page_size: int = 25) -> tuple[list[Conversation], int]:
    q = select(Conversation).where(Conversation.tenant_id == tenant_id)
    total = (await db.execute(select(func.count()).select_from(q.subquery()))).scalar_one()
    items = (await db.execute(q.order_by(Conversation.last_message_at.desc().nullslast()).offset((page-1)*page_size).limit(page_size))).scalars().all()
    return list(items), total


async def get_conversation(db: AsyncSession, tenant_id: uuid.UUID, conv_id: uuid.UUID) -> Conversation:
    result = await db.execute(
        select(Conversation).options(selectinload(Conversation.messages))
        .where(Conversation.id == conv_id, Conversation.tenant_id == tenant_id)
    )
    c = result.scalar_one_or_none()
    if not c:
        raise NotFoundException("Conversation")
    return c


async def send_message(db: AsyncSession, tenant_id: uuid.UUID, data: SendMessageRequest) -> Message:
    # Find or create conversation
    conv = None
    if data.deal_id:
        result = await db.execute(select(Conversation).where(Conversation.deal_id == data.deal_id, Conversation.channel == data.channel))
        conv = result.scalar_one_or_none()

    if not conv:
        conv = Conversation(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            deal_id=data.deal_id,
            customer_id=data.customer_id,
            channel=data.channel,
            customer_phone=data.to_address if data.channel in ("sms", "whatsapp") else None,
            customer_email=data.to_address if data.channel == "email" else None,
        )
        db.add(conv)
        await db.flush()

    msg = Message(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        conversation_id=conv.id,
        direction="outbound",
        channel=data.channel,
        to_address=data.to_address,
        subject=data.subject,
        body=data.body,
        status="queued",
    )
    db.add(msg)
    conv.last_message_at = datetime.now(timezone.utc)
    db.add(conv)
    await db.commit()
    await db.refresh(msg)

    # Enqueue actual send
    from app.workers.queue import enqueue
    if data.channel == "sms":
        await enqueue("send_sms_task", to=data.to_address, body=data.body, tenant_id=str(tenant_id), message_id=str(msg.id))
    elif data.channel == "email":
        await enqueue("send_email_task", to=data.to_address, subject=data.subject or "", html=data.body, tenant_id=str(tenant_id), message_id=str(msg.id))
    elif data.channel == "whatsapp":
        await enqueue("send_whatsapp_task", to=data.to_address, body=data.body, tenant_id=str(tenant_id), message_id=str(msg.id))

    return msg
