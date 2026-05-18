"""Super-admin endpoints — role gating + happy paths."""
from __future__ import annotations

import uuid

import pytest

from app.core.security import create_access_token, hash_password
from app.modules.auth.models import User


async def _make_superadmin(db_session) -> User:
    u = User(
        id=uuid.uuid4(),
        email=f"sa-{uuid.uuid4().hex[:6]}@customerflow.ai",
        password_hash=hash_password("Sup3rPass!"),
        full_name="Test Admin",
        is_superadmin=True,
        totp_backup_codes=[],
    )
    db_session.add(u)
    await db_session.commit()
    return u


@pytest.mark.asyncio
async def test_admin_endpoints_require_auth(client):
    res = await client.get("/api/v1/admin/stats")
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_admin_endpoints_reject_non_superadmin(client):
    """A regular tenant owner cannot access /admin/*."""
    reg = await client.post("/api/v1/auth/register", json={
        "email": f"owner-{uuid.uuid4().hex[:6]}@example.com",
        "password": "TestPass123",
        "full_name": "Plain Owner",
        "business_name": "Admin Gate Co",
        "business_type": "plumber",
        "postcode": "SW1A 1AA",
    })
    assert reg.status_code == 201
    token = reg.json()["access_token"]

    res = await client.get(
        "/api/v1/admin/stats",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 403


@pytest.mark.asyncio
async def test_admin_me_returns_identity(client, db_session):
    admin = await _make_superadmin(db_session)
    token = create_access_token(subject=admin.id, tenant_id=None, role=None)

    res = await client.get(
        "/api/v1/admin/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["email"] == admin.email
    assert body["is_superadmin"] is True


@pytest.mark.asyncio
async def test_admin_stats_returns_aggregate(client, db_session):
    admin = await _make_superadmin(db_session)
    token = create_access_token(subject=admin.id, tenant_id=None, role=None)

    res = await client.get(
        "/api/v1/admin/stats",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    body = res.json()
    for key in (
        "total_tenants", "active_tenants", "suspended_tenants",
        "total_users", "total_leads", "total_deals", "total_invoices",
        "paid_invoices_pence", "open_invoices_pence", "mrr_pence",
        "new_tenants_30d",
    ):
        assert key in body


@pytest.mark.asyncio
async def test_admin_suspend_and_reactivate_tenant(client, db_session):
    admin = await _make_superadmin(db_session)
    token = create_access_token(subject=admin.id, tenant_id=None, role=None)

    # Register a tenant via the public endpoint (creates Tenant + owner).
    reg = await client.post("/api/v1/auth/register", json={
        "email": f"susp-{uuid.uuid4().hex[:6]}@example.com",
        "password": "TestPass123",
        "full_name": "Susp Owner",
        "business_name": f"Susp Co {uuid.uuid4().hex[:4]}",
        "business_type": "plumber",
        "postcode": "SW1A 1AA",
    })
    assert reg.status_code == 201

    tenants_res = await client.get(
        "/api/v1/admin/tenants",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert tenants_res.status_code == 200
    rows = tenants_res.json()
    assert len(rows) >= 1
    tid = rows[0]["id"]
    assert rows[0]["is_active"] is True

    susp = await client.post(
        f"/api/v1/admin/tenants/{tid}/suspend",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert susp.status_code == 200
    assert susp.json()["is_active"] is False

    react = await client.post(
        f"/api/v1/admin/tenants/{tid}/reactivate",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert react.status_code == 200
    assert react.json()["is_active"] is True
