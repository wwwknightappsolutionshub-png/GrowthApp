"""WhatsApp sender module for AI Social approvals.

Exports the single public function ``send_whatsapp_approval_request``.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone

from app.adapters import get_whatsapp_adapter
from app.adapters.whatsapp.base import WhatsAppMessage
from app.modules.social.models import SocialContentDraft
from app.modules.tenants.models import Tenant

logger = logging.getLogger(__name__)


async def send_whatsapp_approval_request(
    tenant: Tenant,
    draft: SocialContentDraft,
    *,
    recipient_whatsapp: str,
) -> dict:
    """WhatsApp a tenant an approval request for an AI-generated social draft.

    Returns a dict with delivery metadata that the caller can use to populate
    the matching ``SocialApprovalQueue`` row.
    """
    body = (
        f"📣 CustomerFlow — new social draft from {tenant.name}:\n\n"
        f"{draft.text_content or ''}\n\n"
        f"Reply APPROVE to publish, or REVISE for changes.\n"
        f"Draft ID: {draft.id}"
    )

    try:
        result = await get_whatsapp_adapter().send(
            WhatsAppMessage(to=recipient_whatsapp, body=body)
        )
        logger.info(
            "[ai_social_whatsapp] draft=%s tenant=%s -> %s (status=%s provider_id=%s)",
            draft.id, tenant.id, recipient_whatsapp, result.status, result.provider_id,
        )
        return {
            "ok": result.error is None,
            "channel": "WHATSAPP",
            "sent_at": datetime.now(timezone.utc),
            "provider_id": result.provider_id,
            "status": result.status,
            "error": result.error,
            "recipient": recipient_whatsapp,
        }
    except Exception as exc:
        logger.exception(
            "[ai_social_whatsapp] FAILED draft=%s tenant=%s recipient=%s err=%s",
            draft.id, tenant.id, recipient_whatsapp, exc,
        )
        return {
            "ok": False,
            "channel": "WHATSAPP",
            "sent_at": None,
            "error": str(exc),
            "recipient": recipient_whatsapp,
        }
