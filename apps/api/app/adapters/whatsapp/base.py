from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class WhatsAppMessage:
    to: str  # E.164 phone number, no "whatsapp:" prefix — adapter adds it.
    body: str
    from_: str | None = None
    # Optional template name + variables for first-contact messages outside
    # the 24h customer-service window (Meta requires templates there).
    template: str | None = None
    template_vars: dict | None = None
    # Optional media URL (image/document) — must be public for Twilio to fetch.
    media_url: str | None = None


@dataclass
class WhatsAppResult:
    provider_id: str
    status: str
    error: str | None = None


class WhatsAppAdapter(ABC):
    @abstractmethod
    async def send(self, msg: WhatsAppMessage) -> WhatsAppResult: ...
