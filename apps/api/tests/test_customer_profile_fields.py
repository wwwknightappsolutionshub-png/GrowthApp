"""Customer profile extension fields."""
from __future__ import annotations

import uuid

import pytest

from app.core.security import hash_password
from app.modules.auth.models import User
from app.modules.crm.models import Customer
from app.modules.tenants.models import Tenant, TenantMember


@pytest.mark.asyncio
async def test_customer_business_profile_fields(db_session):
    owner = User(
        id=uuid.uuid4(),
        email=f"owner-{uuid.uuid4().hex[:6]}@test.com",
        password_hash=hash_password("TestPass123"),
        full_name="Owner",
        totp_backup_codes=[],
    )
    tenant = Tenant(
        id=uuid.uuid4(),
        slug=f"t-{uuid.uuid4().hex[:8]}",
        name="Test Co",
        business_type="plumber",
        postcode="SW1A 1AA",
        owner_user_id=owner.id,
    )
    db_session.add_all([owner, tenant])
    await db_session.flush()
    db_session.add(
        TenantMember(
            id=uuid.uuid4(),
            tenant_id=tenant.id,
            user_id=owner.id,
            role="owner",
        )
    )
    c = Customer(
        id=uuid.uuid4(),
        tenant_id=tenant.id,
        first_name="Acme",
        client_type="business",
        business_name="Acme Plumbing Ltd",
        phone="02070000000",
        address="1 High St",
        needs_reminders=True,
        special_event="Contract renewal",
    )
    db_session.add(c)
    await db_session.commit()
    await db_session.refresh(c)
    assert c.client_type == "business"
    assert c.business_name == "Acme Plumbing Ltd"
    assert c.needs_reminders is True
