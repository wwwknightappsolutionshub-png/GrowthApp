"""Twilio WhatsApp Business adapter.

Twilio exposes WhatsApp via the same Messages API as SMS — the difference is
the channel prefix on `from`/`to` (``whatsapp:+...``) and the optional use of
pre-approved Message Templates for first-contact outside the 24h window.
"""
import asyncio
import logging

from app.adapters.whatsapp.base import WhatsAppAdapter, WhatsAppMessage, WhatsAppResult
from app.core.config import settings

logger = logging.getLogger(__name__)


def _wa_prefix(num: str) -> str:
    """Ensure E.164 numbers carry Twilio's whatsapp: channel prefix."""
    if num.startswith("whatsapp:"):
        return num
    return f"whatsapp:{num}"


class TwilioWhatsAppAdapter(WhatsAppAdapter):
    def __init__(self) -> None:
        from twilio.rest import Client

        self.client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        self.from_number = settings.TWILIO_WHATSAPP_FROM_NUMBER or settings.TWILIO_FROM_NUMBER

    def _send_sync(self, msg: WhatsAppMessage):
        kwargs = {
            "from_": _wa_prefix(msg.from_ or self.from_number),
            "to": _wa_prefix(msg.to),
        }
        if msg.template and settings.TWILIO_WHATSAPP_CONTENT_SID:
            kwargs["content_sid"] = settings.TWILIO_WHATSAPP_CONTENT_SID
            if msg.template_vars:
                import json

                kwargs["content_variables"] = json.dumps(msg.template_vars)
        else:
            kwargs["body"] = msg.body
            if msg.media_url:
                kwargs["media_url"] = [msg.media_url]
        return self.client.messages.create(**kwargs)

    async def send(self, msg: WhatsAppMessage) -> WhatsAppResult:
        try:
            message = await asyncio.to_thread(self._send_sync, msg)
            return WhatsAppResult(provider_id=message.sid, status="sent")
        except Exception as exc:
            logger.error("Twilio WhatsApp error: %s", exc)
            return WhatsAppResult(provider_id="", status="failed", error=str(exc))
