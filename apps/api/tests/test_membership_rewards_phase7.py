"""Phase 7 — feature flags on /addons/status and Stripe billing sync."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytest


async def _register(client) -> tuple[str, uuid.UUID]:
    email = f"mr7-{uuid.uuid4().hex[:8]}@example.com"
    res = await client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "TestPass123",
            "full_name": "MR7 Tester",
            "business_name": f"MR7 Co {uuid.uuid4().hex[:6]}",
            "business_type": "plumber",
            "postcode": "SW1A 1AA",
        },
    )
    assert res.status_code == 201
    token = res.json()["access_token"]
    me = await client.get("/api/v1/tenants/me", headers={"Authorization": f"Bearer {token}"})
    return token, uuid.UUID(me.json()["id"])


@pytest.mark.asyncio
async def test_addons_status_includes_membership_rewards(client):
    token, _ = await _register(client)
    headers = {"Authorization": f"Bearer {token}"}

    res = await client.get("/api/v1/addons/status", headers=headers)
    assert res.status_code == 200
    body = res.json()
    assert body["membership_rewards"] is True
    codes = {item["feature_code"] for item in body["items"]}
    assert "membership_rewards" in codes


@pytest.mark.asyncio
async def test_status_exposes_billing_flags(client):
    token, _ = await _register(client)
    headers = {"Authorization": f"Bearer {token}"}

    res = await client.get("/api/v1/membership-rewards/status", headers=headers)
    assert res.status_code == 200
    body = res.json()
    assert body["has_membership_rewards"] is True
    assert body["is_trial"] is True
    assert body["billing_source"] == "trial"
    assert "stripe_configured" in body


@pytest.mark.asyncio
async def test_activate_from_checkout_stores_subscription_item(client, db_session):
    from app.modules.accounting.models import TenantAddon
    from app.modules.membership_rewards.constants import FEATURE_MEMBERSHIP_REWARDS
    from app.modules.membership_rewards import service as mr_service
    from sqlalchemy import select

    token, tenant_id = await _register(client)
    item_id = "si_test_membership_item"

    await mr_service.activate_from_checkout_metadata(
        db_session,
        tenant_id=tenant_id,
        stripe_subscription_item_id=item_id,
        checkout_session_id="cs_test_123",
    )

    row = (
        await db_session.execute(
            select(TenantAddon).where(
                TenantAddon.tenant_id == tenant_id,
                TenantAddon.feature_code == FEATURE_MEMBERSHIP_REWARDS,
            )
        )
    ).scalar_one()
    assert row.status == "active"
    assert row.stripe_subscription_item_id == item_id
    assert row.expires_at is None

    status = await client.get(
        "/api/v1/membership-rewards/status",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert status.json()["is_paid"] is True
    assert status.json()["billing_source"] == "stripe"


@pytest.mark.asyncio
async def test_sync_revokes_on_canceled_subscription(client, db_session):
    from app.modules.accounting.models import TenantAddon
    from app.modules.billing.models import Subscription
    from app.modules.membership_rewards.constants import FEATURE_MEMBERSHIP_REWARDS
    from app.modules.membership_rewards.billing import sync_addon_from_stripe_subscription
    from app.modules.membership_rewards import service as mr_service
    from sqlalchemy import select

    token, tenant_id = await _register(client)
    await mr_service.activate_from_checkout_metadata(
        db_session,
        tenant_id=tenant_id,
        stripe_subscription_item_id="si_revoke_test",
    )

    sub_id = f"sub_{uuid.uuid4().hex[:12]}"
    db_session.add(
        Subscription(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            plan_id=uuid.uuid4(),
            stripe_subscription_id=sub_id,
            stripe_customer_id="cus_test",
            status="active",
        )
    )
    await db_session.commit()

    stripe_sub = {
        "id": sub_id,
        "status": "canceled",
        "items": {
            "data": [
                {
                    "id": "si_revoke_test",
                    "price": {"id": "price_membership_test"},
                }
            ]
        },
    }

    with patch("app.modules.membership_rewards.billing.settings") as mock_settings:
        mock_settings.STRIPE_PRICE_MEMBERSHIP_REWARDS = "price_membership_test"
        await sync_addon_from_stripe_subscription(
            db_session, stripe_subscription_id=sub_id, stripe_sub=stripe_sub
        )

    row = (
        await db_session.execute(
            select(TenantAddon).where(
                TenantAddon.tenant_id == tenant_id,
                TenantAddon.feature_code == FEATURE_MEMBERSHIP_REWARDS,
            )
        )
    ).scalar_one()
    assert row.status == "canceled"

    blocked = await client.get(
        "/api/v1/membership-rewards/plans",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert blocked.status_code == 403


@pytest.mark.asyncio
async def test_revoke_addon(client, db_session):
    from app.modules.membership_rewards import service as mr_service
    from app.modules.membership_rewards.entitlement import tenant_has_membership_rewards

    _, tenant_id = await _register(client)
    assert await tenant_has_membership_rewards(db_session, tenant_id)
    await mr_service.revoke_addon(db_session, tenant_id)
    assert not await tenant_has_membership_rewards(db_session, tenant_id)


@pytest.mark.asyncio
async def test_public_surfaces_blocked_when_trial_expired(client, db_session):
    """Phase 7 — public landing, interest, and enroll hard-stop after trial expiry."""
    from datetime import datetime, timedelta, timezone

    from app.modules.accounting.models import TenantAddon
    from app.modules.membership_rewards.constants import FEATURE_MEMBERSHIP_REWARDS
    from app.modules.membership_rewards.models import MrMembershipPlan
    from app.modules.membership_rewards.service import grant_addon, publish_landing
    from sqlalchemy import select

    token, tenant_id = await _register(client)
    headers = {"Authorization": f"Bearer {token}"}
    tenant = await client.get("/api/v1/tenants/me", headers=headers)
    slug = tenant.json()["slug"]

    await grant_addon(db_session, tenant_id)
    db_session.add(
        MrMembershipPlan(
            tenant_id=tenant_id,
            name="Public",
            billing_cycle="monthly",
            price_pence=1500,
            is_active=True,
        )
    )
    await db_session.commit()
    await publish_landing(db_session, tenant_id)

    ok = await client.get(f"/api/v1/public/memberships/{slug}")
    assert ok.status_code == 200

    row = (
        await db_session.execute(
            select(TenantAddon).where(
                TenantAddon.tenant_id == tenant_id,
                TenantAddon.feature_code == FEATURE_MEMBERSHIP_REWARDS,
            )
        )
    ).scalar_one()
    row.expires_at = datetime.now(timezone.utc) - timedelta(days=1)
    await db_session.commit()

    blocked_page = await client.get(f"/api/v1/public/memberships/{slug}")
    assert blocked_page.status_code == 404

    blocked_loyalty = await client.get(f"/api/v1/public/loyalty/{slug}")
    assert blocked_loyalty.status_code == 404

    interest = await client.post(
        f"/api/v1/public/memberships/{slug}/interest",
        json={"first_name": "Pat", "email": "pat@expired.test"},
    )
    assert interest.status_code == 404

    enroll = await client.post(
        f"/api/v1/public/memberships/{slug}/loyalty-enroll",
        json={"name": "Pat", "email": "pat@expired.test", "tier_code": "bronze"},
    )
    assert enroll.status_code == 404

    magic = await client.post(
        "/api/v1/loyalty-portal/auth/magic-link",
        json={"email": "pat@expired.test", "tenant_slug": slug},
    )
    assert magic.status_code == 200

    branding = await client.get(f"/api/v1/public/loyalty/{slug}/branding")
    assert branding.status_code == 200
    assert branding.json()["loyalty_enabled"] is False
