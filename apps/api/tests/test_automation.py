"""Automation module tests — presets, routing, and send execution."""
import uuid
from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient

from app.modules.automation import presets
from app.modules.automation.execution import render_template, AutomationContext
from app.modules.automation.models import Automation, AutomationRun
from app.modules.leads.models import Lead
from app.modules.tenants.models import Tenant


async def _register(client: AsyncClient) -> str:
    email = f"auto-{uuid.uuid4().hex[:8]}@example.com"
    res = await client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "TestPass123",
            "full_name": "Auto Tester",
            "business_name": f"Auto Co {uuid.uuid4().hex[:6]}",
            "business_type": "plumber",
            "postcode": "SW1A 1AA",
        },
    )
    assert res.status_code == 201, res.text
    return res.json()["access_token"]


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
async def tenant(db_session):
    tenant = Tenant(
        id=uuid.uuid4(),
        slug=f"test-{uuid.uuid4().hex[:8]}",
        name="Test Business",
        business_type="plumber",
        postcode="SW1A 1AA",
    )
    db_session.add(tenant)
    await db_session.commit()
    await db_session.refresh(tenant)
    return tenant


@pytest.mark.asyncio
async def test_render_template_tokens():
    tenant = Tenant(
        id=uuid.uuid4(),
        slug="acme",
        name="Acme Plumbing",
        business_type="trades",
        postcode="M1 1AA",
        phone="+441234567890",
    )
    ctx = AutomationContext(
        first_name="Jane",
        last_name="Doe",
        tokens={"{{quote_url}}": "https://example.com/quote/abc"},
    )
    out = render_template(
        "Hi {{first_name}}, quote: {{quote_url}} — {{business_name}}",
        ctx,
        tenant,
    )
    assert "Jane" in out
    assert "Acme Plumbing" in out
    assert "https://example.com/quote/abc" in out


@pytest.mark.asyncio
async def test_automation_presets_list_uninstalled(db_session, tenant):
    available = await presets.list_available_presets(db_session, tenant.id)
    assert len(available) == 3
    assert all(not p["installed"] for p in available)


@pytest.mark.asyncio
async def test_install_all_presets(db_session, tenant):
    installed = await presets.install_all_presets(db_session, tenant.id)
    assert len(installed) == 3
    available = await presets.list_available_presets(db_session, tenant.id)
    assert all(p["installed"] for p in available)


@pytest.mark.asyncio
async def test_templates_route_before_uuid(client: AsyncClient):
    token = await _register(client)
    res = await client.get("/api/v1/automations/templates", headers=_auth(token))
    assert res.status_code == 200
    assert isinstance(res.json(), list)


@pytest.mark.asyncio
async def test_execute_send_sms(db_session, tenant):
    from app.modules.automation.execution import execute_send_step

    lead = Lead(
        id=uuid.uuid4(),
        tenant_id=tenant.id,
        first_name="Sam",
        phone="+447700900123",
        source="web_form",
    )
    db_session.add(lead)
    await db_session.commit()

    mock_adapter = AsyncMock()
    mock_adapter.send = AsyncMock(return_value=type("R", (), {"status": "sent"})())

    with patch("app.modules.automation.execution.get_sms_adapter", return_value=mock_adapter):
        await execute_send_step(
            db_session,
            tenant_id=tenant.id,
            entity_type="lead",
            entity_id=lead.id,
            action="send_sms",
            config={"body": "Hi {{first_name}} from {{business_name}}"},
        )

    mock_adapter.send.assert_awaited_once()
    sent = mock_adapter.send.await_args[0][0]
    assert "Sam" in sent.body


@pytest.mark.asyncio
async def test_run_exists_for_entity(db_session, tenant):
    from app.modules.automation import service
    from app.modules.automation.models import Automation, AutomationRun

    automation = Automation(
        id=uuid.uuid4(),
        tenant_id=tenant.id,
        name="Test",
        trigger_event="lead_created",
        is_active=True,
    )
    db_session.add(automation)
    await db_session.flush()
    entity_id = uuid.uuid4()
    db_session.add(
        AutomationRun(
            id=uuid.uuid4(),
            tenant_id=tenant.id,
            automation_id=automation.id,
            entity_type="lead",
            entity_id=entity_id,
            status="running",
        )
    )
    await db_session.commit()

    assert await service.run_exists_for_entity(db_session, automation.id, entity_id) is True
    assert await service.run_exists_for_entity(db_session, automation.id, uuid.uuid4()) is False
