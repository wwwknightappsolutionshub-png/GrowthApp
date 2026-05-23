from datetime import date

import pytest

from app.modules.quotes_invoices.recurrency import (
    REMINDER_DAYS_BEFORE,
    add_recurrency_period,
    validate_recurrency,
)


def test_validate_recurrency_labels():
    assert validate_recurrency("Yearly") == "yearly"
    assert validate_recurrency("Bi-Yearly") == "bi_yearly"
    assert validate_recurrency("quarterly") == "quarterly"
    assert validate_recurrency(None) is None


def test_add_recurrency_period():
    anchor = date(2026, 1, 15)
    assert add_recurrency_period(anchor, "monthly") == date(2026, 2, 15)
    assert add_recurrency_period(anchor, "quarterly") == date(2026, 4, 15)
    assert add_recurrency_period(anchor, "bi_yearly") == date(2026, 7, 15)
    assert add_recurrency_period(anchor, "yearly") == date(2027, 1, 15)


def test_reminder_lead_days():
    assert REMINDER_DAYS_BEFORE == 7
