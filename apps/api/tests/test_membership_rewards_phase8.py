"""Phase 8 — landing aliases and public embed fields."""

from __future__ import annotations

import uuid

import pytest
from httpx import AsyncClient


async def _register(client: AsyncClient) -> tuple[str, uuid.UUID, str]:
    email = f"mr8-{uuid.uuid4().hex[:8]}@example.com"
    slug = f"mr8-{uuid.uuid4().hex[:6]}"
    res = await client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "TestPass123",
            "full_name": "MR8 Tester",
            "business_name": f"MR8 Co {slug}",
            "business_type": "salon",
            "postcode": "SW1A 1AA",
        },
    )
    assert res.status_code == 201
    token = res.json()["access_token"]
    tenant = await client.get("/api/v1/tenants/me", headers={"Authorization": f"Bearer {token}"})
    return token, uuid.UUID(tenant.json()["id"]), tenant.json()["slug"]


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_public_loyalty_alias_matches_memberships(client: AsyncClient, db_session):
    from app.modules.membership_rewards.models import MrMembershipPlan
    from app.modules.membership_rewards.service import grant_addon, publish_landing

    token, tenant_id, slug = await _register(client)
    await grant_addon(db_session, tenant_id)

    db_session.add(
        MrMembershipPlan(
            tenant_id=tenant_id,
            name="Basic",
            billing_cycle="monthly",
            price_pence=1999,
            is_active=True,
        )
    )
    await db_session.commit()
    await publish_landing(db_session, tenant_id)

    memberships = await client.get(f"/api/v1/public/memberships/{slug}")
    loyalty = await client.get(f"/api/v1/public/loyalty/{slug}")
    assert memberships.status_code == 200
    assert loyalty.status_code == 200
    assert loyalty.json()["title"] == memberships.json()["title"]
    assert loyalty.json()["loyalty_url"].endswith(f"/p/{slug}/loyalty")
    assert loyalty.json()["rewards_portal_url"].endswith(f"/rewards/{slug}")


@pytest.mark.asyncio
async def test_booking_links_include_rewards_portal(client: AsyncClient, db_session):
    from app.modules.membership_rewards.service import grant_addon

    token, tenant_id, slug = await _register(client)
    headers = _auth(token)
    await grant_addon(db_session, tenant_id)

    links = await client.get("/api/v1/bookings/links", headers=headers)
    assert links.status_code == 200
    body = links.json()
    assert body["rewards_portal_url"].endswith(f"/rewards/{slug}")
    assert body["rewards_portal_label"] == "Customer rewards wallet"
