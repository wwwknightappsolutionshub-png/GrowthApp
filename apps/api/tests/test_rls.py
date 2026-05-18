"""Row-Level Security regression tests (PostgreSQL only)."""
from __future__ import annotations

import uuid

import pytest
from sqlalchemy import select, text

from tests.conftest import postgres_only

from app.core.database import set_rls_context
from app.modules.leads.models import Lead
from app.modules.tenants.models import Tenant


async def _make_tenant(db_session, slug_suffix: str) -> Tenant:
    t = Tenant(
        id=uuid.uuid4(),
        slug=f"rls-{slug_suffix}-{uuid.uuid4().hex[:6]}",
        name=f"Tenant {slug_suffix}",
        business_type="plumber",
        postcode="SW1A1AA",
    )
    db_session.add(t)
    await db_session.commit()
    return t


async def _add_lead(db_session, tenant_id, first_name: str) -> uuid.UUID:
    lead_id = uuid.uuid4()
    db_session.add(Lead(
        id=lead_id, tenant_id=tenant_id,
        first_name=first_name, source="web_form", status="new",
    ))
    await db_session.commit()
    return lead_id


@postgres_only
@pytest.mark.asyncio
async def test_rls_isolates_tenants(db_session):
    """A SELECT under tenant A's GUC must not return tenant B's rows."""
    a = await _make_tenant(db_session, "a")
    b = await _make_tenant(db_session, "b")

    # Insert as superuser (no GUC) so initial setup is unrestricted.
    await set_rls_context(db_session, None)
    a_lead = await _add_lead(db_session, a.id, "Alice")
    b_lead = await _add_lead(db_session, b.id, "Bob")

    # Now scope to tenant A.
    await set_rls_context(db_session, a.id)
    rows = (await db_session.execute(select(Lead))).scalars().all()
    ids = {r.id for r in rows}
    assert a_lead in ids, "tenant A should see its own lead"
    assert b_lead not in ids, "tenant A must NOT see tenant B's lead"

    # And vice versa.
    await set_rls_context(db_session, b.id)
    rows = (await db_session.execute(select(Lead))).scalars().all()
    ids = {r.id for r in rows}
    assert b_lead in ids
    assert a_lead not in ids


@postgres_only
@pytest.mark.asyncio
async def test_rls_blocks_writes_to_other_tenant(db_session):
    """Trying to insert a row pointing at a different tenant_id must be denied."""
    a = await _make_tenant(db_session, "wa")
    b = await _make_tenant(db_session, "wb")

    await set_rls_context(db_session, a.id)
    # Attempt to insert a lead targeting tenant B while in A's context.
    with pytest.raises(Exception):
        await db_session.execute(text(
            "INSERT INTO leads (id, tenant_id, first_name, source, status, is_spam, tags, extra_data) "
            "VALUES (gen_random_uuid(), :tid, 'mallory', 'web_form', 'new', false, '[]'::jsonb, '{}'::jsonb)"
        ), {"tid": str(b.id)})
        await db_session.commit()
    await db_session.rollback()
