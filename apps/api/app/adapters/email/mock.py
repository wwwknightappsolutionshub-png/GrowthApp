import logging
import uuid
from app.adapters.email.base import EmailAdapter, EmailMessage

logger = logging.getLogger(__name__)


class MockEmailAdapter(EmailAdapter):
    """Logs email details without sending. Safe for dev/test."""

    async def send(self, msg: EmailMessage) -> str:
        message_id = f"mock_{uuid.uuid4().hex[:12]}"
        logger.info(
            "[MOCK EMAIL] id=%s to=%s subject=%s html_length=%d",
            message_id,
            msg.to,
            msg.subject,
            len(msg.html_body),
        )
        return message_id
