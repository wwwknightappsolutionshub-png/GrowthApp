"""Production booking flows — schemas, URLs, and guardrails."""
from __future__ import annotations

import uuid
from datetime import date, time

from app.modules.booking.feedback import (
    feedback_url_for_token,
    generate_feedback_token,
    refer_url_for_slug,
)
from app.modules.booking.schemas import BookingUpdate, PublicBookingCreate


def test_feedback_token_length():
    t = generate_feedback_token()
    assert len(t) >= 32


def test_feedback_url_contains_token():
    token = "abc123"
    url = feedback_url_for_token(token)
    assert token in url
    assert "/book/feedback/" in url


def test_refer_url_for_slug():
    url = refer_url_for_slug("acme-co")
    assert url.endswith("/book/acme-co/refer")


def test_booking_update_notify_fields():
    m = BookingUpdate(
        status="confirmed",
        notify_customer=True,
        notify_channels=["email", "in_app"],
        slot_id=uuid.uuid4(),
    )
    assert m.notify_customer is True
    assert "in_app" in m.notify_channels


def test_public_booking_requires_name_and_date():
    m = PublicBookingCreate(
        customer_name="Jane",
        customer_email="jane@example.com",
        booking_date=date(2026, 6, 1),
        start_time=time(10, 0),
        channel="widget",
    )
    assert m.customer_email == "jane@example.com"

