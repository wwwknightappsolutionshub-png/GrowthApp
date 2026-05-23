"""Accounting add-on entitlement and gated features."""
from __future__ import annotations

import uuid
from datetime import date

import pytest


async def _register(client) -> str:
    email = f"acct-{uuid.uuid4().hex[:8]}@example.com"
    res = await client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "TestPass123",
            "full_name": "Acct Tester",
            "business_name": f"Acct Co {uuid.uuid4().hex[:6]}",
            "business_type": "plumber",
            "postcode": "SW1A 1AA",
        },
    )
    assert res.status_code == 201
    return res.json()["access_token"]


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_accounting_status_and_expense_gate(client, db_session):
    from app.modules.accounting.service import grant_addon
    token = await _register(client)
    headers = _auth(token)

    status = await client.get("/api/v1/accounting/status", headers=headers)
    assert status.status_code == 200
    assert status.json()["has_accounting"] is False

    blocked = await client.post(
        "/api/v1/accounting/expenses",
        headers=headers,
        json={
            "description": "Materials",
            "amount_pence": 5000,
            "expense_date": date.today().isoformat(),
        },
    )
    assert blocked.status_code == 403

    tenant = await client.get("/api/v1/tenants/me", headers=headers)
    tenant_id = uuid.UUID(tenant.json()["id"])
    await grant_addon(db_session, tenant_id)

    ok = await client.post(
        "/api/v1/accounting/expenses",
        headers=headers,
        json={
            "description": "Materials",
            "amount_pence": 5000,
            "expense_date": date.today().isoformat(),
        },
    )
    assert ok.status_code == 201, ok.text

    status2 = await client.get("/api/v1/accounting/status", headers=headers)
    assert status2.json()["has_accounting"] is True
