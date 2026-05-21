"""CRM enterprise integration tests (Phase 6 QA)."""
from __future__ import annotations

import uuid
from datetime import date, time
from unittest.mock import AsyncMock

import pytest
from sqlalchemy import select

from app.modules.automation.models import Automation, AutomationRun, AutomationStep
from app.modules.booking.models import Booking
from app.modules.crm.enterprise_schemas import ActivityCreate
from app.modules.crm import enterprise_service, pipeline_service
from app.modules.crm.models import Customer, Deal
from app.modules.crm.pipeline_models import CrmActivity
from app.modules.leads.models import Lead
from app.modules.messaging.models import Conversation, Message
from app.modules.tenants.models import Tenant


async def _make_tenant(db_session, suffix: str) -> Tenant:
    t = Tenant(
        id=uuid.uuid4(),
        slug=f"crm-qa-{suffix}-{uuid.uuid4().hex[:6]}",
        name=f"CRM QA {suffix}",
        business_type="plumber",
        postcode="SW1A1AA",
    )
    db_session.add(t)
    await db_session.commit()
    return t


@pytest.mark.asyncio
async def test_default_pipeline_has_six_stages(db_session):
    tenant = await _make_tenant(db_session, "pipe")
    pipeline = await pipeline_service.ensure_default_pipeline(db_session, tenant.id)
    assert pipeline.is_default is True
    assert len(pipeline.stages) == 6
    names = [s.name for s in sorted(pipeline.stages, key=lambda s: s.position)]
    assert names[0] == "New"
    assert names[-1] == "Lost"


@pytest.mark.asyncio
async def test_move_lead_records_activity_and_enqueues_automation(db_session, monkeypatch):
    enqueued: list[dict] = []

    async def capture_enqueue(name, **kwargs):
        enqueued.append({"name": name, **kwargs})

    monkeypatch.setattr("app.workers.queue.enqueue", capture_enqueue)

    tenant = await _make_tenant(db_session, "move")
    pipeline = await pipeline_service.ensure_default_pipeline(db_session, tenant.id)
    stages = sorted(pipeline.stages, key=lambda s: s.position)
    lead = Lead(
        id=uuid.uuid4(),
        tenant_id=tenant.id,
        first_name="Mover",
        source="web",
        pipeline_id=pipeline.id,
        stage_id=stages[0].id,
    )
    db_session.add(lead)
    await db_session.commit()

    await pipeline_service.move_board_card(
        db_session,
        tenant.id,
        "lead",
        lead.id,
        stages[1].id,
        0,
        user_id=None,
    )

    acts = (
        await db_session.execute(
            select(CrmActivity).where(
                CrmActivity.entity_type == "lead",
                CrmActivity.entity_id == lead.id,
                CrmActivity.activity_type == "stage_changed",
            )
        )
    ).scalars().all()
    assert len(acts) >= 1

    auto_events = [e for e in enqueued if e["name"] == "trigger_automation_for_event"]
    assert any(
        e.get("event") == "lead_stage_changed"
        and e.get("entity_type") == "lead"
        and e.get("entity_id") == str(lead.id)
        for e in auto_events
    )


@pytest.mark.asyncio
async def test_unified_timeline_merges_activity_message_and_automation(db_session):
    tenant = await _make_tenant(db_session, "timeline")
    customer = Customer(
        id=uuid.uuid4(),
        tenant_id=tenant.id,
        first_name="Tim",
        last_name="Line",
        email="tim@example.com",
    )
    db_session.add(customer)
    await db_session.flush()

    await enterprise_service.create_activity(
        db_session,
        tenant.id,
        ActivityCreate(
            entity_type="customer",
            entity_id=customer.id,
            activity_type="note",
            body="Called back",
        ),
        user_id=None,
    )

    conv = Conversation(
        id=uuid.uuid4(),
        tenant_id=tenant.id,
        customer_id=customer.id,
        channel="email",
        customer_email="tim@example.com",
    )
    db_session.add(conv)
    await db_session.flush()
    db_session.add(
        Message(
            id=uuid.uuid4(),
            tenant_id=tenant.id,
            conversation_id=conv.id,
            direction="outbound",
            channel="email",
            subject="Quote follow-up",
            body="Here is your quote",
            status="sent",
        )
    )

    automation = Automation(
        id=uuid.uuid4(),
        tenant_id=tenant.id,
        name="Welcome",
        trigger_event="lead_created",
        is_active=True,
    )
    db_session.add(automation)
    await db_session.flush()
    db_session.add(
        AutomationRun(
            id=uuid.uuid4(),
            tenant_id=tenant.id,
            automation_id=automation.id,
            entity_type="customer",
            entity_id=customer.id,
            status="completed",
        )
    )
    await db_session.commit()

    items = await enterprise_service.get_unified_timeline(
        db_session, tenant.id, "customer", customer.id
    )
    sources = {i.source for i in items}
    assert "activity" in sources
    assert "message" in sources
    assert "automation" in sources


@pytest.mark.asyncio
async def test_customer_bookings_read_only_list(db_session):
    tenant = await _make_tenant(db_session, "book")
    customer = Customer(
        id=uuid.uuid4(),
        tenant_id=tenant.id,
        first_name="Book",
        last_name="Me",
    )
    db_session.add(customer)
    await db_session.flush()
    db_session.add(
        Booking(
            id=uuid.uuid4(),
            tenant_id=tenant.id,
            customer_id=customer.id,
            customer_name="Book Me",
            booking_date=date(2026, 6, 1),
            start_time=time(10, 0),
            status="confirmed",
        )
    )
    await db_session.commit()

    rows = await enterprise_service.list_customer_bookings(db_session, tenant.id, customer.id)
    assert len(rows) == 1
    assert rows[0]["status"] == "confirmed"


@pytest.mark.asyncio
async def test_lead_bookings_via_matching_customer_email(db_session):
    tenant = await _make_tenant(db_session, "leadbook")
    email = "same@example.com"
    customer = Customer(
        id=uuid.uuid4(),
        tenant_id=tenant.id,
        first_name="Cust",
        email=email,
    )
    pipeline = await pipeline_service.ensure_default_pipeline(db_session, tenant.id)
    stage = sorted(pipeline.stages, key=lambda s: s.position)[0]
    lead = Lead(
        id=uuid.uuid4(),
        tenant_id=tenant.id,
        first_name="Lead",
        email=email,
        pipeline_id=pipeline.id,
        stage_id=stage.id,
    )
    db_session.add(customer)
    db_session.add(lead)
    await db_session.flush()
    db_session.add(
        Booking(
            id=uuid.uuid4(),
            tenant_id=tenant.id,
            customer_id=customer.id,
            customer_name="Cust",
            booking_date=date(2026, 7, 1),
            start_time=time(14, 0),
            status="confirmed",
        )
    )
    await db_session.commit()

    rows = await enterprise_service.list_lead_bookings(db_session, tenant.id, lead.id)
    assert len(rows) == 1


@pytest.mark.asyncio
async def test_deal_bookings_via_customer(db_session):
    tenant = await _make_tenant(db_session, "dealbook")
    customer = Customer(
        id=uuid.uuid4(),
        tenant_id=tenant.id,
        first_name="Deal",
        last_name="Cust",
    )
    deal = Deal(
        id=uuid.uuid4(),
        tenant_id=tenant.id,
        customer_id=customer.id,
        title="Kitchen refit",
        stage="Quoted",
        value_pence=50000,
    )
    db_session.add(customer)
    db_session.add(deal)
    await db_session.flush()
    db_session.add(
        Booking(
            id=uuid.uuid4(),
            tenant_id=tenant.id,
            customer_id=customer.id,
            deal_id=deal.id,
            customer_name="Deal Cust",
            booking_date=date(2026, 8, 1),
            start_time=time(9, 0),
            status="confirmed",
        )
    )
    await db_session.commit()

    rows = await enterprise_service.list_deal_bookings(db_session, tenant.id, deal.id)
    assert len(rows) == 1


@pytest.mark.asyncio
async def test_crm_board_http_after_register(client, monkeypatch):
    """Smoke: authenticated owner can list pipelines and load the board."""
    monkeypatch.setattr(
        "app.workers.queue.enqueue",
        AsyncMock(return_value=None),
    )

    email = f"crm-{uuid.uuid4().hex[:6]}@example.com"
    reg = await client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "TestPass123",
            "full_name": "CRM Owner",
            "business_name": "CRM QA Co",
            "business_type": "plumber",
            "postcode": "SW1A 1AA",
        },
    )
    assert reg.status_code == 201
    token = reg.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    pipes = await client.get("/api/v1/crm/pipelines", headers=headers)
    assert pipes.status_code == 200
    data = pipes.json()
    assert len(data) >= 1
    assert any(p.get("is_default") for p in data)

    pid = data[0]["id"]
    board = await client.get(f"/api/v1/crm/board?pipeline_id={pid}", headers=headers)
    assert board.status_code == 200
    body = board.json()
    assert "columns" in body


@pytest.mark.asyncio
async def test_crm_timeline_requires_auth(client):
    res = await client.get(
        "/api/v1/crm/timeline",
        params={"entity_type": "customer", "entity_id": str(uuid.uuid4())},
    )
    assert res.status_code == 401
