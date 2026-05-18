"""Business logic for the WhatsApp inbox + AI assist.

The WhatsApp channel reuses the generic `conversations` / `messages` tables
with `channel='whatsapp'`. Outbound sends go through `messaging.service.send_message`
so audit logging, quota accounting and worker dispatch stay in one place.
"""
from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime, timezone

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundException
from app.modules.crm.models import Customer
from app.modules.messaging.models import Conversation, Message
from app.services.ai.router import get_ai_router
from app.services.ai.types import AIRouterError

logger = logging.getLogger(__name__)


# ── Conversation listing ────────────────────────────────────────────────────


async def list_conversations(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    *,
    page: int = 1,
    page_size: int = 30,
    status: str | None = None,  # "open" | "resolved" | "all"
) -> tuple[list[dict], int]:
    stmt = (
        select(Conversation)
        .where(Conversation.tenant_id == tenant_id, Conversation.channel == "whatsapp")
        .order_by(Conversation.last_message_at.desc().nullslast())
    )
    if status == "open":
        stmt = stmt.where(Conversation.is_resolved.is_(False))
    elif status == "resolved":
        stmt = stmt.where(Conversation.is_resolved.is_(True))

    total = (
        await db.execute(select(func.count()).select_from(stmt.subquery()))
    ).scalar_one()
    rows = (
        await db.execute(stmt.offset((page - 1) * page_size).limit(page_size))
    ).scalars().all()

    summaries: list[dict] = []
    for conv in rows:
        last_msg = (
            await db.execute(
                select(Message)
                .where(Message.conversation_id == conv.id)
                .order_by(desc(Message.created_at))
                .limit(1)
            )
        ).scalar_one_or_none()

        customer_name: str | None = None
        if conv.customer_id:
            cust = (
                await db.execute(select(Customer).where(Customer.id == conv.customer_id))
            ).scalar_one_or_none()
            if cust:
                customer_name = " ".join(
                    p for p in [getattr(cust, "first_name", None), getattr(cust, "last_name", None)] if p
                ) or None

        summaries.append(
            {
                "id": conv.id,
                "customer_id": conv.customer_id,
                "customer_phone": conv.customer_phone,
                "last_message_at": conv.last_message_at,
                "is_resolved": conv.is_resolved,
                "unread_count": 0,  # placeholder until per-user read state lands
                "last_preview": (last_msg.body[:140] if last_msg else None),
                "last_direction": (last_msg.direction if last_msg else None),
                "customer_name": customer_name,
            }
        )
    return summaries, total


async def get_conversation(
    db: AsyncSession, tenant_id: uuid.UUID, conv_id: uuid.UUID
) -> dict:
    conv = (
        await db.execute(
            select(Conversation).where(
                Conversation.id == conv_id,
                Conversation.tenant_id == tenant_id,
                Conversation.channel == "whatsapp",
            )
        )
    ).scalar_one_or_none()
    if not conv:
        raise NotFoundException("Conversation")

    messages = (
        await db.execute(
            select(Message)
            .where(Message.conversation_id == conv.id)
            .order_by(Message.created_at.asc())
        )
    ).scalars().all()

    customer_name: str | None = None
    if conv.customer_id:
        cust = (
            await db.execute(select(Customer).where(Customer.id == conv.customer_id))
        ).scalar_one_or_none()
        if cust:
            customer_name = " ".join(
                p for p in [getattr(cust, "first_name", None), getattr(cust, "last_name", None)] if p
            ) or None

    return {
        "id": conv.id,
        "customer_id": conv.customer_id,
        "customer_phone": conv.customer_phone,
        "last_message_at": conv.last_message_at,
        "is_resolved": conv.is_resolved,
        "unread_count": 0,
        "last_preview": (messages[-1].body[:140] if messages else None),
        "last_direction": (messages[-1].direction if messages else None),
        "customer_name": customer_name,
        "messages": [
            {
                "id": m.id,
                "direction": m.direction,
                "body": m.body,
                "from_address": m.from_address,
                "to_address": m.to_address,
                "status": m.status,
                "created_at": m.created_at,
            }
            for m in messages
        ],
    }


async def mark_resolved(
    db: AsyncSession, tenant_id: uuid.UUID, conv_id: uuid.UUID, *, resolved: bool
) -> None:
    conv = (
        await db.execute(
            select(Conversation).where(
                Conversation.id == conv_id,
                Conversation.tenant_id == tenant_id,
            )
        )
    ).scalar_one_or_none()
    if not conv:
        raise NotFoundException("Conversation")
    conv.is_resolved = resolved
    db.add(conv)
    await db.commit()


async def list_recent_inbound_for_inbox(
    db: AsyncSession, tenant_id: uuid.UUID, *, limit: int = 30
) -> list[Message]:
    """Used by the dashboard inbox card."""
    return list(
        (
            await db.execute(
                select(Message)
                .where(
                    Message.tenant_id == tenant_id,
                    Message.channel == "whatsapp",
                    Message.direction == "inbound",
                )
                .order_by(Message.created_at.desc())
                .limit(limit)
            )
        )
        .scalars()
        .all()
    )


# ── AI assist ────────────────────────────────────────────────────────────────

_SUGGEST_SYSTEM = (
    "You are an enterprise-class WhatsApp Business assistant for a UK SMB. "
    "Given the conversation so far, draft the next reply for the BUSINESS to "
    "send to the customer. Write naturally, in British English, polite, "
    "concise (≤ 220 chars), and never make up facts. If the customer is "
    "asking for a quote or booking, suggest the next concrete step. Output "
    "ONLY the reply body — no labels, no markdown."
)

_SENTIMENT_SYSTEM = (
    "You are a sentiment classifier. Read the conversation and label the "
    "customer's CURRENT mood as one of: positive, neutral, negative, urgent. "
    "Output strict JSON: {\"label\":\"...\",\"score\":<-1..1>,\"reason\":\"...\"}. "
    "Score is +1 (delighted) to -1 (angry). 'urgent' = needs reply within 1h."
)

_SUMMARY_SYSTEM = (
    "Summarise this WhatsApp conversation for a busy operator. Output strict "
    "JSON: {\"summary\":\"…\",\"bullets\":[\"…\",\"…\"],\"next_action\":\"…\"}. "
    "Keep summary under 280 chars. Bullets max 3, each ≤ 80 chars. next_action "
    "is the single best next move (e.g. 'Send quote', 'Schedule callback')."
)


def _conversation_to_transcript(messages: list[dict]) -> str:
    lines: list[str] = []
    for m in messages:
        who = "Customer" if m["direction"] == "inbound" else "Business"
        when = m["created_at"].strftime("%Y-%m-%d %H:%M") if m.get("created_at") else ""
        lines.append(f"[{when}] {who}: {m['body']}")
    return "\n".join(lines[-30:])  # keep prompt compact


async def suggest_reply(
    db: AsyncSession, tenant_id: uuid.UUID, conv_id: uuid.UUID
) -> dict:
    detail = await get_conversation(db, tenant_id, conv_id)
    transcript = _conversation_to_transcript(detail["messages"])
    if not transcript:
        return {"suggestion": "", "tone": "professional", "requires_review": True}

    try:
        router_svc = get_ai_router()
        response = await router_svc.chat(
            messages=[
                {"role": "system", "content": _SUGGEST_SYSTEM},
                {"role": "user", "content": transcript},
            ],
            tenant_id=tenant_id,
            purpose="whatsapp_suggest_reply",
            max_tokens=200,
            temperature=0.5,
        )
        suggestion = response.content.strip()
    except AIRouterError as exc:
        logger.warning("whatsapp suggest_reply failed: %s", exc)
        suggestion = (
            "Thanks for getting in touch — I'll come back to you with details shortly."
        )

    return {"suggestion": suggestion, "tone": "professional", "requires_review": True}


async def analyse_sentiment(
    db: AsyncSession, tenant_id: uuid.UUID, conv_id: uuid.UUID
) -> dict:
    detail = await get_conversation(db, tenant_id, conv_id)
    transcript = _conversation_to_transcript(detail["messages"])
    if not transcript:
        return {"label": "neutral", "score": 0.0, "reason": "No messages yet."}

    try:
        router_svc = get_ai_router()
        response = await router_svc.chat(
            messages=[
                {"role": "system", "content": _SENTIMENT_SYSTEM},
                {"role": "user", "content": transcript},
            ],
            tenant_id=tenant_id,
            purpose="whatsapp_sentiment",
            max_tokens=120,
            temperature=0.0,
        )
        payload = _parse_json_loose(response.content)
        if not payload:
            return {"label": "neutral", "score": 0.0, "reason": None}
        label = str(payload.get("label", "neutral")).lower()
        if label not in {"positive", "neutral", "negative", "urgent"}:
            label = "neutral"
        score = float(payload.get("score", 0.0))
        score = max(-1.0, min(1.0, score))
        return {"label": label, "score": score, "reason": payload.get("reason")}
    except AIRouterError as exc:
        logger.warning("whatsapp sentiment failed: %s", exc)
        return {"label": "neutral", "score": 0.0, "reason": "AI unavailable"}


async def summarise(
    db: AsyncSession, tenant_id: uuid.UUID, conv_id: uuid.UUID
) -> dict:
    detail = await get_conversation(db, tenant_id, conv_id)
    transcript = _conversation_to_transcript(detail["messages"])
    if not transcript:
        return {"summary": "No messages yet.", "bullets": [], "next_action": None}

    try:
        router_svc = get_ai_router()
        response = await router_svc.chat(
            messages=[
                {"role": "system", "content": _SUMMARY_SYSTEM},
                {"role": "user", "content": transcript},
            ],
            tenant_id=tenant_id,
            purpose="whatsapp_summary",
            max_tokens=300,
            temperature=0.2,
        )
        payload = _parse_json_loose(response.content)
        if not payload:
            return {"summary": response.content[:280], "bullets": [], "next_action": None}
        bullets = payload.get("bullets") or []
        if not isinstance(bullets, list):
            bullets = [str(bullets)]
        return {
            "summary": str(payload.get("summary", ""))[:280],
            "bullets": [str(b)[:80] for b in bullets[:3]],
            "next_action": payload.get("next_action"),
        }
    except AIRouterError as exc:
        logger.warning("whatsapp summarise failed: %s", exc)
        return {"summary": "AI summary unavailable.", "bullets": [], "next_action": None}


def _parse_json_loose(text: str) -> dict | None:
    """Best-effort JSON parsing — small models sometimes pad with prose."""
    if not text:
        return None
    text = text.strip()
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end < start:
        return None
    try:
        return json.loads(text[start : end + 1])
    except json.JSONDecodeError:
        return None
