"""Line-item and birthday loyalty point calculations."""

from __future__ import annotations

import uuid
from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.membership_rewards.constants import DEFAULT_EARN_RULES
from app.modules.quotes_invoices.models import InvoiceItem


def _int_rule(rules: dict, key: str, default: int = 0) -> int:
    try:
        return max(0, int(rules.get(key, default)))
    except (TypeError, ValueError):
        return default


def product_keyword_bonus(item: InvoiceItem, rules: dict) -> int:
    raw = rules.get("product_keywords")
    if not isinstance(raw, dict) or not raw:
        return 0
    desc = (item.description or "").lower()
    bonus = 0
    for keyword, points in raw.items():
        try:
            pts = max(0, int(points))
        except (TypeError, ValueError):
            continue
        if keyword and str(keyword).lower() in desc:
            bonus += pts * max(1, item.quantity)
    return bonus


def points_for_invoice_item(item: InvoiceItem, rules: dict) -> int:
    """Compute loyalty points for a single invoice line."""
    rules = rules or {}
    service_per_pound = _int_rule(rules, "purchase_per_pound", DEFAULT_EARN_RULES["purchase_per_pound"])
    product_per_pound = _int_rule(rules, "product_per_pound", DEFAULT_EARN_RULES["product_per_pound"])
    product_per_item = _int_rule(rules, "product_per_item", DEFAULT_EARN_RULES["product_per_item"])

    line_pounds = max(0, item.line_total_pence) // 100
    if (item.line_kind or "service") == "product":
        per_pound = product_per_pound or service_per_pound
        pts = line_pounds * per_pound
        if product_per_item:
            pts += product_per_item * max(1, item.quantity)
        pts += product_keyword_bonus(item, rules)
        return pts

    return line_pounds * service_per_pound


def birthday_reference_id(tenant_id: uuid.UUID, customer_id: uuid.UUID, year: int) -> uuid.UUID:
    return uuid.uuid5(uuid.NAMESPACE_OID, f"{tenant_id}:{customer_id}:birthday:{year}")


def is_birthday_today(dob: date, *, today: date | None = None) -> bool:
    ref = today or date.today()
    return dob.month == ref.month and dob.day == ref.day
