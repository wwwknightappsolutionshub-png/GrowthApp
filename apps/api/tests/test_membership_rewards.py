"""Membership & Rewards — trial, entitlement, points ledger, public landing."""
from __future__ import annotations

import uuid

import pytest


async def _register(client) -> str:
    email = f"mr-{uuid.uuid4().hex[:8]}@example.com"
    res = await client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "TestPass123",
            "full_name": "MR Tester",
            "business_name": f"MR Co {uuid.uuid4().hex[:6]}",
            "business_type": "plumber",
            "postcode": "SW1A 1AA",
        },
    )
    assert res.status_code == 201
    return res.json()["access_token"]


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_signup_starts_membership_trial(client, db_session):
    token = await _register(client)
    headers = _auth(token)

    status = await client.get("/api/v1/membership-rewards/status", headers=headers)
    assert status.status_code == 200
    body = status.json()
    assert body["has_membership_rewards"] is True
    assert body["trial_ends_at"] is not None


@pytest.mark.asyncio
async def test_plans_and_points_gated_then_work(client, db_session):
    from app.modules.membership_rewards.service import grant_addon

    token = await _register(client)
    headers = _auth(token)

    tenant = await client.get("/api/v1/tenants/me", headers=headers)
    tenant_id = uuid.UUID(tenant.json()["id"])

    # Revoke trial to test gate (simulate expired)
    from app.modules.accounting.models import TenantAddon
    from app.modules.membership_rewards.constants import FEATURE_MEMBERSHIP_REWARDS
    from sqlalchemy import select

    row = (
        await db_session.execute(
            select(TenantAddon).where(
                TenantAddon.tenant_id == tenant_id,
                TenantAddon.feature_code == FEATURE_MEMBERSHIP_REWARDS,
            )
        )
    ).scalar_one()
    row.status = "canceled"
    await db_session.commit()

    blocked = await client.get("/api/v1/membership-rewards/plans", headers=headers)
    assert blocked.status_code == 403

    await grant_addon(db_session, tenant_id)

    plan_res = await client.post(
        "/api/v1/membership-rewards/plans",
        headers=headers,
        json={
            "name": "Gold Monthly",
            "billing_cycle": "monthly",
            "price_pence": 4999,
        },
    )
    assert plan_res.status_code == 200, plan_res.text

    tiers = await client.get("/api/v1/membership-rewards/tiers", headers=headers)
    assert tiers.status_code == 200
    assert len(tiers.json()["items"]) >= 4


@pytest.mark.asyncio
async def test_public_memberships_requires_publish(client, db_session):
    from app.modules.membership_rewards.service import grant_addon
    from app.modules.tenants.models import Tenant
    from sqlalchemy import select

    token = await _register(client)
    headers = _auth(token)
    tenant = await client.get("/api/v1/tenants/me", headers=headers)
    tenant_id = uuid.UUID(tenant.json()["id"])
    slug = tenant.json()["slug"]

    unpublished = await client.get(f"/api/v1/public/memberships/{slug}")
    assert unpublished.status_code == 404

    await grant_addon(db_session, tenant_id)
    plan_res = await client.post(
        "/api/v1/membership-rewards/plans",
        headers=headers,
        json={"name": "Public Plan", "billing_cycle": "monthly", "price_pence": 2500},
    )
    assert plan_res.status_code == 200

    pub = await client.get(f"/api/v1/public/memberships/{slug}")
    assert pub.status_code == 200
    assert pub.json()["tenant_slug"] == slug
