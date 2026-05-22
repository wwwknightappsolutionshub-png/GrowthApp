"""Deterministic assistant responses when no external AI API is configured."""
from __future__ import annotations

import time
from typing import Any

from app.services.ai.providers.base import AIProvider
from app.services.ai.types import AIMessage, AIResponse


def _last_user_text(messages: list[AIMessage]) -> str:
    for m in reversed(messages):
        if m.get("role") == "user":
            return (m.get("content") or "").strip()
    return ""


def _mock_reply(user_text: str) -> str:
    lower = user_text.lower()
    if any(k in lower for k in ("lead", "enquir", "landing", "referral", "ads")):
        return (
            "Here is a practical lead-generation plan for your trade business:\n\n"
            "1. Publish a clear landing page with one primary call-to-action (phone + short form).\n"
            "2. Ask every happy customer for a Google review and a referral — referrals convert 3–5× better than cold ads.\n"
            "3. Run a simple weekly check: how many new leads, how many quoted, how many booked.\n\n"
            "In CustomerFlow, open **Leads** and **Landing pages** to track which source is working. "
            "I can dig into your live lead list once a cloud AI key is connected under Settings → Integrations."
        )
    if any(k in lower for k in ("convert", "pipeline", "follow", "quote", "book")):
        return (
            "To improve conversion, tighten your follow-up rhythm:\n\n"
            "• Contact new leads within 15 minutes where possible.\n"
            "• Move deals through **Quoted → Booked** with a dated next step on every card.\n"
            "• Send one friendly chase 48 hours after a quote if you have not heard back.\n\n"
            "Open **CRM → Pipeline** to drag deals forward and log notes. "
            "Connect OpenAI in Integrations for personalised follow-up drafts from your real data."
        )
    if any(k in lower for k in ("retarget", "win back", "cold", "lapsed", "dormant")):
        return (
            "Retargeting works best with a short, honest message:\n\n"
            "• Segment customers with no booking in 90+ days.\n"
            "• Offer something specific (seasonal check, small discount, priority slot).\n"
            "• Use one channel they already use (SMS or email), not both on day one.\n\n"
            "Use **Outreach** or the pipeline remarketing panel on a deal card when you are ready to send."
        )
    if any(k in lower for k in ("retain", "repeat", "loyal", "nurture", "referral")):
        return (
            "Retention is about rhythm, not one-off campaigns:\n\n"
            "• After each job, schedule the next touch (annual service, seasonal reminder).\n"
            "• Send booking reminders automatically from **Bookings → Reminders**.\n"
            "• Ask for reviews while satisfaction is high — it feeds the next lead cycle.\n\n"
            "Track repeat bookings in **Bookings** and **CRM** to see who is coming back."
        )
    if any(k in lower for k in ("crm", "coach", "pipeline", "customer")):
        return (
            "Your CRM hub is the control centre: leads become customers, customers feed deals, "
            "deals link to bookings and invoices.\n\n"
            "Start on **CRM → Pipeline** each morning — move anything stale, add a note, "
            "and book the next action. Pin your hottest deals so they stay visible."
        )
    return (
        "I am running in guidance mode because no cloud AI provider is reachable right now "
        "(add an OpenAI API key under Settings → Integrations for live data lookups).\n\n"
        "Tell me whether you want help with leads, conversion, retargeting, or retention — "
        "or pick a focus chip above — and I will outline concrete next steps for your business."
    )


class MockAIProvider(AIProvider):
    name = "mock"

    def available(self) -> bool:
        return True

    async def chat(
        self,
        messages: list[AIMessage],
        *,
        model: str | None = None,
        max_tokens: int | None = None,
        temperature: float = 0.7,
        tools: list[dict[str, Any]] | None = None,
        timeout: float = 30.0,
    ) -> AIResponse:
        del model, max_tokens, temperature, tools, timeout
        started = time.perf_counter()
        user_text = _last_user_text(messages)
        content = _mock_reply(user_text)
        latency_ms = int((time.perf_counter() - started) * 1000)
        return AIResponse(
            content=content,
            provider=self.name,
            model="mock-assistant",
            input_tokens=max(1, len(user_text) // 4),
            output_tokens=max(1, len(content) // 4),
            cost_pence=0,
            latency_ms=latency_ms,
            finish_reason="stop",
            tool_calls=[],
        )
