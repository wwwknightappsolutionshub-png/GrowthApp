"""Tests for the centralised audit-logging helper.

Verifies that:
  * `log_action` writes an AuditLog row that survives the caller's commit.
  * The `extra_metadata` field round-trips JSON correctly.
  * Errors from a bad session do not propagate to the caller (best-effort).
"""
import uuid

import pytest
from sqlalchemy import select

from app.core.audit import log_action
from app.modules.audit.models import AuditLog


@pytest.mark.asyncio
async def test_log_action_persists(db_session):
    tenant_id = uuid.uuid4()
    user_id = uuid.uuid4()
    resource_id = uuid.uuid4()

    await log_action(
        db_session,
        action="test.created",
        resource="thing",
        resource_id=resource_id,
        user_id=user_id,
        tenant_id=tenant_id,
        metadata={"hello": "world", "count": 3},
    )
    await db_session.commit()

    rows = (
        await db_session.execute(
            select(AuditLog).where(AuditLog.resource_id == str(resource_id))
        )
    ).scalars().all()

    assert len(rows) == 1
    row = rows[0]
    assert row.action == "test.created"
    assert row.resource == "thing"
    assert row.tenant_id == tenant_id
    assert row.user_id == user_id
    assert row.extra_metadata == {"hello": "world", "count": 3}


@pytest.mark.asyncio
async def test_log_action_without_metadata_defaults_to_empty_dict(db_session):
    resource_id = uuid.uuid4()
    await log_action(
        db_session,
        action="test.noop",
        resource="thing",
        resource_id=resource_id,
    )
    await db_session.commit()

    row = (
        await db_session.execute(
            select(AuditLog).where(AuditLog.resource_id == str(resource_id))
        )
    ).scalar_one()
    assert row.extra_metadata == {}


@pytest.mark.asyncio
async def test_log_action_swallows_errors(db_session):
    """If the row is somehow invalid, log_action must not raise."""

    class BrokenSession:
        def add(self, _row):
            raise RuntimeError("boom")

        async def flush(self):
            raise RuntimeError("boom")

    await log_action(
        BrokenSession(),
        action="test.fail",
        resource="thing",
    )
