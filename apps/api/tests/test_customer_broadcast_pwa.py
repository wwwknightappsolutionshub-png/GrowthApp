"""Customer broadcast + PWA install reminder tests."""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import select

from app.modules.crm.models import Customer
from app.modules.membership_rewards.models import MrCustomerLoyalty, MrPwaInstallReminder
from app.modules.membership_rewards.services.customer_broadcast_service import count_broadcast_recipients
from app.modules.membership_rewards.services.pwa_install_reminders import sweep_pwa_install_reminders


async def _register(client) -> tuple[str, uuid.UUID]:
    email = f"bc-{uuid.uuid4().hex[:8]}@example.com"
    res = await client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "TestPass123",
            "full_name": "Broadcast Tester",
            "business_name": f"BC Co {uuid.uuid4().hex[:6]}",
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


@pytest.mark.asyncio
async def test_customer_broadcast_requires_enrolled_customers(client, db_session, monkeypatch):
    from app.modules.membership_rewards.service import grant_addon
    from app.core.config import settings

    monkeypatch.setattr(settings, "VAPID_PRIVATE_KEY", "test-key")
    monkeypatch.setattr(settings, "VAPID_PUBLIC_KEY", "test-pub")
    monkeypatch.setattr(settings, "VAPID_SUBJECT", "mailto:test@example.com")

    token, tenant_id = await _register(client)
    await grant_addon(db_session, tenant_id)

    blocked = await client.post(
        "/api/v1/membership-rewards/customers/broadcast",
        headers=_auth(token),
        json={"title": "Hello", "body": "World", "send_push": True},
    )
    assert blocked.status_code == 400
    assert "enrolled" in blocked.json()["detail"].lower()


@pytest.mark.asyncio
async def test_count_broadcast_recipients_uses_loyalty_table(db_session, client):
    from app.modules.membership_rewards.service import grant_addon

    _, tenant_id = await _register(client)
    await grant_addon(db_session, tenant_id)

    customer = Customer(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        first_name="Pat",
        email=f"pat-{uuid.uuid4().hex[:6]}@example.com",
    )
    db_session.add(customer)
    db_session.add(
        MrCustomerLoyalty(tenant_id=tenant_id, customer_id=customer.id, points_balance=0, points_lifetime=0)
    )
    await db_session.commit()

    counts = await count_broadcast_recipients(db_session, tenant_id)
    assert counts["customers"] == 1


@pytest.mark.asyncio
async def test_pwa_reminder_sweep_sends_30m_email(db_session, monkeypatch):
    from app.modules.auth.models import User
    from app.modules.tenants.models import Tenant, TenantMember

    tenant_id = uuid.uuid4()
    user_id = uuid.uuid4()
    db_session.add(
        Tenant(
            id=tenant_id,
            slug=f"t-{uuid.uuid4().hex[:6]}",
            name="Test Biz",
            business_type="plumber",
            postcode="SW1A 1AA",
        )
    )
    db_session.add(
        User(
            id=user_id,
            email=f"owner-{uuid.uuid4().hex[:6]}@example.com",
            full_name="Owner",
            password_hash="x",
        )
    )
    db_session.add(TenantMember(id=uuid.uuid4(), tenant_id=tenant_id, user_id=user_id, role="owner"))
    registered = datetime.now(timezone.utc) - timedelta(minutes=35)
    db_session.add(
        MrPwaInstallReminder(
            id=uuid.uuid4(),
            audience="tenant",
            tenant_id=tenant_id,
            user_id=user_id,
            registered_at=registered,
        )
    )
    await db_session.commit()

    sent = []

    class FakeAdapter:
        async def send(self, msg):
            sent.append(msg.to)

    from app.adapters.email import get_email_adapter

    monkeypatch.setattr(
        "app.modules.membership_rewards.services.pwa_install_reminders.get_email_adapter",
        lambda: FakeAdapter(),
    )

    count = await sweep_pwa_install_reminders(db_session)
    assert count == 1
    assert len(sent) == 1

    row = (await db_session.execute(select(MrPwaInstallReminder))).scalar_one()
    assert row.reminder_30m_sent_at is not None
