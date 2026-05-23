"""Industry add-on entitlement and status API."""

from __future__ import annotations

import uuid

import pytest

from app.modules.addons.common.constants import FEATURE_INDUSTRY_BOOKING
from app.modules.addons.common.service import grant_addon


async def _register(client) -> str:
    email = f"addon-{uuid.uuid4().hex[:8]}@example.com"
    res = await client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "TestPass123",
            "full_name": "Addon Tester",
            "business_name": f"Salon Co {uuid.uuid4().hex[:6]}",
            "business_type": "salon",
            "postcode": "SW1A 1AA",
        },
    )
    assert res.status_code == 201
    return res.json()["access_token"]


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_addon_status_without_entitlement(client):
    token = await _register(client)
    r = await client.get("/api/v1/addons/status", headers=_auth(token))
    assert r.status_code == 200
    data = r.json()
    assert data["industry_booking"] is False
    assert data["vertical"] == "salon"


@pytest.mark.asyncio
async def test_addon_status_after_grant(client, db_session):
    token = await _register(client)
    headers = _auth(token)
    tenant = await client.get("/api/v1/tenants/me", headers=headers)
    tenant_id = uuid.UUID(tenant.json()["id"])
    await grant_addon(db_session, tenant_id, FEATURE_INDUSTRY_BOOKING)
    r = await client.get("/api/v1/addons/status", headers=headers)
    assert r.status_code == 200
    assert r.json()["industry_booking"] is True
