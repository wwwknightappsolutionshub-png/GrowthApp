"""Pricing Engine — calculates lead prices based on rules and quality."""
from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.lead_marketplace.models import LeadPricing, LeadCategory, LeadTerritory


async def calculate_price(
    db: AsyncSession,
    category_id: uuid.UUID,
    territory_id: uuid.UUID,
    ai_score: int,
    has_phone: bool = False,
    has_email: bool = False,
) -> float:
    """Calculate the marketplace price for a lead."""
    pricing = (
        await db.execute(
            select(LeadPricing)
            .where(
                LeadPricing.category_id == category_id,
                LeadPricing.territory_id == territory_id,
                LeadPricing.is_active == True,  # noqa: E712
            )
            .order_by(LeadPricing.updated_at.desc())
            .limit(1)
        )
    ).scalar_one_or_none()

    if not pricing:
        return 0.0

    base = float(pricing.base_price)
    # Score-based multiplier: top-quality leads priced higher
    if ai_score >= 80:
        multiplier = pricing.score_multiplier_high if hasattr(pricing, "score_multiplier_high") else 1.5
    elif ai_score >= 50:
        multiplier = 1.2
    else:
        multiplier = 1.0

    # Contact bonus
    contact_bonus = 0.0
    if has_phone:
        contact_bonus += getattr(pricing, "phone_bonus", 0.0)
    if has_email:
        contact_bonus += getattr(pricing, "email_bonus", 0.0)

    return round(base * multiplier + contact_bonus, 2)


async def get_pricing_rules(db: AsyncSession) -> list[dict]:
    rows = (await db.execute(select(LeadPricing).order_by(LeadPricing.updated_at.desc()))).scalars().all()
    return [
        {
            "id": str(r.id), "category_id": str(r.category_id),
            "territory_id": str(r.territory_id), "base_price": float(r.base_price),
            "is_active": r.is_active,
        }
        for r in rows
    ]
