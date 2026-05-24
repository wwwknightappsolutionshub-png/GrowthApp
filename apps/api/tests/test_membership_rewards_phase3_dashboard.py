"""Phase 3 — tenant dashboard analytics and customer list APIs."""

from __future__ import annotations

import uuid

import pytest


async def _register(client) -> tuple[str, uuid.UUID]:
    email = f"mr3a-{uuid.uuid4().hex[:8]}@example.com"
    res = await client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "TestPass123",
            "full_name": "MR3A Tester",
            "business_name": f"MR3A Co {uuid.uuid4().hex[:6]}",
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
async def test_analytics_and_loyalty_customers(client, db_session):
    from app.modules.crm.models import Customer
    from app.modules.membership_rewards.engines.earning_engine import earn_points
    from app.modules.membership_rewards.service import grant_addon

    token, tenant_id = await _register(client)
    headers = _auth(token)
    await grant_addon(db_session, tenant_id)

    customer_id = uuid.uuid4()
    db_session.add(
        Customer(
            id=customer_id,
            tenant_id=tenant_id,
            first_name="Analytics",
            last_name="Member",
            email="analytics-member@test.com",
        )
    )
    await db_session.commit()

    await earn_points(
        db_session,
        tenant_id,
        customer_id,
        300,
        source="adjustment",
        description="analytics test",
    )

    analytics = await client.get("/api/v1/membership-rewards/analytics", headers=headers)
    assert analytics.status_code == 200, analytics.text
    body = analytics.json()
    assert body["members_total"] >= 1
    assert body["points_by_source"].get("adjustment", 0) >= 300
    assert len(body["top_customers"]) >= 1

    customers = await client.get(
        "/api/v1/membership-rewards/loyalty/customers",
        headers=headers,
        params={"search": "Analytics"},
    )
    assert customers.status_code == 200
    listed = customers.json()
    assert listed["total"] >= 1
    assert any(c["customer_id"] == str(customer_id) for c in listed["items"])

    redemptions = await client.get("/api/v1/membership-rewards/redemptions", headers=headers)
    assert redemptions.status_code == 200
    assert "items" in redemptions.json()
