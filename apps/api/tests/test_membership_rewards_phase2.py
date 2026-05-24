"""Phase 2 — loyalty engines and customer portal models."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import pytest


@pytest.mark.asyncio
async def test_earn_and_redeem_via_engines(db_session):
    from app.modules.crm.models import Customer
    from app.modules.membership_rewards.engines.earning_engine import earn_points
    from app.modules.membership_rewards.engines.redemption_engine import redeem_reward
    from app.modules.membership_rewards.models import MrRewardCatalog
    from app.modules.membership_rewards.service import grant_addon
    from app.modules.tenants.models import Tenant

    tenant_id = uuid.uuid4()
    customer_id = uuid.uuid4()
    db_session.add(
        Tenant(
            id=tenant_id,
            name="Engine Test",
            slug=f"eng-{uuid.uuid4().hex[:6]}",
            email="eng@test.com",
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
            first_name="Test",
            last_name="User",
            email="loyalty-engine@test.com",
        )
    )
    await db_session.flush()

    entry = await earn_points(
        db_session,
        tenant_id,
        customer_id,
        500,
        source="adjustment",
        description="test credit",
    )
    assert entry.balance_after == 500

    item = MrRewardCatalog(
        tenant_id=tenant_id,
        name="Free coffee",
        points_cost=100,
        is_active=True,
    )
    db_session.add(item)
    await db_session.commit()
    await db_session.refresh(item)

    redemption = await redeem_reward(db_session, tenant_id, customer_id, item.id)
    assert redemption.points_spent == 100


@pytest.mark.asyncio
async def test_sweep_expired_points(db_session):
    from app.modules.crm.models import Customer
    from app.modules.membership_rewards.engines.earning_engine import earn_points, sweep_expired_points
    from app.modules.membership_rewards.models import MrCustomerLoyalty, MrPointsLedger, MrTenantSettings
    from app.modules.membership_rewards.service import grant_addon
    from app.modules.tenants.models import Tenant

    tenant_id = uuid.uuid4()
    customer_id = uuid.uuid4()
    db_session.add(
        Tenant(
            id=tenant_id,
            name="Expiry Test",
            slug=f"exp-{uuid.uuid4().hex[:6]}",
            email="exp-owner@test.com",
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
            first_name="Exp",
            last_name="User",
            email="expiry@test.com",
        )
    )
    await db_session.flush()

    settings = await db_session.get(MrTenantSettings, tenant_id)
    settings.points_expire_days = 30
    await db_session.commit()

    await earn_points(
        db_session,
        tenant_id,
        customer_id,
        200,
        source="adjustment",
        description="will expire",
    )

    ledger = (
        await db_session.execute(
            MrPointsLedger.__table__.select().where(
                MrPointsLedger.tenant_id == tenant_id,
                MrPointsLedger.customer_id == customer_id,
                MrPointsLedger.amount > 0,
            )
        )
    ).first()
    assert ledger is not None
    row = await db_session.get(MrPointsLedger, ledger.id)
    row.expires_at = datetime.now(timezone.utc) - timedelta(days=1)
    await db_session.commit()

    expired = await sweep_expired_points(db_session)
    assert expired == 1

    loyalty = await db_session.get(
        MrCustomerLoyalty, {"tenant_id": tenant_id, "customer_id": customer_id}
    )
    assert loyalty.points_balance == 0


@pytest.mark.asyncio
async def test_customer_credentials_and_magic_link(db_session):
    from app.modules.crm.models import Customer
    from app.modules.membership_rewards.customer_auth.credentials import (
        authenticate_customer,
        ensure_credentials,
    )
    from app.modules.membership_rewards.customer_auth.magic_link import consume_magic_link, issue_magic_link
    from app.modules.tenants.models import Tenant

    tenant_id = uuid.uuid4()
    customer_id = uuid.uuid4()
    db_session.add(
        Tenant(
            id=tenant_id,
            name="Test Salon",
            slug=f"test-{uuid.uuid4().hex[:6]}",
            email="owner@test.com",
            business_type="salon",
            postcode="SW1A 1AA",
            is_active=True,
        )
    )
    db_session.add(
        Customer(
            id=customer_id,
            tenant_id=tenant_id,
            first_name="Pat",
            email="pat@test.com",
        )
    )
    await db_session.commit()

    _, temp = await ensure_credentials(db_session, tenant_id, customer_id, temp_password="TempPass123")
    assert temp == "TempPass123"
    await db_session.commit()

    tokens = await authenticate_customer(db_session, tenant_id, customer_id, "TempPass123")
    assert tokens["access_token"]
    assert tokens["must_change_password"] is True

    await issue_magic_link(
        db_session,
        tenant_id=tenant_id,
        customer_id=customer_id,
        email="pat@test.com",
    )
    # Re-issue to get raw token from DB is awkward; test consume via stored hash path
    from sqlalchemy import select
    from app.modules.membership_rewards.models import MrCustomerMagicLink
    from app.core.security import hash_token
    import secrets

    raw = secrets.token_urlsafe(48)
    db_session.add(
        MrCustomerMagicLink(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            customer_id=customer_id,
            email="pat@test.com",
            token_hash=hash_token(raw),
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=30),
        )
    )
    await db_session.commit()

    result = await consume_magic_link(db_session, raw_token=raw, tenant_id=tenant_id)
    assert result["customer_id"] == str(customer_id)
    assert result["access_token"]
