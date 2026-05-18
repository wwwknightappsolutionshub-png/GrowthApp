"""Per-route rate limits on the auth endpoints."""
from __future__ import annotations

import uuid

import pytest

from app.core.middleware import limiter

pytestmark = pytest.mark.ratelimited


@pytest.mark.asyncio
async def test_login_rate_limited(client):
    """Login is capped at 10/minute. The 11th hit should be 429."""
    # Burn through the bucket. Bad credentials count toward the limit too.
    statuses = []
    for _ in range(12):
        res = await client.post(
            "/api/v1/auth/login",
            json={"email": "noone@example.com", "password": "Whatever123"},
        )
        statuses.append(res.status_code)
    assert 429 in statuses, f"expected at least one 429, saw {statuses}"


@pytest.mark.asyncio
async def test_forgot_password_rate_limited(client):
    """Forgot-password is much stricter: 3/minute."""
    statuses = []
    for _ in range(5):
        res = await client.post(
            "/api/v1/auth/forgot-password",
            json={"email": f"u-{uuid.uuid4().hex[:6]}@example.com"},
        )
        statuses.append(res.status_code)
    assert 429 in statuses, f"expected at least one 429, saw {statuses}"


@pytest.mark.asyncio
async def test_public_lead_rate_limited(client):
    """Public lead capture: 10/min/IP — the 11th should 429."""
    statuses = []
    for _ in range(12):
        res = await client.post(
            "/api/v1/public/leads/some-tenant",
            json={"first_name": "X", "email": "x@y.com"},
        )
        statuses.append(res.status_code)
    assert 429 in statuses
