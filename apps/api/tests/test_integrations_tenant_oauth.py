"""Integration layer tests: tenant Google OAuth + social webhooks."""
from __future__ import annotations

import hmac
import uuid

import orjson
import pytest
from sqlalchemy import select

from app.core.config import settings
from app.modules.integrations.auth.social_auth import generate_api_key, generate_api_secret, sign_payload
from app.modules.integrations.models import TenantSocialChannel, TenantSocialWebhookLog
from app.modules.integrations.social import service as social_service
from app.modules.integrations.token_crypto import encrypt_secret
from app.modules.integrations.validators.social_payload import SocialWebhookPayload
from app.modules.messaging.models import Conversation, Message


async def _register(client) -> tuple[str, uuid.UUID]:
    email = f"int-{uuid.uuid4().hex[:8]}@example.com"
    res = await client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "TestPass123",
            "full_name": "Integration Tester",
            "business_name": f"Int Co {uuid.uuid4().hex[:6]}",
            "business_type": "plumber",
            "postcode": "SW1A 1AA",
        },
    )
    assert res.status_code == 201
    token = res.json()["access_token"]
    tenant = await client.get("/api/v1/tenants/me", headers={"Authorization": f"Bearer {token}"})
    return token, uuid.UUID(tenant.json()["id"])


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
async def tenant_with_social_channel(db_session, client, monkeypatch):
    monkeypatch.setattr(settings, "INTEGRATIONS_TOKEN_ENCRYPTION_KEY", "test-encryption-key")
    token, tenant_id = await _register(client)
    api_key = generate_api_key()
    api_secret = generate_api_secret()
    channel_id = uuid.uuid4()
    row = TenantSocialChannel(
        id=channel_id,
        tenant_id=tenant_id,
        channel_type="facebook",
        api_key=api_key,
        api_secret_encrypted=encrypt_secret(api_secret),
        webhook_url=f"http://test/api/v1/integrations/webhooks/social/{channel_id}?key={api_key}",
        zapier_integration_key="zap-test",
        make_integration_key="make-test",
        status="pending",
    )
    db_session.add(row)
    await db_session.commit()
    await db_session.refresh(row)
    return row, api_secret, token


def test_social_payload_normalizes_event_type():
    p = SocialWebhookPayload.model_validate(
        {"event_type": "post-status", "platform": "facebook", "message": "ok"}
    )
    assert p.event_type == "post_status"


def test_sign_payload_roundtrip():
    secret = "test-secret"
    body = b'{"event_type":"message"}'
    sig = sign_payload(secret, body)
    assert hmac.compare_digest(sig, sign_payload(secret, body))


@pytest.mark.asyncio
async def test_provision_social_channel(db_session, client, monkeypatch):
    monkeypatch.setattr(settings, "INTEGRATIONS_TOKEN_ENCRYPTION_KEY", "test-encryption-key")
    _, tenant_id = await _register(client)
    row = await social_service.provision_channel(db_session, tenant_id, "instagram")
    assert row.channel_type == "instagram"
    assert row.api_key
    assert "/integrations/webhooks/social/" in row.webhook_url


@pytest.mark.asyncio
async def test_register_google_credentials(client, monkeypatch):
    monkeypatch.setattr(settings, "INTEGRATIONS_TOKEN_ENCRYPTION_KEY", "test-encryption-key")
    token, _ = await _register(client)
    res = await client.post(
        "/api/v1/integrations/google/register-credentials",
        headers=_auth(token),
        json={
            "google_client_id": "123456789012-abcdef.apps.googleusercontent.com",
            "google_client_secret": "GOCSPX-test-secret-value",
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert data["registered"] is True
    assert data["redirect_uri"].endswith("/api/v1/integrations/google/oauth-callback")


@pytest.mark.asyncio
async def test_social_webhook_creates_inbox_message(client, db_session, tenant_with_social_channel, monkeypatch):
    monkeypatch.setattr(settings, "INTEGRATIONS_TOKEN_ENCRYPTION_KEY", "test-encryption-key")
    channel, api_secret, _token = tenant_with_social_channel
    payload = {
        "event_type": "message",
        "platform": "facebook",
        "sender_name": "Jane Doe",
        "sender_email": "jane@example.com",
        "message": "Hello from Facebook",
        "external_id": "fb-msg-1",
    }
    body = orjson.dumps(payload)
    signature = sign_payload(api_secret, body)

    res = await client.post(
        f"/api/v1/integrations/webhooks/social/{channel.id}?key={channel.api_key}",
        content=body,
        headers={"Content-Type": "application/json", "X-CF-Signature": signature},
    )
    assert res.status_code == 200
    assert res.json()["ok"] is True

    msgs = (
        await db_session.execute(select(Message).where(Message.tenant_id == channel.tenant_id))
    ).scalars().all()
    assert len(msgs) >= 1
    assert msgs[0].body == "Hello from Facebook"

    convs = (
        await db_session.execute(select(Conversation).where(Conversation.tenant_id == channel.tenant_id))
    ).scalars().all()
    assert convs[0].channel == "facebook"

    logs = (
        await db_session.execute(
            select(TenantSocialWebhookLog).where(TenantSocialWebhookLog.tenant_id == channel.tenant_id)
        )
    ).scalars().all()
    assert logs[-1].status == "processed"


@pytest.mark.asyncio
async def test_social_webhook_rejects_bad_key(client, tenant_with_social_channel):
    channel, _, _ = tenant_with_social_channel
    res = await client.post(
        f"/api/v1/integrations/webhooks/social/{channel.id}?key=wrong-key",
        json={"event_type": "message", "platform": "facebook", "message": "hi"},
    )
    assert res.status_code == 400


@pytest.mark.asyncio
async def test_integrations_onboarding_save(client):
    token, _ = await _register(client)
    res = await client.post(
        "/api/v1/integrations/onboarding",
        headers=_auth(token),
        json={"skipped": True, "google_connected": False},
    )
    assert res.status_code == 200
    assert res.json()["skipped"] is True
