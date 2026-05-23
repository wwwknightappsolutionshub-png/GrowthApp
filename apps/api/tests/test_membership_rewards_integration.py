"""Phase 8 — end-to-end smoke: trial → plans → landing → public page → addons status."""

from __future__ import annotations

import uuid

import pytest


async def _register(client) -> tuple[str, str]:
    email = f"mrint-{uuid.uuid4().hex[:8]}@example.com"
    res = await client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "TestPass123",
            "full_name": "MR Int Tester",
            "business_name": f"MR Int {uuid.uuid4().hex[:6]}",
            "business_type": "plumber",
            "postcode": "SW1A 1AA",
        },
    )
    assert res.status_code == 201
    token = res.json()["access_token"]
    me = await client.get("/api/v1/tenants/me", headers={"Authorization": f"Bearer {token}"})
    return token, me.json()["slug"]


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_signup_trial_dashboard_and_addons_status(client):
    token, _ = await _register(client)
    headers = _auth(token)

    status = await client.get("/api/v1/membership-rewards/status", headers=headers)
    assert status.status_code == 200
    assert status.json()["has_membership_rewards"] is True
    assert status.json()["is_trial"] is True

    trial = await client.get("/api/v1/membership-rewards/trial", headers=headers)
    assert trial.status_code == 200
    assert trial.json()["on_trial"] is True

    dash = await client.get("/api/v1/membership-rewards/dashboard", headers=headers)
    assert dash.status_code == 200

    addons = await client.get("/api/v1/addons/status", headers=headers)
    assert addons.status_code == 200
    assert addons.json()["membership_rewards"] is True


@pytest.mark.asyncio
async def test_plan_publish_public_interest_flow(client, db_session):
    from app.modules.membership_rewards.service import grant_addon

    token, slug = await _register(client)
    headers = _auth(token)
    tenant = await client.get("/api/v1/tenants/me", headers=headers)
    tenant_id = uuid.UUID(tenant.json()["id"])

    await grant_addon(db_session, tenant_id)

    plan = await client.post(
        "/api/v1/membership-rewards/plans",
        headers=headers,
        json={"name": "Smoke Plan", "billing_cycle": "monthly", "price_pence": 1999},
    )
    assert plan.status_code == 200, plan.text

    pub = await client.post("/api/v1/membership-rewards/landing/publish", headers=headers)
    assert pub.status_code == 200, pub.text

    page = await client.get(f"/api/v1/public/memberships/{slug}")
    assert page.status_code == 200
    assert page.json()["tenant_slug"] == slug

    interest = await client.post(
        f"/api/v1/public/memberships/{slug}/interest",
        json={
            "first_name": "Alex",
            "last_name": "Visitor",
            "email": "alex@example.com",
            "phone": "07700900123",
            "message": "Interested in Smoke Plan",
        },
    )
    assert interest.status_code == 201, interest.text


@pytest.mark.asyncio
async def test_entitlement_blocks_when_revoked(client, db_session):
    from app.modules.membership_rewards import service as mr_service

    token, _ = await _register(client)
    headers = _auth(token)
    tenant = await client.get("/api/v1/tenants/me", headers=headers)
    tenant_id = uuid.UUID(tenant.json()["id"])

    await mr_service.revoke_addon(db_session, tenant_id)

    blocked = await client.get("/api/v1/membership-rewards/plans", headers=headers)
    assert blocked.status_code == 403

    status = await client.get("/api/v1/membership-rewards/status", headers=headers)
    assert status.json()["has_membership_rewards"] is False
