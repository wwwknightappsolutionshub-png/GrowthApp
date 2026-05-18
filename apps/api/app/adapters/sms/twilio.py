import asyncio
import logging
from app.adapters.sms.base import SMSAdapter, SMSMessage, SMSResult
from app.core.config import settings

logger = logging.getLogger(__name__)


class TwilioSMSAdapter(SMSAdapter):
    """
    Twilio adapter.

    The official twilio-python SDK exposes blocking I/O. We dispatch every call
    to a thread via `asyncio.to_thread` so the event loop is never blocked on
    a network round-trip to api.twilio.com.
    """

    def __init__(self):
        from twilio.rest import Client
        self.client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        self.from_number = settings.TWILIO_FROM_NUMBER

    def _send_sync(self, body: str, to: str, from_: str):
        return self.client.messages.create(body=body, from_=from_, to=to)

    async def send(self, msg: SMSMessage) -> SMSResult:
        try:
            message = await asyncio.to_thread(
                self._send_sync,
                msg.body,
                msg.to,
                msg.from_ or self.from_number,
            )
            return SMSResult(provider_id=message.sid, status="sent")
        except Exception as e:
            logger.error("Twilio SMS error: %s", e)
            return SMSResult(provider_id="", status="failed", error=str(e))

    async def send_bulk(self, messages: list[SMSMessage]) -> list[SMSResult]:
        # Fire concurrently — each `send` is already off-loop via to_thread.
        return list(await asyncio.gather(*(self.send(m) for m in messages)))
