"""GDPR endpoints are owner-only and enqueue background jobs."""
from __future__ import annotations

import uuid

import pytest


@pytest.mark.asyncio
async def test_gdpr_export_requires_auth(client):
    res = await client.post("/api/v1/gdpr/export")
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_gdpr_export_persists_request(client, db_session, monkeypatch):
    """Authenticated owner can request an export; a pending row is recorded."""
    from app.modules.gdpr.models import GdprRequest
    from sqlalchemy import select

    # Stub the queue so we don't need Redis in tests.
    enqueued: list[tuple[str, dict]] = []

    async def fake_enqueue(name, **kwargs):
        enqueued.append((name, kwargs))

    monkeypatch.setattr("app.modules.gdpr.router.enqueue", fake_enqueue)

    # Register a fresh owner.
    email = f"gdpr-{uuid.uuid4().hex[:6]}@example.com"
    reg = await client.post("/api/v1/auth/register", json={
        "email": email,
        "password": "TestPass123",
        "full_name": "GDPR Owner",
        "business_name": "GDPR Co",
        "business_type": "plumber",
        "postcode": "SW1A 1AA",
    })
    assert reg.status_code == 201
    token = reg.json()["access_token"]

    res = await client.post(
        "/api/v1/gdpr/export",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 202

    rows = (await db_session.execute(select(GdprRequest))).scalars().all()
    assert any(r.type == "export" and r.status == "pending" for r in rows)
    assert any(name == "gdpr_export" for name, _ in enqueued)


@pytest.mark.asyncio
async def test_gdpr_erasure_requires_known_customer(client, monkeypatch):
    async def fake_enqueue(name, **kwargs):
        pass

    monkeypatch.setattr("app.modules.gdpr.router.enqueue", fake_enqueue)

    email = f"gdpr-{uuid.uuid4().hex[:6]}@example.com"
    reg = await client.post("/api/v1/auth/register", json={
        "email": email,
        "password": "TestPass123",
        "full_name": "GDPR Owner",
        "business_name": "GDPR Erase Co",
        "business_type": "plumber",
        "postcode": "SW1A 1AA",
    })
    token = reg.json()["access_token"]

    res = await client.post(
        "/api/v1/gdpr/erasure",
        json={"customer_id": str(uuid.uuid4())},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 404
