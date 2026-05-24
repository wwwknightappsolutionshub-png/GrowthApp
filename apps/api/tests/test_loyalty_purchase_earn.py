"""Tests for product line earning and birthday helpers."""

from datetime import date
from uuid import uuid4

from app.modules.membership_rewards.engines.purchase_earn import (
    birthday_reference_id,
    is_birthday_today,
    points_for_invoice_item,
    product_keyword_bonus,
)
from app.modules.quotes_invoices.models import InvoiceItem


def _item(**kwargs) -> InvoiceItem:
    defaults = {
        "description": "Shampoo",
        "quantity": 2,
        "line_total_pence": 3000,
        "line_kind": "product",
        "unit_price_pence": 1500,
        "vat_rate": 20,
        "sort_order": 0,
    }
    defaults.update(kwargs)
    return InvoiceItem(invoice_id=uuid4(), **defaults)


def test_product_line_uses_product_rules():
    rules = {
        "purchase_per_pound": 5,
        "product_per_pound": 10,
        "product_per_item": 3,
    }
    pts = points_for_invoice_item(_item(), rules)
    # £30 * 10 + 2 * 3 = 306
    assert pts == 306


def test_product_keyword_bonus_matches_description():
    rules = {"product_keywords": {"shampoo": 25, "wax": 10}}
    bonus = product_keyword_bonus(_item(description="Premium Shampoo 500ml"), rules)
    assert bonus == 50


def test_service_line_uses_purchase_per_pound():
    rules = {"purchase_per_pound": 8, "product_per_pound": 20}
    pts = points_for_invoice_item(_item(line_kind="service", line_total_pence=5000), rules)
    assert pts == 400


def test_birthday_reference_is_stable_per_year():
    tenant_id = uuid4()
    customer_id = uuid4()
    a = birthday_reference_id(tenant_id, customer_id, 2026)
    b = birthday_reference_id(tenant_id, customer_id, 2026)
    c = birthday_reference_id(tenant_id, customer_id, 2027)
    assert a == b
    assert a != c


def test_is_birthday_today():
    dob = date(1990, 5, 19)
    assert is_birthday_today(dob, today=date(2026, 5, 19))
    assert not is_birthday_today(dob, today=date(2026, 5, 18))
