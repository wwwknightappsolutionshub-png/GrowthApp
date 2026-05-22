"""Booking widget forms, refer-win, and form schema tests."""
from __future__ import annotations

import uuid

import pytest

from app.modules.booking.form_builder import (
    BOOKING_CATEGORIES,
    default_schema_for_category,
    ensure_booking_form_schema,
    extract_schema_payload,
    merge_form_schemas,
    _validate_schema,
    map_submission_to_booking,
)
from app.modules.booking.refer_win import ReferWinSubmitBody


def test_base_slug_from_archived():
    from app.modules.admin.deletion import base_slug_from_archived

    assert base_slug_from_archived("bethel-financial-services-deleted-a0020bb9") == "bethel-financial-services"
    assert base_slug_from_archived("acme-co") is None


def test_extract_schema_payload_accepts_wrapped_schema():
    inner = default_schema_for_category("general")
    wrapped = extract_schema_payload({"schema": inner, "name": "x"})
    assert len(wrapped["fields"]) >= 3


def test_ensure_booking_form_schema_fills_empty():
    empty = ensure_booking_form_schema({"version": 1, "fields": []}, "general")
    assert len(empty["fields"]) >= 3


def test_default_schema_has_system_fields():
    schema = default_schema_for_category("tradesman")
    ids = {f["id"] for f in schema["fields"]}
    assert "customer_name" in ids
    assert "customer_email" in ids


def test_merge_tenant_override():
    base = default_schema_for_category("general")
    override = {
        "version": 1,
        "fields": [{"id": "customer_name", "type": "text", "label": "Full name", "required": True, "order": 0}],
    }
    merged = merge_form_schemas(base, override)
    name_field = next(f for f in merged["fields"] if f["id"] == "customer_name")
    assert name_field["label"] == "Full name"


def test_validate_schema_rejects_duplicate_ids():
    with pytest.raises(ValueError):
        _validate_schema(
            {
                "fields": [
                    {"id": "a", "type": "text", "label": "A"},
                    {"id": "a", "type": "text", "label": "B"},
                ]
            }
        )


def test_map_submission_splits_custom():
    schema = default_schema_for_category("general")
    booking, extras = map_submission_to_booking(
        {
            "customer_name": "Jane",
            "customer_email": "j@example.com",
            "booking_date": "2026-07-01",
            "start_time": "10:00",
            "extra_question": "yes",
        },
        schema,
    )
    assert booking["customer_name"] == "Jane"
    assert extras["intake_responses"]["extra_question"] == "yes"


def test_refer_win_body_validation():
    body = ReferWinSubmitBody(
        referral_name="Sam Referrer",
        referral_phone="+4407700900000",
        referred_phone="+4407700900001",
        referred_email="friend@example.com",
        referral_reason="Great service",
    )
    assert body.referral_name == "Sam Referrer"


def test_booking_categories_list():
    assert "tradesman" in BOOKING_CATEGORIES
    assert "general" in BOOKING_CATEGORIES


@pytest.mark.asyncio
async def test_normalize_public_booking_requires_datetime(db_session):
    import uuid as _uuid

    from app.modules.booking.form_builder import normalize_public_booking_payload

    with pytest.raises(ValueError, match="time"):
        await normalize_public_booking_payload(
            db_session,
            _uuid.uuid4(),
            {"customer_name": "Jane", "customer_email": "j@example.com"},
        )
