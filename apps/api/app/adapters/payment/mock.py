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

    async def create_payment_intent(
        self,
        amount_pence: int,
        currency: str = "gbp",
        metadata: dict | None = None,
        customer_email: str | None = None,
        setup_future_usage: str | None = None,
    ) -> dict:
        pid = f"mock_pi_{uuid.uuid4().hex[:16]}"
        logger.info(
            "[MOCK PAYMENT] PaymentIntent %s £%.2f %s metadata=%s",
            pid,
            amount_pence / 100,
            currency,
            metadata,
        )
        if setup_future_usage:
            sid = f"mock_si_{uuid.uuid4().hex[:12]}"
            return {
                "payment_intent_id": sid,
                "client_secret": f"{sid}_secret_mock",
                "setup_intent_id": sid,
            }
        return {
            "payment_intent_id": pid,
            "client_secret": f"{pid}_secret_mock",
        }

    async def create_refund(self, payment_intent_id: str, amount_pence: int) -> dict:
        rid = f"mock_re_{uuid.uuid4().hex[:12]}"
        logger.info("[MOCK PAYMENT] Refund %s for %s amount=%s", rid, payment_intent_id, amount_pence)
        return {"refund_id": rid, "status": "succeeded"}
