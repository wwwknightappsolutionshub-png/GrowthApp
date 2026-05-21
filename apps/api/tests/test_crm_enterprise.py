"""CRM enterprise API unit tests."""
from __future__ import annotations

import uuid

import pytest

from app.modules.crm.enterprise_schemas import (
    BoardMoveRequest,
    BulkUpdateRequest,
    PipelineCreate,
    StageCreate,
    TimelineItemResponse,
)
from app.modules.crm.pipeline_models import DEFAULT_PIPELINE_STAGES
from app.modules.crm.enterprise_service import _match_condition
from app.modules.leads.models import Lead


def test_default_pipeline_stages_count():
    assert len(DEFAULT_PIPELINE_STAGES) == 6
    assert DEFAULT_PIPELINE_STAGES[0][0] == "New"
    assert DEFAULT_PIPELINE_STAGES[-1][0] == "Lost"


def test_board_move_request_pattern():
    m = BoardMoveRequest(card_type="lead", card_id=uuid.uuid4(), stage_id=uuid.uuid4(), stage_order=1)
    assert m.card_type == "lead"


def test_pipeline_create_schema():
    m = PipelineCreate(name="Service Pipeline", is_default=False)
    assert m.name == "Service Pipeline"


def test_stage_create_schema():
    m = StageCreate(name="Qualified", position=2, is_won=False)
    assert m.position == 2


def test_score_rule_match_eq():
    lead = Lead(
        id=uuid.uuid4(),
        tenant_id=uuid.uuid4(),
        first_name="Jane",
        source="web_form",
    )
    assert _match_condition(lead, {"field": "source", "op": "eq", "value": "web_form"}) is True
    assert _match_condition(lead, {"field": "source", "op": "eq", "value": "referral"}) is False


def test_bulk_update_schema():
    m = BulkUpdateRequest(entity_type="lead", ids=[uuid.uuid4()], updates={"status": "contacted"})
    assert m.entity_type == "lead"


def test_timeline_item_schema():
    from datetime import datetime, timezone

    item = TimelineItemResponse(
        id="message:abc",
        source="message",
        activity_type="email",
        title="Hello",
        body="Test",
        channel="email",
        direction="outbound",
        created_at=datetime.now(timezone.utc),
    )
    assert item.source == "message"
