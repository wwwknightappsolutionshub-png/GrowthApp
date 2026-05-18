from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class EmailMessage:
    to: str
    to_name: str | None = None
    subject: str = ""
    html_body: str = ""
    text_body: str = ""
    from_email: str | None = None
    from_name: str | None = None
    reply_to: str | None = None


class EmailAdapter(ABC):
    @abstractmethod
    async def send(self, msg: EmailMessage) -> str: ...
