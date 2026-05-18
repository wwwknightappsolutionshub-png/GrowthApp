"""Email sender module for AI Social approvals.

Exports the single public function ``send_social_approval_request``.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone

from app.adapters import get_email_adapter
from app.adapters.email.base import EmailMessage
from app.modules.social.models import SocialContentDraft
from app.modules.tenants.models import Tenant

logger = logging.getLogger(__name__)


async def send_social_approval_request(
    tenant: Tenant,
    draft: SocialContentDraft,
    *,
    recipient_email: str,
) -> dict:
    """Email a tenant an approval request for an AI-generated social draft.

    Returns a dict with delivery metadata that the caller can use to populate
    the matching ``SocialApprovalQueue`` row.
    """
    subject = f"[CustomerFlow] Approve social draft — {tenant.name}"
    text_body = (
        f"Hi {tenant.name},\n\n"
        f"A new social draft is ready for your approval:\n\n"
        f"{draft.text_content or ''}\n\n"
        f"Reply APPROVE to publish, or REVISE for changes.\n"
        f"Draft ID: {draft.id}\n"
    )
    html_body = (
        f"<p>Hi <strong>{tenant.name}</strong>,</p>"
        f"<p>A new social draft is ready for your approval:</p>"
        f"<blockquote style='border-left:4px solid #2563eb;padding-left:12px;color:#374151;'>"
        f"{(draft.text_content or '').replace(chr(10), '<br/>')}"
        f"</blockquote>"
        f"<p>Reply <strong>APPROVE</strong> to publish, or <strong>REVISE</strong> for changes.</p>"
        f"<p style='color:#6b7280;font-size:12px;'>Draft ID: {draft.id}</p>"
    )

    try:
        provider_id = await get_email_adapter().send(
            EmailMessage(
                to=recipient_email,
                subject=subject,
                text_body=text_body,
                html_body=html_body,
            )
        )
        logger.info(
            "[ai_social_email] draft=%s tenant=%s -> %s (provider_id=%s)",
            draft.id, tenant.id, recipient_email, provider_id,
        )
        return {
            "ok": True,
            "channel": "EMAIL",
            "sent_at": datetime.now(timezone.utc),
            "provider_id": provider_id,
            "recipient": recipient_email,
        }
    except Exception as exc:
        logger.exception(
            "[ai_social_email] FAILED draft=%s tenant=%s recipient=%s err=%s",
            draft.id, tenant.id, recipient_email, exc,
        )
        return {
            "ok": False,
            "channel": "EMAIL",
            "sent_at": None,
            "error": str(exc),
            "recipient": recipient_email,
        }
