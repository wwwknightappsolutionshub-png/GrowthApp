import stripe
from app.adapters.payment.base import CheckoutSessionResult, PaymentAdapter, PaymentLinkResult
from app.core.config import settings


class StripePaymentAdapter(PaymentAdapter):
    def __init__(self):
        stripe.api_key = settings.STRIPE_SECRET_KEY

    async def create_customer(self, email: str, name: str, metadata: dict) -> str:
        customer = stripe.Customer.create(email=email, name=name, metadata=metadata)
        return customer.id

    async def create_checkout_session(self, customer_id: str, price_id: str, success_url: str, cancel_url: str) -> CheckoutSessionResult:
        session = stripe.checkout.Session.create(
            customer=customer_id,
            payment_method_types=["card"],
            line_items=[{"price": price_id, "quantity": 1}],
            mode="subscription",
            success_url=success_url,
            cancel_url=cancel_url,
        )
        return CheckoutSessionResult(session_id=session.id, checkout_url=session.url)

    async def create_payment_link(self, amount_pence: int, description: str, metadata: dict) -> PaymentLinkResult:
        price = stripe.Price.create(
            currency="gbp",
            unit_amount=amount_pence,
            product_data={"name": description},
        )
        link = stripe.PaymentLink.create(line_items=[{"price": price.id, "quantity": 1}])
        return PaymentLinkResult(url=link.url)

    async def create_customer_portal(self, customer_id: str, return_url: str) -> str:
        session = stripe.billing_portal.Session.create(customer=customer_id, return_url=return_url)
        return session.url

    async def verify_webhook(self, payload: bytes, sig: str) -> dict:
        event = stripe.Webhook.construct_event(payload, sig, settings.STRIPE_WEBHOOK_SECRET)
        return dict(event)
