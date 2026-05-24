"""Phase 4 — customer loyalty portal API."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_portal_branding_and_magic_link_flow(client: AsyncClient, db_session):
    from app.modules.crm.models import Customer
    from app.modules.membership_rewards.customer_auth.credentials import ensure_credentials
    from app.modules.membership_rewards.service import grant_addon
    from app.modules.tenants.models import Tenant

    tenant_id = uuid.uuid4()
    customer_id = uuid.uuid4()
    slug = f"portal-{uuid.uuid4().hex[:6]}"
    db_session.add(
        Tenant(
            id=tenant_id,
            name="Portal Test Co",
            slug=slug,
            email="owner@portal.test",
            business_type="salon",
            postcode="SW1A 1AA",
            is_active=True,
            primary_color="#9333EA",
        )
    )
    await grant_addon(db_session, tenant_id)
    db_session.add(
        Customer(
            id=customer_id,
            tenant_id=tenant_id,
            first_name="Alex",
            last_name="Member",
            email="alex@portal.test",
        )
    )
    await db_session.commit()

    branding = await client.get(f"/api/v1/loyalty-portal/public/branding/{slug}")
    assert branding.status_code == 200
    body = branding.json()
    assert body["tenant_slug"] == slug
    assert body["primary_color"] == "#9333EA"
    assert body["loyalty_enabled"] is True

    public_branding = await client.get(f"/api/v1/public/loyalty/{slug}/branding")
    assert public_branding.status_code == 200

    magic_req = await client.post(
        "/api/v1/loyalty-portal/auth/magic-link",
        json={"email": "alex@portal.test", "tenant_slug": slug},
    )
    assert magic_req.status_code == 200

    from sqlalchemy import select
    from app.core.security import hash_token
    from app.modules.membership_rewards.models import MrCustomerMagicLink
    import secrets

    raw = secrets.token_urlsafe(48)
    db_session.add(
        MrCustomerMagicLink(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            customer_id=customer_id,
            email="alex@portal.test",
            token_hash=hash_token(raw),
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=30),
        )
    )
    await db_session.commit()

    verify = await client.post(
        "/api/v1/loyalty-portal/auth/magic-link/verify",
        json={"token": raw, "tenant_slug": slug},
    )
    assert verify.status_code == 200
    token = verify.json()["access_token"]
    assert token

    me = await client.get(
        "/api/v1/loyalty-portal/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert me.status_code == 200
    profile = me.json()
    assert profile["first_name"] == "Alex"
    assert profile["tenant_slug"] == slug


@pytest.mark.asyncio
async def test_portal_password_login_and_redeem(client: AsyncClient, db_session):
    from app.modules.crm.models import Customer
    from app.modules.membership_rewards.customer_auth.credentials import ensure_credentials
    from app.modules.membership_rewards.engines.earning_engine import earn_points
    from app.modules.membership_rewards.models import MrRewardCatalog
    from app.modules.membership_rewards.service import grant_addon
    from app.modules.tenants.models import Tenant

    tenant_id = uuid.uuid4()
    customer_id = uuid.uuid4()
    slug = f"redeem-{uuid.uuid4().hex[:6]}"
    db_session.add(
        Tenant(
            id=tenant_id,
            name="Redeem Test",
            slug=slug,
            email="owner@redeem.test",
            business_type="salon",
            postcode="SW1A 1AA",
            is_active=True,
        )
    )
    await grant_addon(db_session, tenant_id)
    db_session.add(
        Customer(
            id=customer_id,
            tenant_id=tenant_id,
            first_name="Sam",
            email="sam@redeem.test",
        )
    )
    await ensure_credentials(
        db_session, tenant_id, customer_id, temp_password="SecurePass123"
    )
    await db_session.commit()

    await earn_points(
        db_session,
        tenant_id,
        customer_id,
        500,
        source="adjustment",
        description="test",
    )

    item = MrRewardCatalog(
        tenant_id=tenant_id,
        name="Free drink",
        points_cost=100,
        is_active=True,
    )
    db_session.add(item)
    await db_session.commit()
    await db_session.refresh(item)

    login = await client.post(
        "/api/v1/loyalty-portal/auth/login",
        json={
            "email": "sam@redeem.test",
            "password": "SecurePass123",
            "tenant_slug": slug,
        },
    )
    assert login.status_code == 200
    token = login.json()["access_token"]
    assert login.json()["must_change_password"] is True

    rewards = await client.get(
        "/api/v1/loyalty-portal/rewards",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert rewards.status_code == 200
    assert len(rewards.json()["items"]) == 1

    redeem = await client.post(
        f"/api/v1/loyalty-portal/rewards/{item.id}/redeem",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert redeem.status_code == 200
    assert redeem.json()["points_spent"] == 100
    assert redeem.json()["reward_name"] == "Free drink"

    me = await client.get(
        "/api/v1/loyalty-portal/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert me.json()["points_balance"] == 400

    qr = await client.get(
        "/api/v1/loyalty-portal/qr",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert qr.status_code == 200
    assert qr.json()["qr_data_url"].startswith("data:image/png;base64,")
