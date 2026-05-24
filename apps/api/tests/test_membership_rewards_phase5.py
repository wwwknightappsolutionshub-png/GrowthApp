"""Phase 5 — booking loyalty provisioning and landing auto-generation."""

from __future__ import annotations

import uuid
from datetime import date, time

import pytest
from sqlalchemy import select


async def _register(client) -> tuple[str, uuid.UUID, str]:
    slug_suffix = uuid.uuid4().hex[:6]
    email = f"mr5-{slug_suffix}@example.com"
    res = await client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "TestPass123",
            "full_name": "MR5 Tester",
            "business_name": f"MR5 Co {slug_suffix}",
            "business_type": "plumber",
            "postcode": "SW1A 1AA",
        },
    )
    assert res.status_code == 201
    token = res.json()["access_token"]
    tenant = await client.get("/api/v1/tenants/me", headers={"Authorization": f"Bearer {token}"})
    tenant_id = uuid.UUID(tenant.json()["id"])
    slug = tenant.json()["slug"]
    await client.post(
        "/api/v1/membership-rewards/dev/grant",
        headers={"Authorization": f"Bearer {token}"},
    )
    return token, tenant_id, slug


@pytest.mark.asyncio
async def test_booking_provisions_loyalty_portal(client, db_session):
    from app.modules.crm.models import Customer
    from app.modules.membership_rewards.models import MrCustomerCredentials, MrCustomerMagicLink
    from app.modules.membership_rewards.customer_auth.provisioning import should_provision_from_booking

    _, tenant_id, slug = await _register(client)

    booking = await client.post(
        f"/api/v1/public/booking/{slug}",
        json={
            "customer_name": "Jamie Loyal",
            "customer_email": "jamie-loyal@example.com",
            "customer_phone": "07700900123",
            "booking_date": date.today().isoformat(),
            "start_time": time(10, 0).isoformat(),
            "join_loyalty_program": True,
        },
    )
    assert booking.status_code == 200, booking.text

    cust = (
        await db_session.execute(
            select(Customer.id).where(
                Customer.email == "jamie-loyal@example.com",
                Customer.tenant_id == tenant_id,
            )
        )
    ).scalar_one()

    creds = await db_session.get(MrCustomerCredentials, {"tenant_id": tenant_id, "customer_id": cust})
    assert creds is not None

    links = (
        await db_session.execute(
            select(MrCustomerMagicLink).where(MrCustomerMagicLink.customer_id == cust)
        )
    ).scalars().all()
    assert len(links) >= 1

    assert (
        await should_provision_from_booking(
            db_session,
            tenant_id=tenant_id,
            customer_id=cust,
            join_loyalty_program=True,
        )
        is False
    )


@pytest.mark.asyncio
async def test_booking_opt_out_skips_provisioning(client, db_session):
    from app.modules.crm.models import Customer
    from app.modules.membership_rewards.models import MrCustomerCredentials

    _, tenant_id, slug = await _register(client)

    res = await client.post(
        f"/api/v1/public/booking/{slug}",
        json={
            "customer_name": "Opt Out User",
            "customer_email": "opt-out@example.com",
            "booking_date": date.today().isoformat(),
            "start_time": time(11, 0).isoformat(),
            "join_loyalty_program": False,
        },
    )
    assert res.status_code == 200, res.text

    cust = (
        await db_session.execute(
            select(Customer.id).where(Customer.email == "opt-out@example.com", Customer.tenant_id == tenant_id)
        )
    ).scalar_one()

    creds = await db_session.get(MrCustomerCredentials, {"tenant_id": tenant_id, "customer_id": cust})
    assert creds is None


@pytest.mark.asyncio
async def test_widget_config_includes_loyalty_flag(client):
    _, _, slug = await _register(client)
    widget = await client.get(f"/api/v1/public/booking/{slug}/widget")
    assert widget.status_code == 200
    assert widget.json()["loyalty_program_available"] is True


@pytest.mark.asyncio
async def test_create_plan_auto_publishes_landing(client, db_session):
    from app.modules.membership_rewards.models import MrLandingConfig, MrTenantSettings
    from app.modules.membership_rewards.service import grant_addon

    email = f"mr5land-{uuid.uuid4().hex[:8]}@example.com"
    res = await client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "TestPass123",
            "full_name": "MR5 Tester",
            "business_name": f"MR5 Co {uuid.uuid4().hex[:6]}",
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

    await grant_addon(db_session, tenant_id)

    pub_before = await client.get(f"/api/v1/public/memberships/{slug}")
    assert pub_before.status_code == 404

    plan = await client.post(
        "/api/v1/membership-rewards/plans",
        headers=headers,
        json={"name": "Starter", "billing_cycle": "monthly", "price_pence": 1999},
    )
    assert plan.status_code == 200, plan.text

    pub_after = await client.get(f"/api/v1/public/memberships/{slug}")
    assert pub_after.status_code == 200
    body = pub_after.json()
    assert body["tenant_slug"] == slug
    assert len(body["plans"]) == 1

    cfg = await db_session.get(MrLandingConfig, tenant_id)
    settings = await db_session.get(MrTenantSettings, tenant_id)
    assert cfg.published is True
    assert settings.landing_published is True


@pytest.mark.asyncio
async def test_regenerate_landing_and_interest_lead(client, db_session):
    from app.modules.membership_rewards.service import grant_addon

    email = f"mr5blead-{uuid.uuid4().hex[:8]}@example.com"
    res = await client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "TestPass123",
            "full_name": "Lead Tester",
            "business_name": f"Lead Co {uuid.uuid4().hex[:6]}",
            "business_type": "plumber",
            "postcode": "E1 6AN",
        },
    )
    token = res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    tenant = await client.get("/api/v1/tenants/me", headers=headers)
    tenant_id = uuid.UUID(tenant.json()["id"])
    slug = tenant.json()["slug"]
    await grant_addon(db_session, tenant_id)

    await client.post(
        "/api/v1/membership-rewards/plans",
        headers=headers,
        json={"name": "Gold", "billing_cycle": "yearly", "price_pence": 9999},
    )

    regen = await client.post("/api/v1/membership-rewards/landing/regenerate", headers=headers)
    assert regen.status_code == 200
    assert regen.json()["auto_generated"] is True

    interest = await client.post(
        f"/api/v1/public/memberships/{slug}/interest",
        json={
            "first_name": "Alex",
            "email": "alex@example.com",
            "message": "I want to join",
        },
    )
    assert interest.status_code == 201
