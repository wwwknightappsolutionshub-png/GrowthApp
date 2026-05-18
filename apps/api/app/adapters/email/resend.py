import logging
import resend
from app.adapters.email.base import EmailAdapter, EmailMessage

logger = logging.getLogger(__name__)


class ResendEmailAdapter(EmailAdapter):
    def __init__(self, api_key: str, from_email: str = "noreply@yourdomain.com", from_name: str = "CustomerFlow AI"):
        self._from_email = from_email
        self._from_name = from_name
        resend.api_key = api_key

    async def send(self, msg: EmailMessage) -> str:
        from_address = f"{msg.from_name or self._from_name} <{msg.from_email or self._from_email}>"
        to_address = f"{msg.to_name} <{msg.to}>" if msg.to_name else msg.to

        params: resend.Emails.SendParams = {
            "from": from_address,
            "to": [to_address],
            "subject": msg.subject,
            "html": msg.html_body,
        }
        if msg.text_body:
            params["text"] = msg.text_body
        if msg.reply_to:
            params["reply_to"] = [msg.reply_to]

        try:
            result = resend.Emails.send(params)
            message_id: str = result.get("id", "")
            logger.info("Resend email sent id=%s to=%s subject=%s", message_id, msg.to, msg.subject)
            return message_id
        except Exception as exc:
            logger.error("Resend send failed to=%s subject=%s error=%s", msg.to, msg.subject, exc)
            raise
