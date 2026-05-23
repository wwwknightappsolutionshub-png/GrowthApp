"""Phase 6 — trial reminders sweep and trial status API."""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import pytest


@pytest.mark.asyncio
async def test_trial_status_on_active_trial(client, db_session):
    from app.modules.membership_rewards.reminders import get_trial_status
    from app.modules.membership_rewards.service import start_trial_for_tenant

    email = f"mr6-{uuid.uuid4().hex[:8]}@example.com"
    res = await client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "TestPass123",
            "full_name": "MR6 Tester",
            "business_name": f"MR6 Co {uuid.uuid4().hex[:6]}",
            "business_type": "plumber",
            "postcode": "SW1A 1AA",
        },
    )
    token = res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    tenant = await client.get("/api/v1/tenants/me", headers=headers)
    tenant_id = uuid.UUID(tenant.json()["id"])

    await start_trial_for_tenant(db_session, tenant_id)

    trial_api = await client.get("/api/v1/membership-rewards/trial", headers=headers)
    assert trial_api.status_code == 200
    body = trial_api.json()
    assert body["on_trial"] is True
    assert body["days_remaining"] >= 0
    assert body["setup_url"].endswith("/dashboard/membership-rewards")

    status = await get_trial_status(db_session, tenant_id)
    assert status["on_trial"] is True


@pytest.mark.asyncio
async def test_sweep_day3_email_and_notification(db_session):
    from app.modules.accounting.models import TenantAddon
    from app.modules.auth.models import User
    from app.modules.membership_rewards.constants import FEATURE_MEMBERSHIP_REWARDS
    from app.modules.membership_rewards.models import MrTrialReminders
    from app.modules.membership_rewards.reminders import sweep_membership_trial_reminders
    from app.modules.notifications.models import Notification
    from app.modules.tenants.models import Tenant, TenantMember
    from sqlalchemy import select

    tenant_id = uuid.uuid4()
    user_id = uuid.uuid4()
    db_session.add(
        Tenant(
            id=tenant_id,
            slug=f"t-{uuid.uuid4().hex[:8]}",
            name="Sweep Test",
            business_type="plumber",
            postcode="SW1A 1AA",
        )
    )
    db_session.add(
        User(
            id=user_id,
            email=f"sweep-{uuid.uuid4().hex[:6]}@example.com",
            password_hash="x",
            full_name="Sweep Owner",
        )
    )
    db_session.add(
        TenantMember(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            user_id=user_id,
            role="owner",
            joined_at=datetime.now(timezone.utc),
        )
    )
    now = datetime.now(timezone.utc)
    ends = now + timedelta(days=7)
    db_session.add(
        TenantAddon(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            feature_code=FEATURE_MEMBERSHIP_REWARDS,
            status="active",
            granted_at=now,
            expires_at=ends,
        )
    )
    db_session.add(
        MrTrialReminders(
            tenant_id=tenant_id,
            trial_started_at=now - timedelta(days=4),
            trial_ends_at=ends,
        )
    )
    await db_session.commit()

    count = await sweep_membership_trial_reminders(db_session)
    assert count >= 1

    trial = await db_session.get(MrTrialReminders, tenant_id)
    assert trial.day3_email_at is not None

    notifs = (
        await db_session.execute(
            select(Notification).where(
                Notification.tenant_id == tenant_id,
                Notification.kind == "membership.trial_reminder",
            )
        )
    ).scalars().all()
    assert len(notifs) >= 1


@pytest.mark.asyncio
async def test_sweep_winback_after_expiry(db_session):
    from app.modules.accounting.models import TenantAddon
    from app.modules.auth.models import User
    from app.modules.membership_rewards.constants import FEATURE_MEMBERSHIP_REWARDS
    from app.modules.membership_rewards.models import MrTrialReminders
    from app.modules.membership_rewards.reminders import get_trial_status, sweep_membership_trial_reminders
    from app.modules.tenants.models import Tenant, TenantMember

    tenant_id = uuid.uuid4()
    user_id = uuid.uuid4()
    db_session.add(
        Tenant(
            id=tenant_id,
            slug=f"w-{uuid.uuid4().hex[:8]}",
            name="Winback Co",
            business_type="plumber",
            postcode="E1 1AA",
        )
    )
    db_session.add(
        User(
            id=user_id,
            email=f"wb-{uuid.uuid4().hex[:6]}@example.com",
            password_hash="x",
            full_name="Winback Owner",
        )
    )
    db_session.add(
        TenantMember(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            user_id=user_id,
            role="owner",
            joined_at=datetime.now(timezone.utc),
        )
    )
    started = datetime.now(timezone.utc) - timedelta(days=16)
    expired = datetime.now(timezone.utc) - timedelta(days=9)
    db_session.add(
        TenantAddon(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            feature_code=FEATURE_MEMBERSHIP_REWARDS,
            status="active",
            granted_at=started,
            expires_at=expired,
        )
    )
    db_session.add(
        MrTrialReminders(
            tenant_id=tenant_id,
            trial_started_at=started,
            trial_ends_at=started + timedelta(days=7),
            winback_discount_percent=50,
        )
    )
    await db_session.commit()

    count = await sweep_membership_trial_reminders(db_session)
    assert count >= 1

    trial_row = await db_session.get(MrTrialReminders, tenant_id)
    assert trial_row.day15_winback_at is not None

    status = await get_trial_status(db_session, tenant_id)
    assert status["show_winback_banner"] is True
    assert status["winback_discount_percent"] == 50
