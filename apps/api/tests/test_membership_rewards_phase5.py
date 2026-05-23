"""Phase 5 — landing auto-generation and publish on first plan."""
from __future__ import annotations

import uuid

import pytest


@pytest.mark.asyncio
async def test_create_plan_auto_publishes_landing(client, db_session):
    from app.modules.membership_rewards.models import MrLandingConfig, MrTenantSettings
    from app.modules.membership_rewards.service import grant_addon

    email = f"mr5-{uuid.uuid4().hex[:8]}@example.com"
    res = await client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "TestPass123",
            "full_name": "MR5 Tester",
            "business_name": f"MR5 Co {uuid.uuid4().hex[:6]}",
            "business_type": "plumber",
            "postcode": "SW1A 1AA",
        },
    )
    assert res.status_code == 201
    token = res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    tenant = await client.get("/api/v1/tenants/me", headers=headers)
    tenant_id = uuid.UUID(tenant.json()["id"])
    slug = tenant.json()["slug"]

    await grant_addon(db_session, tenant_id)

    pub_before = await client.get(f"/api/v1/public/memberships/{slug}")
    assert pub_before.status_code == 404

    plan = await client.post(
        "/api/v1/membership-rewards/plans",
        headers=headers,
        json={"name": "Starter", "billing_cycle": "monthly", "price_pence": 1999},
    )
    assert plan.status_code == 200, plan.text

    pub_after = await client.get(f"/api/v1/public/memberships/{slug}")
    assert pub_after.status_code == 200
    body = pub_after.json()
    assert body["tenant_slug"] == slug
    assert len(body["plans"]) == 1
    assert "Starter" in body["hero"]["headline"] or "MR5" in body["title"]

    cfg = await db_session.get(MrLandingConfig, tenant_id)
    settings = await db_session.get(MrTenantSettings, tenant_id)
    assert cfg.published is True
    assert settings.landing_published is True


@pytest.mark.asyncio
async def test_regenerate_landing_and_interest_lead(client, db_session):
    from app.modules.membership_rewards.service import grant_addon

    email = f"mr5b-{uuid.uuid4().hex[:8]}@example.com"
    res = await client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "TestPass123",
            "full_name": "Lead Tester",
            "business_name": f"Lead Co {uuid.uuid4().hex[:6]}",
            "business_type": "plumber",
            "postcode": "E1 6AN",
        },
    )
    token = res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    tenant = await client.get("/api/v1/tenants/me", headers=headers)
    tenant_id = uuid.UUID(tenant.json()["id"])
    slug = tenant.json()["slug"]
    await grant_addon(db_session, tenant_id)

    await client.post(
        "/api/v1/membership-rewards/plans",
        headers=headers,
        json={"name": "Gold", "billing_cycle": "yearly", "price_pence": 9999},
    )

    regen = await client.post("/api/v1/membership-rewards/landing/regenerate", headers=headers)
    assert regen.status_code == 200
    assert regen.json()["auto_generated"] is True

    interest = await client.post(
        f"/api/v1/public/memberships/{slug}/interest",
        json={
            "first_name": "Alex",
            "email": "alex@example.com",
            "message": "I want to join",
        },
    )
    assert interest.status_code == 201
