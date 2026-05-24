"""Wallet in-app notification tests."""
from __future__ import annotations

import uuid

import pytest

from app.modules.crm.models import Customer
from app.modules.membership_rewards.models import MrCustomerLoyalty, MrCustomerNotification
from app.modules.membership_rewards.services.customer_notification_service import (
    list_customer_notifications,
    notify_loyalty_customer,
    unread_count,
)


@pytest.mark.asyncio
async def test_notify_loyalty_customer_creates_in_app_row(db_session, client, monkeypatch):
    from app.core.config import settings
    from app.modules.membership_rewards.service import grant_addon

    monkeypatch.setattr(settings, "VAPID_PRIVATE_KEY", "")
    monkeypatch.setattr(settings, "VAPID_PUBLIC_KEY", "")

    email = f"wallet-notif-{uuid.uuid4().hex[:8]}@example.com"
    res = await client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "TestPass123",
            "full_name": "Wallet Tester",
            "business_name": f"Wallet Co {uuid.uuid4().hex[:6]}",
            "business_type": "plumber",
            "postcode": "SW1A 1AA",
        },
    )
    assert res.status_code == 201
    token = res.json()["access_token"]
    tenant = await client.get("/api/v1/tenants/me", headers={"Authorization": f"Bearer {token}"})
    tenant_id = uuid.UUID(tenant.json()["id"])
    await grant_addon(db_session, tenant_id)

    customer = Customer(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        first_name="Sam",
        email=f"sam-{uuid.uuid4().hex[:6]}@example.com",
    )
    db_session.add(customer)
    db_session.add(
        MrCustomerLoyalty(tenant_id=tenant_id, customer_id=customer.id, points_balance=100, points_lifetime=100)
    )
    await db_session.commit()

    result = await notify_loyalty_customer(
        db_session,
        tenant_id=tenant_id,
        customer_id=customer.id,
        title="Special offer",
        body="Double points this weekend.",
        path="rewards",
        kind="loyalty.broadcast",
        send_push=False,
    )
    assert result["notification_id"]

    count = await unread_count(db_session, tenant_id=tenant_id, customer_id=customer.id)
    assert count == 1

    rows, unread = await list_customer_notifications(
        db_session, tenant_id=tenant_id, customer_id=customer.id
    )
    assert unread == 1
    assert rows[0].title == "Special offer"
    assert rows[0].link == "rewards"


@pytest.mark.asyncio
async def test_portal_notifications_api(db_session, client, monkeypatch):
    from app.core.config import settings
    from app.core.security import create_access_token
    from app.modules.membership_rewards.service import grant_addon
    from app.modules.tenants.models import Tenant

    monkeypatch.setattr(settings, "VAPID_PRIVATE_KEY", "")

    email = f"portal-notif-{uuid.uuid4().hex[:8]}@example.com"
    res = await client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "TestPass123",
            "full_name": "Portal Tester",
            "business_name": f"Portal Co {uuid.uuid4().hex[:6]}",
            "business_type": "plumber",
            "postcode": "SW1A 1AA",
        },
    )
    token = res.json()["access_token"]
    tenant_id = uuid.UUID(
        (await client.get("/api/v1/tenants/me", headers={"Authorization": f"Bearer {token}"})).json()["id"]
    )
    await db_session.get(Tenant, tenant_id)
    await grant_addon(db_session, tenant_id)

    customer = Customer(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        first_name="Alex",
        email=f"alex-{uuid.uuid4().hex[:6]}@example.com",
    )
    db_session.add(customer)
    db_session.add(
        MrCustomerLoyalty(tenant_id=tenant_id, customer_id=customer.id, points_balance=50, points_lifetime=50)
    )
    db_session.add(
        MrCustomerNotification(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            customer_id=customer.id,
            kind="loyalty.system",
            title="Welcome",
            body="Thanks for joining.",
            link="dashboard",
        )
    )
    await db_session.commit()

    customer_token = create_access_token(
        subject=customer.id,
        tenant_id=tenant_id,
        role="customer",
    )
    headers = {"Authorization": f"Bearer {customer_token}"}

    listed = await client.get("/api/v1/loyalty-portal/notifications", headers=headers)
    assert listed.status_code == 200
    payload = listed.json()
    assert payload["unread"] == 1
    assert payload["items"][0]["title"] == "Welcome"

    notif_id = payload["items"][0]["id"]
    marked = await client.post(f"/api/v1/loyalty-portal/notifications/{notif_id}/read", headers=headers)
    assert marked.status_code == 200
    assert marked.json()["read_at"] is not None

    unread = await client.get("/api/v1/loyalty-portal/notifications/unread-count", headers=headers)
    assert unread.json()["unread"] == 0
