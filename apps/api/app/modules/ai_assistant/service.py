"""AI Assistant service.

Each turn:

  1. Persist the user message.
  2. Build the prompt (system + thread history + new user message).
  3. Call the AI router with tools.
  4. If the model returned tool calls, execute each and loop back to step 3.
  5. Persist the final assistant message; return it.

Capped at 5 tool-call iterations per turn to prevent runaway loops.
"""
from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime, timezone

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundException
from app.modules.ai_assistant.models import AIAssistantMessage, AIAssistantThread
from app.modules.ai_assistant.tools import TOOL_SCHEMAS, execute_tool
from app.services.ai.prompts import ASSISTANT_SYSTEM
from app.services.ai.router import get_ai_router
from app.services.ai.types import AIRouterError

logger = logging.getLogger(__name__)

MAX_TOOL_ITERATIONS = 5


# ── Threads ──────────────────────────────────────────────────────────────────

async def list_threads(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
    *,
    include_archived: bool = False,
    limit: int = 50,
) -> list[AIAssistantThread]:
    q = select(AIAssistantThread).where(
        AIAssistantThread.tenant_id == tenant_id,
        AIAssistantThread.user_id == user_id,
    )
    if not include_archived:
        q = q.where(AIAssistantThread.archived_at.is_(None))
    q = q.order_by(desc(AIAssistantThread.pinned), desc(AIAssistantThread.last_message_at), desc(AIAssistantThread.created_at)).limit(limit)
    return list((await db.execute(q)).scalars().all())


async def get_thread(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
    thread_id: uuid.UUID,
) -> AIAssistantThread:
    row = (
        await db.execute(
            select(AIAssistantThread).where(
                AIAssistantThread.id == thread_id,
                AIAssistantThread.tenant_id == tenant_id,
                AIAssistantThread.user_id == user_id,
            )
        )
    ).scalar_one_or_none()
    if not row:
        raise NotFoundException("Thread")
    return row


async def create_thread(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
    *,
    title: str = "New conversation",
) -> AIAssistantThread:
    thread = AIAssistantThread(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        user_id=user_id,
        title=title,
    )
    db.add(thread)
    await db.commit()
    await db.refresh(thread)
    return thread


async def list_messages(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    thread_id: uuid.UUID,
) -> list[AIAssistantMessage]:
    rows = (
        await db.execute(
            select(AIAssistantMessage)
            .where(
                AIAssistantMessage.tenant_id == tenant_id,
                AIAssistantMessage.thread_id == thread_id,
            )
            .order_by(AIAssistantMessage.created_at.asc())
        )
    ).scalars().all()
    return list(rows)


# ── The actual chat turn ─────────────────────────────────────────────────────

async def send_message(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
    thread: AIAssistantThread,
    user_content: str,
) -> AIAssistantMessage:
    """Append the user's message, run the model, return the assistant reply."""
    now = datetime.now(timezone.utc)
    user_msg = AIAssistantMessage(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        thread_id=thread.id,
        role="user",
        content=user_content,
    )
    db.add(user_msg)
    thread.last_message_at = now
    # Auto-title from the first user message (first 64 chars).
    if thread.title == "New conversation":
        thread.title = (user_content[:60].rstrip() + "…") if len(user_content) > 60 else user_content
    db.add(thread)
    await db.commit()

    # Build the prompt.
    history = await list_messages(db, tenant_id, thread.id)
    messages: list[dict] = [{"role": "system", "content": ASSISTANT_SYSTEM}]
    for m in history:
        msg: dict = {"role": m.role, "content": m.content or ""}
        if m.tool_calls:
            msg["tool_calls"] = m.tool_calls
        if m.tool_call_id:
            msg["tool_call_id"] = m.tool_call_id
        messages.append(msg)

    router = get_ai_router()
    final_response = None
    for iteration in range(MAX_TOOL_ITERATIONS):
        try:
            response = await router.chat(
                messages=messages,
                tenant_id=tenant_id,
                user_id=user_id,
                purpose="assistant_chat",
                max_tokens=800,
                temperature=0.4,
                tools=TOOL_SCHEMAS,
            )
        except AIRouterError as exc:
            logger.warning("Assistant chat failed: %s", exc)
            error_msg = AIAssistantMessage(
                id=uuid.uuid4(),
                tenant_id=tenant_id,
                thread_id=thread.id,
                role="assistant",
                content=(
                    "Sorry — I couldn't reach any AI provider just now. "
                    "Please check your AI configuration in Settings → Integrations and try again."
                ),
            )
            db.add(error_msg)
            await db.commit()
            await db.refresh(error_msg)
            return error_msg

        # If the model wants to call tools, append its message + tool results
        # and loop.
        if response.tool_calls:
            assistant_msg = AIAssistantMessage(
                id=uuid.uuid4(),
                tenant_id=tenant_id,
                thread_id=thread.id,
                role="assistant",
                content=response.content or "",
                tool_calls=response.tool_calls,
                provider=response.provider,
                model=response.model,
                input_tokens=response.input_tokens,
                output_tokens=response.output_tokens,
                cost_pence=response.cost_pence,
            )
            db.add(assistant_msg)
            await db.commit()

            # Append to the in-memory prompt so the next loop iteration sees it.
            messages.append({
                "role": "assistant",
                "content": response.content or "",
                "tool_calls": response.tool_calls,
            })

            # Execute each tool call.
            for tc in response.tool_calls:
                fn = tc.get("function", {}) or {}
                name = fn.get("name", "")
                args = fn.get("arguments", "{}")
                result = await execute_tool(db, tenant_id, name, args)
                tool_msg = AIAssistantMessage(
                    id=uuid.uuid4(),
                    tenant_id=tenant_id,
                    thread_id=thread.id,
                    role="tool",
                    content=result,
                    tool_call_id=tc.get("id"),
                )
                db.add(tool_msg)
                messages.append({
                    "role": "tool",
                    "content": result,
                    "tool_call_id": tc.get("id"),
                })
            await db.commit()
            continue  # loop back for the model to summarise

        # No tool calls → this is the final answer.
        final_response = response
        break

    if final_response is None:
        # Hit MAX_TOOL_ITERATIONS — return a message stub.
        final = AIAssistantMessage(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            thread_id=thread.id,
            role="assistant",
            content="I needed too many tool calls to answer this. Try narrowing the question.",
        )
        db.add(final)
        await db.commit()
        await db.refresh(final)
        thread.last_message_at = datetime.now(timezone.utc)
        db.add(thread)
        await db.commit()
        return final

    final_msg = AIAssistantMessage(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        thread_id=thread.id,
        role="assistant",
        content=final_response.content,
        provider=final_response.provider,
        model=final_response.model,
        input_tokens=final_response.input_tokens,
        output_tokens=final_response.output_tokens,
        cost_pence=final_response.cost_pence,
    )
    db.add(final_msg)
    thread.last_message_at = datetime.now(timezone.utc)
    db.add(thread)
    await db.commit()
    await db.refresh(final_msg)
    return final_msg
