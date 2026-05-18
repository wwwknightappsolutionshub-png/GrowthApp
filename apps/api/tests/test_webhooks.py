"""Webhook signature verification + Stripe invoice handler."""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time
import uuid

import pytest
from sqlalchemy import select

from app.core.config import settings
from app.modules.webhooks.router import (
    _verify_svix_signature,
    _verify_twilio_signature,
)


# ──────────────────────────────────────────────────────────────────────────
# Twilio signature
# ──────────────────────────────────────────────────────────────────────────

def _sign_twilio(auth_token: str, url: str, params: dict[str, str]) -> str:
    payload = url + "".join(f"{k}{params[k]}" for k in sorted(params.keys()))
    return base64.b64encode(
        hmac.new(auth_token.encode(), payload.encode(), hashlib.sha1).digest()
    ).decode()


def test_twilio_signature_accepts_correct_signature():
    token = "test-auth-token"
    url = "https://api.example.com/api/v1/webhooks/twilio/sms"
    params = {"From": "+447700900111", "To": "+441632960123", "Body": "hi"}
    sig = _sign_twilio(token, url, params)
    assert _verify_twilio_signature(token, url, params, sig) is True


def test_twilio_signature_rejects_tampered_body():
    token = "test-auth-token"
    url = "https://api.example.com/api/v1/webhooks/twilio/sms"
    params = {"From": "+447700900111", "Body": "hi"}
    sig = _sign_twilio(token, url, params)
    params["Body"] = "evil"
    assert _verify_twilio_signature(token, url, params, sig) is False


def test_twilio_signature_rejects_empty():
    assert _verify_twilio_signature("", "u", {}, "") is False
    assert _verify_twilio_signature("token", "u", {}, "") is False


@pytest.mark.asyncio
async def test_twilio_sms_endpoint_rejects_unsigned(client, monkeypatch):
    """End-to-end: hitting /webhooks/twilio/sms without a signature is 401."""
    monkeypatch.setattr(settings, "TWILIO_AUTH_TOKEN", "test-auth-token")
    res = await client.post(
        "/api/v1/webhooks/twilio/sms",
        data={"From": "+447700900111", "Body": "hi", "MessageSid": "SM1"},
    )
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_twilio_sms_endpoint_503_when_not_configured(client, monkeypatch):
    monkeypatch.setattr(settings, "TWILIO_AUTH_TOKEN", "")
    res = await client.post(
        "/api/v1/webhooks/twilio/sms",
        data={"From": "+447700900111", "Body": "hi"},
    )
    assert res.status_code == 503


# ──────────────────────────────────────────────────────────────────────────
# Resend / Svix signature
# ──────────────────────────────────────────────────────────────────────────

def _make_svix_secret(raw: bytes = b"\x00" * 32) -> str:
    return "whsec_" + base64.b64encode(raw).decode()


def _sign_svix(secret: str, msg_id: str, timestamp: str, body: bytes) -> str:
    key_b64 = secret.split("_", 1)[-1]
    key = base64.b64decode(key_b64)
    signed = f"{msg_id}.{timestamp}.".encode() + body
    sig = base64.b64encode(hmac.new(key, signed, hashlib.sha256).digest()).decode()
    return f"v1,{sig}"


def test_svix_signature_accepts_correct():
    secret = _make_svix_secret(b"\x12" * 32)
    body = b'{"type":"email.delivered","data":{"email_id":"em_1"}}'
    msg_id = "msg_test"
    timestamp = str(int(time.time()))
    header = _sign_svix(secret, msg_id, timestamp, body)
    assert _verify_svix_signature(secret, msg_id, timestamp, body, header) is True


def test_svix_signature_rejects_expired_timestamp():
    secret = _make_svix_secret(b"\x12" * 32)
    body = b"{}"
    msg_id = "msg"
    # 1 hour old
    timestamp = str(int(time.time()) - 3600)
    header = _sign_svix(secret, msg_id, timestamp, body)
    assert _verify_svix_signature(secret, msg_id, timestamp, body, header) is False


def test_svix_signature_rejects_wrong_secret():
    a = _make_svix_secret(b"\x12" * 32)
    b = _make_svix_secret(b"\x34" * 32)
    body = b"{}"
    msg_id = "msg"
    timestamp = str(int(time.time()))
    header = _sign_svix(a, msg_id, timestamp, body)
    assert _verify_svix_signature(b, msg_id, timestamp, body, header) is False


@pytest.mark.asyncio
async def test_resend_endpoint_rejects_unsigned(client, monkeypatch):
    monkeypatch.setattr(settings, "RESEND_WEBHOOK_SECRET", _make_svix_secret(b"\x42" * 32))
    res = await client.post("/api/v1/webhooks/resend", json={"type": "email.delivered"})
    assert res.status_code == 401


# ──────────────────────────────────────────────────────────────────────────
# Stripe invoice.payment_succeeded
# ──────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_stripe_invoice_payment_succeeded_creates_billing_row(client, db_session, monkeypatch):
    """Verify the no-op `pass` is gone — an event creates a BillingInvoice."""
    from app.modules.billing.models import BillingInvoice, Subscription
    from app.modules.tenants.models import Tenant

    # Make sig verification a no-op for this test.
    class FakeAdapter:
        async def verify_webhook(self, payload, sig):
            return json.loads(payload.decode())

    from app.adapters import get_payment_adapter
    get_payment_adapter.cache_clear()  # type: ignore[attr-defined]
    monkeypatch.setattr("app.adapters.get_payment_adapter", lambda: FakeAdapter())

    # Seed a tenant + subscription linking stripe_subscription_id="sub_abc"
    tenant = Tenant(
        id=uuid.uuid4(), slug="acme", name="Acme", business_type="plumber", postcode="SW1A1AA",
    )
    db_session.add(tenant)
    await db_session.flush()
    sub = Subscription(
        id=uuid.uuid4(),
        tenant_id=tenant.id,
        plan_id=uuid.uuid4(),
        stripe_customer_id="cus_test",
        stripe_subscription_id="sub_abc",
        status="active",
    )
    db_session.add(sub)
    await db_session.commit()

    event = {
        "id": "evt_test",
        "type": "invoice.payment_succeeded",
        "data": {
            "object": {
                "id": "in_test_1",
                "customer": "cus_test",
                "subscription": "sub_abc",
                "amount_paid": 14900,
                "currency": "gbp",
                "status": "paid",
                "invoice_pdf": "https://example.com/invoice.pdf",
                "period_start": 1_700_000_000,
                "period_end": 1_702_500_000,
            }
        },
    }

    res = await client.post(
        "/api/v1/webhooks/stripe",
        content=json.dumps(event).encode(),
        headers={"stripe-signature": "sig_ignored"},
    )
    assert res.status_code == 200

    row = (await db_session.execute(
        select(BillingInvoice).where(BillingInvoice.stripe_invoice_id == "in_test_1")
    )).scalar_one()
    assert row.amount_pence == 14900
    assert row.status == "paid"
    assert row.tenant_id == tenant.id


@pytest.mark.asyncio
async def test_stripe_invalid_signature_returns_400(client, monkeypatch):
    class FakeAdapter:
        async def verify_webhook(self, payload, sig):
            raise ValueError("invalid signature")

    monkeypatch.setattr("app.adapters.get_payment_adapter", lambda: FakeAdapter())

    res = await client.post(
        "/api/v1/webhooks/stripe",
        content=b"{}",
        headers={"stripe-signature": "bogus"},
    )
    assert res.status_code == 400
