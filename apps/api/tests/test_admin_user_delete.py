"""Super-admin delete user — soft and permanent."""
from __future__ import annotations

import uuid

import pytest
from sqlalchemy import select

from app.core.security import create_access_token, decode_access_token, hash_password
from app.modules.auth.models import User
from app.modules.tenants.models import Tenant, TenantMember


async def _make_superadmin(db_session) -> User:
    u = User(
        id=uuid.uuid4(),
        email=f"sa-{uuid.uuid4().hex[:6]}@customerflow.ai",
        password_hash=hash_password("Sup3rPass!"),
        full_name="Test Admin",
        is_superadmin=True,
        totp_backup_codes=[],
    )
    db_session.add(u)
    await db_session.commit()
    return u


@pytest.mark.asyncio
async def test_admin_soft_delete_user(client, db_session):
    admin = await _make_superadmin(db_session)
    token = create_access_token(subject=admin.id, tenant_id=None, role=None)

    reg = await client.post(
        "/api/v1/auth/register",
        json={
            "email": f"del-soft-{uuid.uuid4().hex[:6]}@example.com",
            "password": "TestPass123",
            "full_name": "Delete Me Soft",
            "business_name": f"Del Co {uuid.uuid4().hex[:4]}",
            "business_type": "plumber",
            "postcode": "SW1A 1AA",
        },
    )
    assert reg.status_code == 201
    user_id = decode_access_token(reg.json()["access_token"])["sub"]

    res = await client.delete(
        f"/api/v1/admin/users/{user_id}",
        params={"permanent": False},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200, res.text
    assert "deleted" in res.json()["message"].lower()

    row = (
        await db_session.execute(select(User).where(User.id == uuid.UUID(user_id)))
    ).scalar_one()
    assert row.deleted_at is not None


@pytest.mark.asyncio
async def test_admin_permanent_delete_user(client, db_session):
    admin = await _make_superadmin(db_session)
    token = create_access_token(subject=admin.id, tenant_id=None, role=None)

    reg = await client.post(
        "/api/v1/auth/register",
        json={
            "email": f"del-hard-{uuid.uuid4().hex[:6]}@example.com",
            "password": "TestPass123",
            "full_name": "Delete Me Hard",
            "business_name": f"Hard Del Co {uuid.uuid4().hex[:4]}",
            "business_type": "plumber",
            "postcode": "SW1A 1AA",
        },
    )
    assert reg.status_code == 201
    user_id = uuid.UUID(decode_access_token(reg.json()["access_token"])["sub"])

    owned_tenant = (
        await db_session.execute(
            select(Tenant)
            .join(TenantMember, TenantMember.tenant_id == Tenant.id)
            .where(TenantMember.user_id == user_id, TenantMember.role == "owner")
        )
    ).scalar_one()

    res = await client.delete(
        f"/api/v1/admin/users/{user_id}",
        params={"permanent": True},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200, res.text
    assert "permanently deleted" in res.json()["message"].lower()

    assert (
        await db_session.execute(select(User).where(User.id == user_id))
    ).scalar_one_or_none() is None
    assert (
        await db_session.execute(select(Tenant).where(Tenant.id == owned_tenant.id))
    ).scalar_one_or_none() is None
