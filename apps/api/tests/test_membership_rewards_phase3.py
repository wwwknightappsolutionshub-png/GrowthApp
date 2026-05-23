"""Phase 3 — subscriptions, points hooks, dashboard."""
from __future__ import annotations

import uuid
from datetime import date

import pytest


async def _register(client) -> tuple[str, uuid.UUID]:
    email = f"mr3-{uuid.uuid4().hex[:8]}@example.com"
    res = await client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "TestPass123",
            "full_name": "MR3 Tester",
            "business_name": f"MR3 Co {uuid.uuid4().hex[:6]}",
            "business_type": "plumber",
            "postcode": "SW1A 1AA",
        },
    )
    assert res.status_code == 201
    token = res.json()["access_token"]
    tenant = await client.get("/api/v1/tenants/me", headers={"Authorization": f"Bearer {token}"})
    return token, uuid.UUID(tenant.json()["id"])


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_subscription_and_booking_points(client, db_session):
    from app.modules.booking.models import Booking
    from app.modules.membership_rewards.hooks import on_booking_completed
    from app.modules.membership_rewards.service import grant_addon, list_ledger

    token, tenant_id = await _register(client)
    headers = _auth(token)
    await grant_addon(db_session, tenant_id)

    cust = await client.post(
        "/api/v1/crm/customers",
        headers=headers,
        json={"first_name": "Pat", "last_name": "Lee", "email": "pat@example.com"},
    )
    assert cust.status_code == 201, cust.text
    customer_id = uuid.UUID(cust.json()["id"])

    plan = await client.post(
        "/api/v1/membership-rewards/plans",
        headers=headers,
        json={"name": "Monthly", "billing_cycle": "monthly", "price_pence": 2999},
    )
    assert plan.status_code == 200
    plan_id = uuid.UUID(plan.json()["id"])

    sub = await client.post(
        "/api/v1/membership-rewards/subscriptions",
        headers=headers,
        json={"customer_id": str(customer_id), "plan_id": str(plan_id)},
    )
    assert sub.status_code == 200, sub.text
    assert sub.json()["status"] == "active"

    ledger = await list_ledger(db_session, tenant_id, customer_id)
    assert any(e.source == "membership" for e in ledger)

    from datetime import time

    booking = Booking(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        customer_id=customer_id,
        customer_name="Pat Lee",
        booking_date=date.today(),
        start_time=time(10, 0),
        status="completed",
    )
    db_session.add(booking)
    await db_session.commit()

    await on_booking_completed(db_session, tenant_id=tenant_id, booking=booking)
    ledger2 = await list_ledger(db_session, tenant_id, customer_id)
    assert any(e.source == "booking" for e in ledger2)

    dash = await client.get("/api/v1/membership-rewards/dashboard", headers=headers)
    assert dash.status_code == 200
    assert dash.json()["active_subscriptions"] >= 1


@pytest.mark.asyncio
async def test_cancel_subscription(client, db_session):
    from app.modules.membership_rewards.service import grant_addon

    token, tenant_id = await _register(client)
    headers = _auth(token)
    await grant_addon(db_session, tenant_id)

    cust = await client.post(
        "/api/v1/crm/customers",
        headers=headers,
        json={"first_name": "Sam", "last_name": "Fox", "email": "sam@example.com"},
    )
    customer_id = uuid.UUID(cust.json()["id"])
    plan = await client.post(
        "/api/v1/membership-rewards/plans",
        headers=headers,
        json={"name": "Basic", "billing_cycle": "monthly", "price_pence": 1000},
    )
    plan_id = uuid.UUID(plan.json()["id"])
    sub = await client.post(
        "/api/v1/membership-rewards/subscriptions",
        headers=headers,
        json={"customer_id": str(customer_id), "plan_id": str(plan_id)},
    )
    sub_id = sub.json()["id"]
    canceled = await client.post(
        f"/api/v1/membership-rewards/subscriptions/{sub_id}/cancel",
        headers=headers,
    )
    assert canceled.status_code == 200
    assert canceled.json()["status"] == "canceled"
