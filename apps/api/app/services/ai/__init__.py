"""Hybrid AI router — primary provider with automatic fallback to local LLM.

Public surface:

    from app.services.ai import get_ai_router

    router = get_ai_router()
    response = await router.chat(
        messages=[{"role": "user", "content": "Hello"}],
        tenant_id=tenant.id,
        purpose="lead_scoring",
    )
    print(response.content)

The router transparently:
  * Tries providers in `AI_PROVIDER_ORDER` (default: openai → ollama)
  * Retries transient failures `AI_MAX_RETRIES_PER_PROVIDER` times
  * Tracks tokens + cost per call into `ai_usage_events`
  * Emits structured logs that include the provider, model, latency, cost
"""
from app.services.ai.models import AIUsageEvent  # noqa: F401  (register table)
from app.services.ai.router import get_ai_router  # noqa: F401
from app.services.ai.types import AIMessage, AIResponse, AIRouterError  # noqa: F401
