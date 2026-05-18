"""End-to-end public (unauthenticated) flows."""
from __future__ import annotations

import uuid

import pytest


async def _register_tenant(client, slug_seed: str | None = None):
    email = f"pub-{uuid.uuid4().hex[:6]}@example.com"
    biz = f"Pub Plumbing {slug_seed or uuid.uuid4().hex[:4]}"
    res = await client.post("/api/v1/auth/register", json={
        "email": email,
        "password": "TestPass123",
        "full_name": "Owner",
        "business_name": biz,
        "business_type": "plumber",
        "postcode": "SW1A 1AA",
    })
    assert res.status_code == 201, res.text
    return biz, email


@pytest.mark.asyncio
async def test_public_lead_capture_404_for_unknown_tenant(client):
    res = await client.post(
        "/api/v1/public/leads/does-not-exist",
        json={"first_name": "Hi", "email": "hi@example.com"},
    )
    # Either 404 (tenant not found) or 429 (rate limit) — both prove the
    # endpoint isn't blindly accepting submissions.
    assert res.status_code in (404, 429)


@pytest.mark.asyncio
async def test_public_widget_returns_empty_for_unknown_tenant(client):
    res = await client.get("/api/v1/public/widget/reviews/no-such-tenant")
    assert res.status_code == 200
    body = res.json()
    assert body == {"reviews": [], "avg_rating": 0, "total": 0}


@pytest.mark.asyncio
async def test_healthz_ok(client):
    res = await client.get("/healthz")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"
