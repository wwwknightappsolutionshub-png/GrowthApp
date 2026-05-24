"""Normalize inbound integration events into inbox + CRM."""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.crm.models import Customer
from app.modules.crm.schemas import CustomerCreate
from app.modules.crm import service as crm_service
from app.modules.messaging.models import Conversation, Message
from app.modules.integrations.validators.social_payload import SocialWebhookPayload
from app.workers.queue import enqueue

logger = logging.getLogger(__name__)

CHANNEL_MAP = {
    "facebook": "facebook",
    "instagram": "instagram",
    "linkedin": "linkedin",
    "tiktok": "tiktok",
    "google": "google_gmb",
}


def _split_name(name: str | None) -> tuple[str, str | None]:
    if not name:
        return "Unknown", None
    parts = name.strip().split(None, 1)
    if len(parts) == 1:
        return parts[0], None
    return parts[0], parts[1]


async def upsert_contact_from_inbound(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    *,
    first_name: str,
    last_name: str | None = None,
    email: str | None = None,
    phone: str | None = None,
    source: str,
    tags: list[str] | None = None,
) -> Customer:
    customer: Customer | None = None
    if email:
        customer = (
            await db.execute(
                select(Customer).where(
                    Customer.tenant_id == tenant_id,
                    Customer.email == email,
                    Customer.deleted_at.is_(None),
                )
            )
        ).scalar_one_or_none()
    if not customer and phone:
        customer = (
            await db.execute(
                select(Customer).where(
                    Customer.tenant_id == tenant_id,
                    Customer.phone == phone,
                    Customer.deleted_at.is_(None),
                )
            )
        ).scalar_one_or_none()

    if customer:
        if last_name and not customer.last_name:
            customer.last_name = last_name
        if phone and not customer.phone:
            customer.phone = phone
        if email and not customer.email:
            customer.email = email
        if tags:
            note = customer.notes or ""
            tag_line = f"Tags: {', '.join(tags)}"
            if tag_line not in note:
                customer.notes = f"{note}\n{tag_line}".strip()
        db.add(customer)
        await db.flush()
        return customer

    return await crm_service.create_customer(
        db,
        tenant_id,
        CustomerCreate(
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone=phone,
            source=source,
        ),
        commit=False,
    )


async def _find_or_create_conversation(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    *,
    channel: str,
    customer_id: uuid.UUID | None,
    external_id: str | None,
    customer_email: str | None = None,
    customer_phone: str | None = None,
) -> Conversation:
    conv: Conversation | None = None
    if external_id:
        conv = (
            await db.execute(
                select(Conversation).where(
                    Conversation.tenant_id == tenant_id,
                    Conversation.channel == channel,
                    Conversation.external_id == external_id,
                )
            )
        ).scalar_one_or_none()
    if not conv and customer_id:
        conv = (
            await db.execute(
                select(Conversation).where(
                    Conversation.tenant_id == tenant_id,
                    Conversation.channel == channel,
                    Conversation.customer_id == customer_id,
                )
            )
        ).scalar_one_or_none()
    if not conv:
        conv = Conversation(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            channel=channel,
            customer_id=customer_id,
            external_id=external_id,
            customer_email=customer_email,
            customer_phone=customer_phone,
        )
        db.add(conv)
        await db.flush()
    return conv


async def ingest_inbound_message(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    *,
    channel: str,
    body: str,
    sender_name: str | None = None,
    sender_email: str | None = None,
    sender_phone: str | None = None,
    external_id: str | None = None,
    source: str,
    tags: list[str] | None = None,
) -> Message:
    first, last = _split_name(sender_name)
    customer = await upsert_contact_from_inbound(
        db,
        tenant_id,
        first_name=first,
        last_name=last,
        email=sender_email,
        phone=sender_phone,
        source=source,
        tags=tags,
    )
    conv = await _find_or_create_conversation(
        db,
        tenant_id,
        channel=channel,
        customer_id=customer.id,
        external_id=external_id,
        customer_email=sender_email,
        customer_phone=sender_phone,
    )
    msg = Message(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        conversation_id=conv.id,
        direction="inbound",
        channel=channel,
        from_address=sender_email or sender_phone or sender_name,
        body=body,
        status="received",
        provider_message_id=external_id,
    )
    db.add(msg)
    conv.last_message_at = datetime.now(timezone.utc)
    db.add(conv)
    await db.flush()

    await enqueue(
        "trigger_automation_for_event",
        tenant_id=str(tenant_id),
        event_type="message.received",
        payload={
            "channel": channel,
            "customer_id": str(customer.id),
            "message_id": str(msg.id),
            "source": source,
        },
    )
    return msg


async def ingest_social_webhook(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    payload: SocialWebhookPayload,
) -> dict[str, Any]:
    channel = CHANNEL_MAP.get(payload.platform, payload.platform)
    source = f"{payload.platform}_{payload.event_type}"

    if payload.event_type == "lead":
        first, last = _split_name(payload.sender_name)
        customer = await upsert_contact_from_inbound(
            db,
            tenant_id,
            first_name=first or "Lead",
            last_name=last,
            email=payload.sender_email,
            phone=payload.sender_phone,
            source=source,
            tags=payload.tags,
        )
        await enqueue(
            "trigger_automation_for_event",
            tenant_id=str(tenant_id),
            event_type="lead.received",
            payload={
                "channel": channel,
                "customer_id": str(customer.id),
                "source": source,
            },
        )
        return {"customer_id": str(customer.id), "event": "lead"}

    if payload.event_type == "post_status":
        return {"event": "post_status", "status": payload.status, "post_id": payload.post_id}

    body = payload.body_text()
    if not body:
        body = f"New {payload.event_type} on {payload.platform}"

    msg = await ingest_inbound_message(
        db,
        tenant_id,
        channel=channel,
        body=body,
        sender_name=payload.sender_name,
        sender_email=payload.sender_email,
        sender_phone=payload.sender_phone,
        external_id=payload.external_id or payload.post_id,
        source=source,
        tags=payload.tags,
    )
    return {"message_id": str(msg.id), "event": payload.event_type}


async def ingest_google_message(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    *,
    sender_name: str,
    body: str,
    external_id: str | None,
) -> Message:
    return await ingest_inbound_message(
        db,
        tenant_id,
        channel="google_gmb",
        body=body,
        sender_name=sender_name,
        external_id=external_id,
        source="google_gmb_message",
    )
