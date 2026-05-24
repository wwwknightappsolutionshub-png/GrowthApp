"""Loyalty tier enrollment — portal provisioning and duplicate guards."""

from __future__ import annotations

import uuid

import pytest
from sqlalchemy import select


async def _setup_public_memberships(client, db_session) -> tuple[str, uuid.UUID]:
    slug_suffix = uuid.uuid4().hex[:6]
    email = f"mrenroll-{slug_suffix}@example.com"
    res = await client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "TestPass123",
            "full_name": "Enroll Tester",
            "business_name": f"Enroll Co {slug_suffix}",
            "business_type": "plumber",
            "postcode": "SW1A 1AA",
        },
    )
    assert res.status_code == 201
    token = res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    tenant = await client.get("/api/v1/tenants/me", headers=headers)
    tenant_id = uuid.UUID(tenant.json()["id"])
    slug = tenant.json()["slug"]

    from app.modules.membership_rewards.models import MrMembershipPlan
    from app.modules.membership_rewards.service import grant_addon, publish_landing

    await grant_addon(db_session, tenant_id)
    db_session.add(
        MrMembershipPlan(
            tenant_id=tenant_id,
            name="Basic",
            billing_cycle="monthly",
            price_pence=999,
            is_active=True,
        )
    )
    await db_session.commit()
    await publish_landing(db_session, tenant_id)
    return slug, tenant_id


@pytest.mark.asyncio
async def test_loyalty_enroll_creates_portal_account(client, db_session):
    from app.modules.crm.models import Customer
    from app.modules.membership_rewards.models import MrCustomerCredentials, MrCustomerMagicLink

    slug, tenant_id = await _setup_public_memberships(client, db_session)
    member_email = f"member-{uuid.uuid4().hex[:8]}@example.com"

    enroll = await client.post(
        f"/api/v1/public/memberships/{slug}/loyalty-enroll",
        json={
            "name": "Alex Member",
            "email": member_email,
            "phone": "07700900456",
            "tier_code": "bronze",
        },
    )
    assert enroll.status_code == 201, enroll.text
    body = enroll.json()
    assert body["tier_code"] == "bronze"
    assert body["portal_account_created"] is True
    assert body["rewards_email_sent"] is True

    cust_id = (
        await db_session.execute(
            select(Customer.id).where(
                Customer.tenant_id == tenant_id,
                Customer.email == member_email,
            )
        )
    ).scalar_one()

    creds = await db_session.get(
        MrCustomerCredentials, {"tenant_id": tenant_id, "customer_id": cust_id}
    )
    assert creds is not None

    links = (
        await db_session.execute(
            select(MrCustomerMagicLink).where(MrCustomerMagicLink.customer_id == cust_id)
        )
    ).scalars().all()
    assert len(links) >= 1


@pytest.mark.asyncio
async def test_loyalty_enroll_rejects_duplicate_email(client, db_session):
    slug, _ = await _setup_public_memberships(client, db_session)
    member_email = f"dup-{uuid.uuid4().hex[:8]}@example.com"

    first = await client.post(
        f"/api/v1/public/memberships/{slug}/loyalty-enroll",
        json={"name": "First User", "email": member_email, "tier_code": "bronze"},
    )
    assert first.status_code == 201, first.text

    second = await client.post(
        f"/api/v1/public/memberships/{slug}/loyalty-enroll",
        json={"name": "Second User", "email": member_email, "tier_code": "silver"},
    )
    assert second.status_code == 400
    assert "already registered" in second.json()["detail"].lower()


@pytest.mark.asyncio
async def test_loyalty_enroll_rejects_duplicate_phone(client, db_session):
    slug, _ = await _setup_public_memberships(client, db_session)
    phone = "07700900789"

    first = await client.post(
        f"/api/v1/public/memberships/{slug}/loyalty-enroll",
        json={
            "name": "Phone User",
            "email": f"phone-a-{uuid.uuid4().hex[:6]}@example.com",
            "phone": phone,
            "tier_code": "bronze",
        },
    )
    assert first.status_code == 201, first.text

    second = await client.post(
        f"/api/v1/public/memberships/{slug}/loyalty-enroll",
        json={
            "name": "Other User",
            "email": f"phone-b-{uuid.uuid4().hex[:6]}@example.com",
            "phone": phone,
            "tier_code": "silver",
        },
    )
    assert second.status_code == 400
    assert "already registered" in second.json()["detail"].lower()


@pytest.mark.asyncio
async def test_loyalty_enroll_succeeds_when_lead_email_rejected(client, db_session):
    """Reserved TLDs (e.g. .local) must not fail enrollment after portal provisioning."""
    slug, _ = await _setup_public_memberships(client, db_session)
    member_email = f"debug-{uuid.uuid4().hex[:8]}@test.local"

    enroll = await client.post(
        f"/api/v1/public/memberships/{slug}/loyalty-enroll",
        json={"name": "Local Tester", "email": member_email, "tier_code": "bronze"},
    )
    assert enroll.status_code == 201, enroll.text
    body = enroll.json()
    assert body["tier_code"] == "bronze"
    assert body["portal_account_created"] is True


@pytest.mark.asyncio
async def test_loyalty_enroll_requires_email(client, db_session):
    slug, _ = await _setup_public_memberships(client, db_session)

    res = await client.post(
        f"/api/v1/public/memberships/{slug}/loyalty-enroll",
        json={"name": "No Email", "phone": "07700900333", "tier_code": "bronze"},
    )
    assert res.status_code == 422
    detail = str(res.json()).lower()
    assert "email" in detail
