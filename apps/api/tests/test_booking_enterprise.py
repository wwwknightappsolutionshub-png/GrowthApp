"""Enterprise booking module tests."""
from __future__ import annotations

import uuid
from datetime import date, time

import pytest

from app.modules.booking.enterprise.marketing import generate_manage_token
from app.modules.booking.enterprise_schemas import BookingSettingsUpdate, StaffCreate, StaffShiftCreate
from app.modules.booking.schemas import PublicBookingCreate


def test_generate_manage_token_unique():
    a = generate_manage_token()
    b = generate_manage_token()
    assert a != b
    assert len(a) >= 32


def test_booking_settings_update_schema():
    m = BookingSettingsUpdate(timezone="Europe/London", deposit_enabled=True)
    assert m.timezone == "Europe/London"
    assert m.deposit_enabled is True


def test_staff_create_schema():
    m = StaffCreate(name="Alex Smith", role="staff")
    assert m.name == "Alex Smith"


def test_staff_shift_schema_validates_end_after_start():
    with pytest.raises(ValueError):
        StaffShiftCreate(
            staff_id=uuid.uuid4(),
            shift_date=date.today(),
            start_time=time(17, 0),
            end_time=time(9, 0),
        )


def test_public_booking_create_accepts_channel():
    m = PublicBookingCreate(
        customer_name="Jane Doe",
        booking_date=date(2026, 6, 1),
        start_time=time(10, 0),
        channel="widget",
    )
    assert m.channel == "widget"
