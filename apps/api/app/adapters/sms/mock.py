import logging
import uuid
from app.adapters.sms.base import SMSAdapter, SMSMessage, SMSResult

logger = logging.getLogger(__name__)


class MockSMSAdapter(SMSAdapter):
    async def send(self, msg: SMSMessage) -> SMSResult:
        provider_id = f"mock_sms_{uuid.uuid4().hex[:8]}"
        logger.info("[MOCK SMS] To=%s Body=%s provider_id=%s", msg.to, msg.body[:50], provider_id)
        return SMSResult(provider_id=provider_id, status="sent")

    async def send_bulk(self, messages: list[SMSMessage]) -> list[SMSResult]:
        return [await self.send(m) for m in messages]
