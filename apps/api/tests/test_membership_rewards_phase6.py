"""Phase 6 — staff QR scan API."""

from __future__ import annotations

import uuid

import pytest
from httpx import AsyncClient


async def _register(client: AsyncClient) -> tuple[str, uuid.UUID]:
    email = f"mr6-{uuid.uuid4().hex[:8]}@example.com"
    res = await client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "TestPass123",
            "full_name": "MR6 Staff",
            "business_name": f"MR6 Co {uuid.uuid4().hex[:6]}",
            "business_type": "salon",
            "postcode": "SW1A 1AA",
        },
    )
    assert res.status_code == 201
    token = res.json()["access_token"]
    tenant = await client.get("/api/v1/tenants/me", headers={"Authorization": f"Bearer {token}"})
    return token, uuid.UUID(tenant.json()["id"])


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_staff_qr_scan_awards_checkin_points(client: AsyncClient, db_session):
    from app.modules.crm.models import Customer
    from app.modules.membership_rewards.customer_auth.qr_tokens import issue_qr_token
    from app.modules.membership_rewards.service import grant_addon
    from app.modules.tenants.models import Tenant

    token, tenant_id = await _register(client)
    headers = _auth(token)
    await grant_addon(db_session, tenant_id)

    customer_id = uuid.uuid4()
    db_session.add(
        Customer(
            id=customer_id,
            tenant_id=tenant_id,
            first_name="Jamie",
            last_name="Visitor",
            email="jamie@scan.test",
        )
    )
    await db_session.commit()

    raw_token, _ = await issue_qr_token(db_session, tenant_id, customer_id)
    payload = f"cf-loyalty:{tenant_id}:{customer_id}:{raw_token}"

    scan = await client.post(
        "/api/v1/membership-rewards/qr/scan",
        headers=headers,
        json={"payload": payload},
    )
    assert scan.status_code == 200, scan.text
    body = scan.json()
    assert body["customer_name"] == "Jamie Visitor"
    assert body["points_awarded"] == 25
    assert body["points_balance"] == 25

    # Second scan same day — no duplicate visit points
    raw_token2, _ = await issue_qr_token(db_session, tenant_id, customer_id)
    payload2 = f"cf-loyalty:{tenant_id}:{customer_id}:{raw_token2}"
    scan2 = await client.post(
        "/api/v1/membership-rewards/qr/scan",
        headers=headers,
        json={"payload": payload2},
    )
    assert scan2.status_code == 200
    assert scan2.json()["points_awarded"] == 0
    assert scan2.json()["points_balance"] == 25


@pytest.mark.asyncio
async def test_staff_qr_scan_rejects_expired_token(client: AsyncClient, db_session):
    from datetime import datetime, timedelta, timezone

    from app.core.security import hash_token
    from app.modules.crm.models import Customer
    from app.modules.membership_rewards.models import MrCustomerQrToken
    from app.modules.membership_rewards.service import grant_addon
    from app.modules.tenants.models import Tenant
    import secrets

    token, tenant_id = await _register(client)
    headers = _auth(token)
    await grant_addon(db_session, tenant_id)

    customer_id = uuid.uuid4()
    db_session.add(
        Customer(
            id=customer_id,
            tenant_id=tenant_id,
            first_name="Expired",
            email="expired@scan.test",
        )
    )
    raw = secrets.token_urlsafe(32)
    db_session.add(
        MrCustomerQrToken(
            tenant_id=tenant_id,
            customer_id=customer_id,
            token_hash=hash_token(raw),
            expires_at=datetime.now(timezone.utc) - timedelta(minutes=1),
        )
    )
    await db_session.commit()

    payload = f"cf-loyalty:{tenant_id}:{customer_id}:{raw}"
    scan = await client.post(
        "/api/v1/membership-rewards/qr/scan",
        headers=headers,
        json={"payload": payload},
    )
    assert scan.status_code == 404


@pytest.mark.asyncio
async def test_staff_qr_scan_rejects_other_tenant(client: AsyncClient, db_session):
    from app.modules.crm.models import Customer
    from app.modules.membership_rewards.customer_auth.qr_tokens import issue_qr_token
    from app.modules.membership_rewards.service import grant_addon
    from app.modules.tenants.models import Tenant

    token, tenant_id = await _register(client)
    headers = _auth(token)
    await grant_addon(db_session, tenant_id)

    other_tenant_id = uuid.uuid4()
    db_session.add(
        Tenant(
            id=other_tenant_id,
            name="Other Biz",
            slug=f"other-{uuid.uuid4().hex[:6]}",
            email="other@test.com",
            business_type="salon",
            postcode="SW1A 1AA",
            is_active=True,
        )
    )
    customer_id = uuid.uuid4()
    db_session.add(
        Customer(
            id=customer_id,
            tenant_id=other_tenant_id,
            first_name="Other",
            email="other@scan.test",
        )
    )
    await db_session.commit()

    raw_token, _ = await issue_qr_token(db_session, other_tenant_id, customer_id)
    payload = f"cf-loyalty:{other_tenant_id}:{customer_id}:{raw_token}"

    scan = await client.post(
        "/api/v1/membership-rewards/qr/scan",
        headers=headers,
        json={"payload": payload},
    )
    assert scan.status_code == 403
