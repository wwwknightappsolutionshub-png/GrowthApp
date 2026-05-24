"""Earn-rule resolution and validation."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.membership_rewards.constants import DEFAULT_EARN_RULES
from app.modules.membership_rewards.models import MrPointsLedger
from app.modules.membership_rewards.services.tenant_loyalty_settings import get_or_create_settings


async def earn_rule_amount(db: AsyncSession, tenant_id: uuid.UUID, rule_key: str) -> int:
    settings = await get_or_create_settings(db, tenant_id)
    rules = settings.earn_rules or {}
    try:
        return int(rules.get(rule_key, 0))
    except (TypeError, ValueError):
        return 0


async def membership_signup_bonus_points(db: AsyncSession, tenant_id: uuid.UUID) -> int:
    settings = await get_or_create_settings(db, tenant_id)
    rules = settings.earn_rules or {}
    try:
        raw = rules.get("membership_signup", DEFAULT_EARN_RULES["membership_signup"])
        return max(0, int(raw))
    except (TypeError, ValueError):
        return DEFAULT_EARN_RULES["membership_signup"]


async def has_loyalty_signup_bonus(
    db: AsyncSession, tenant_id: uuid.UUID, customer_id: uuid.UUID
) -> bool:
    row = (
        await db.execute(
            select(MrPointsLedger.id)
            .where(
                MrPointsLedger.tenant_id == tenant_id,
                MrPointsLedger.customer_id == customer_id,
                MrPointsLedger.source == "membership",
                MrPointsLedger.reference_type == "loyalty_signup",
            )
            .limit(1)
        )
    ).scalar_one_or_none()
    return row is not None


def validate_earn_rules(rules: dict) -> dict:
    """Normalize earn_rules payload; preserves product keyword bonuses."""
    out = dict(DEFAULT_EARN_RULES)
    for key, val in (rules or {}).items():
        if key == "product_keywords":
            if isinstance(val, dict):
                cleaned: dict[str, int] = {}
                for k, v in val.items():
                    try:
                        cleaned[str(k)] = max(0, int(v))
                    except (TypeError, ValueError):
                        continue
                out[key] = cleaned
            continue
        try:
            out[key] = max(0, int(val))
        except (TypeError, ValueError):
            continue
    return out
