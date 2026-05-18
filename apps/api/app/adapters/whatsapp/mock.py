import logging
import uuid

from app.adapters.whatsapp.base import WhatsAppAdapter, WhatsAppMessage, WhatsAppResult

logger = logging.getLogger(__name__)


class MockWhatsAppAdapter(WhatsAppAdapter):
    """Logs the outgoing WhatsApp message and returns a synthetic provider ID."""

    async def send(self, msg: WhatsAppMessage) -> WhatsAppResult:
        logger.info(
            "[mock-whatsapp] to=%s body=%r template=%s media=%s",
            msg.to, msg.body[:120], msg.template, msg.media_url,
        )
        return WhatsAppResult(provider_id=f"mock_wa_{uuid.uuid4().hex[:12]}", status="sent")
