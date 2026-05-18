from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class SMSMessage:
    to: str
    body: str
    from_: str | None = None


@dataclass
class SMSResult:
    provider_id: str
    status: str
    error: str | None = None


class SMSAdapter(ABC):
    @abstractmethod
    async def send(self, msg: SMSMessage) -> SMSResult: ...

    @abstractmethod
    async def send_bulk(self, messages: list[SMSMessage]) -> list[SMSResult]: ...
