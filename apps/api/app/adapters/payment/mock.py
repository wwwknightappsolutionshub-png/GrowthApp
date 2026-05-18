import logging
import uuid
from app.adapters.payment.base import CheckoutSessionResult, PaymentAdapter, PaymentLinkResult

logger = logging.getLogger(__name__)


class MockPaymentAdapter(PaymentAdapter):
    async def create_customer(self, email: str, name: str, metadata: dict) -> str:
        cid = f"mock_cus_{uuid.uuid4().hex[:12]}"
        logger.info("[MOCK PAYMENT] Created customer: %s -> %s", email, cid)
        return cid

    async def create_checkout_session(self, customer_id: str, price_id: str, success_url: str, cancel_url: str) -> CheckoutSessionResult:
        sid = f"mock_cs_{uuid.uuid4().hex[:12]}"
        logger.info("[MOCK PAYMENT] Checkout session %s for price %s", sid, price_id)
        return CheckoutSessionResult(session_id=sid, checkout_url=f"{success_url}?mock_session={sid}")

    async def create_payment_link(self, amount_pence: int, description: str, metadata: dict) -> PaymentLinkResult:
        logger.info("[MOCK PAYMENT] Payment link for £%.2f: %s", amount_pence / 100, description)
        return PaymentLinkResult(url=f"https://mock-payment.example.com/pay/{uuid.uuid4().hex[:8]}")

    async def create_customer_portal(self, customer_id: str, return_url: str) -> str:
        return f"https://mock-billing.example.com/portal/{customer_id}"

    async def verify_webhook(self, payload: bytes, sig: str) -> dict:
        return {"type": "mock.event", "data": {"object": {}}}
