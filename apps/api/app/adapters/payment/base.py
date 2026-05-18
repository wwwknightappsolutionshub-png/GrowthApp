from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class CheckoutSessionResult:
    session_id: str
    checkout_url: str


@dataclass
class PaymentLinkResult:
    url: str


class PaymentAdapter(ABC):
    @abstractmethod
    async def create_customer(self, email: str, name: str, metadata: dict) -> str: ...

    @abstractmethod
    async def create_checkout_session(
        self, customer_id: str, price_id: str, success_url: str, cancel_url: str
    ) -> CheckoutSessionResult: ...

    @abstractmethod
    async def create_payment_link(
        self, amount_pence: int, description: str, metadata: dict
    ) -> PaymentLinkResult: ...

    @abstractmethod
    async def create_customer_portal(self, customer_id: str, return_url: str) -> str: ...

    @abstractmethod
    async def verify_webhook(self, payload: bytes, sig: str) -> dict: ...
