"""Salon + garage industry add-ons integration tests."""

from __future__ import annotations

import uuid
from datetime import date

import pytest

from app.modules.addons.common.constants import (
    FEATURE_INDUSTRY_BILLING,
    FEATURE_INDUSTRY_BOOKING,
    FEATURE_INDUSTRY_CRM,
)
from app.modules.addons.common.service import grant_addon
from app.modules.addons.common.vertical import set_tenant_vertical
from app.modules.addons.common.constants import Vertical


async def _register(client, business_type: str) -> tuple[str, str]:
    email = f"ind-{uuid.uuid4().hex[:8]}@example.com"
    res = await client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "TestPass123",
            "full_name": "Industry Tester",
            "business_name": f"Biz {uuid.uuid4().hex[:6]}",
            "business_type": business_type,
            "postcode": "SW1A 1AA",
        },
    )
    assert res.status_code == 201
    token = res.json()["access_token"]
    me = await client.get("/api/v1/tenants/me", headers={"Authorization": f"Bearer {token}"})
    return token, me.json()["id"]


def _h(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_industry_booking_gated_then_salon_gap_fill(client, db_session):
    token, tenant_id = await _register(client, "salon")
    headers = _h(token)
    blocked = await client.get(
        "/api/v1/addons/booking/gap-fill",
        headers=headers,
        params={"target_date": date.today().isoformat()},
    )
    assert blocked.status_code == 403
    await grant_addon(db_session, uuid.UUID(tenant_id), FEATURE_INDUSTRY_BOOKING)
    await set_tenant_vertical(db_session, uuid.UUID(tenant_id), Vertical.SALON)
    ok = await client.get(
        "/api/v1/addons/booking/gap-fill",
        headers=headers,
        params={"target_date": date.today().isoformat()},
    )
    assert ok.status_code == 200
    assert isinstance(ok.json(), list)


@pytest.mark.asyncio
async def test_salon_crm_profile_and_segments(client, db_session):
    token, tenant_id = await _register(client, "beautician")
    headers = _h(token)
    await grant_addon(db_session, uuid.UUID(tenant_id), FEATURE_INDUSTRY_CRM)
    await set_tenant_vertical(db_session, uuid.UUID(tenant_id), Vertical.SALON)
    cust = await client.post(
        "/api/v1/crm/customers",
        headers=headers,
        json={"first_name": "Jane", "last_name": "Doe", "email": f"j{uuid.uuid4().hex[:6]}@t.com"},
    )
    assert cust.status_code in (200, 201), cust.text
    cid = cust.json()["id"]
    prof = await client.put(
        "/api/v1/addons/crm/salon/profile",
        headers=headers,
        json={
            "customer_id": cid,
            "color_formula": "7/0 + 20vol",
            "allergies": "PPD",
            "segment_tags": ["vip", "color"],
        },
    )
    assert prof.status_code == 200
    segs = await client.get("/api/v1/addons/crm/salon/segments", headers=headers)
    assert segs.status_code == 200


@pytest.mark.asyncio
async def test_garage_parts_and_vehicle(client, db_session):
    token, tenant_id = await _register(client, "garage")
    headers = _h(token)
    await grant_addon(db_session, uuid.UUID(tenant_id), FEATURE_INDUSTRY_BOOKING)
    await grant_addon(db_session, uuid.UUID(tenant_id), FEATURE_INDUSTRY_CRM)
    await set_tenant_vertical(db_session, uuid.UUID(tenant_id), Vertical.GARAGE)
    part = await client.post(
        "/api/v1/addons/booking/parts",
        headers=headers,
        json={
            "sku": "OIL-5W30",
            "name": "Engine oil 5W30",
            "quantity_on_hand": 10,
            "unit_cost_pence": 800,
        },
    )
    assert part.status_code == 200
    cust = await client.post(
        "/api/v1/crm/customers",
        headers=headers,
        json={"first_name": "Bob", "last_name": "Driver", "email": f"b{uuid.uuid4().hex[:6]}@t.com"},
    )
    cid = cust.json()["id"]
    veh = await client.post(
        "/api/v1/addons/booking/vehicles",
        headers=headers,
        json={
            "customer_id": cid,
            "vin": "WVWZZZ3CZWE123456",
            "make": "VW",
            "model": "Golf",
            "year": 2018,
        },
    )
    assert veh.status_code == 200
    vid = veh.json()["id"]
    hist = await client.get(f"/api/v1/addons/crm/garage/vehicles/{vid}/history", headers=headers)
    assert hist.status_code == 200


@pytest.mark.asyncio
async def test_garage_billing_warranty_requires_addon(client, db_session):
    token, tenant_id = await _register(client, "mechanic")
    headers = _h(token)
    await set_tenant_vertical(db_session, uuid.UUID(tenant_id), Vertical.GARAGE)
    blocked = await client.get("/api/v1/addons/billing/templates", headers=headers)
    assert blocked.status_code == 403
    await grant_addon(db_session, uuid.UUID(tenant_id), FEATURE_INDUSTRY_BILLING)
    ok = await client.get("/api/v1/addons/billing/templates", headers=headers)
    assert ok.status_code == 200
