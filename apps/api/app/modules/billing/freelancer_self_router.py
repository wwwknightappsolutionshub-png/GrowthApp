"""Freelancer self-service billing — internal pricing page.

GET  /api/v1/freelancer/billing/me   → my current pricing snapshot
PATCH /api/v1/freelancer/billing/me  → update my estimated_client_count
                                       (recalculates price unless an override exists)
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.modules.auth.models import User
from app.modules.billing.freelancer_pricing import calculate_freelancer_price
from app.modules.billing.models import FreelancerBilling

router = APIRouter(
    prefix="/api/v1/freelancer/billing",
    tags=["Freelancer — Billing"],
)


class FreelancerBillingMe(BaseModel):
    user_id: str
    estimated_client_count: int
    calculated_price_gbp: float
    override_price_gbp: float | None
    effective_price_gbp: float
    calculation_source: str
    tier: str  # 1-50 | 51-100 | >100
    next_tier_threshold: int | None
    next_tier_price_gbp: float | None
    updated_at: datetime | None


class UpdateMyClientCount(BaseModel):
    estimated_client_count: int = Field(ge=0, le=10_000)


def _tier(count: int) -> str:
    if count <= 50:
        return "1-50"
    if count <= 100:
        return "51-100"
    return ">100"


def _next_tier(count: int) -> tuple[int | None, Decimal | None]:
    if count <= 50:
        return 51, Decimal("40")
    if count <= 100:
        return 101, calculate_freelancer_price(101)
    return None, None


async def _get_or_create_billing(db: AsyncSession, user: User) -> FreelancerBilling:
    row = (
        await db.execute(
            select(FreelancerBilling).where(FreelancerBilling.user_id == user.id)
        )
    ).scalar_one_or_none()
    if row:
        return row

    count = user.estimated_client_count or 0
    row = FreelancerBilling(
        id=uuid.uuid4(),
        user_id=user.id,
        estimated_client_count=count,
        calculated_price=calculate_freelancer_price(count),
        calculation_source="auto",
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return row


def _serialize(row: FreelancerBilling) -> dict[str, Any]:
    calc = Decimal(str(row.calculated_price or 0))
    override = row.override_price
    effective = override if override is not None else calc
    nxt_count, nxt_price = _next_tier(int(row.estimated_client_count or 0))
    return {
        "user_id": str(row.user_id),
        "estimated_client_count": int(row.estimated_client_count or 0),
        "calculated_price_gbp": float(calc),
        "override_price_gbp": float(override) if override is not None else None,
        "effective_price_gbp": float(effective),
        "calculation_source": row.calculation_source,
        "tier": _tier(int(row.estimated_client_count or 0)),
        "next_tier_threshold": nxt_count,
        "next_tier_price_gbp": float(nxt_price) if nxt_price is not None else None,
        "updated_at": None,  # FreelancerBilling has no updated_at yet
    }


@router.get("/me", response_model=FreelancerBillingMe)
async def my_billing(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if current_user.user_type != "freelancer":
        raise HTTPException(403, "Only freelancers can view this page.")
    row = await _get_or_create_billing(db, current_user)
    return _serialize(row)


@router.patch("/me", response_model=FreelancerBillingMe)
async def update_client_count(
    body: UpdateMyClientCount,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Freelancer self-updates their estimated client count.

    Recalculates `calculated_price`. Manual `override_price` is preserved as-is
    — the Super Admin's override remains the effective price.
    """
    if current_user.user_type != "freelancer":
        raise HTTPException(403, "Only freelancers can update this.")
    row = await _get_or_create_billing(db, current_user)
    row.estimated_client_count = body.estimated_client_count
    row.calculated_price = calculate_freelancer_price(body.estimated_client_count)
    # If there was no manual override, leave calculation_source=auto.
    if row.override_price is None:
        row.calculation_source = "auto"
    current_user.estimated_client_count = body.estimated_client_count
    db.add(row)
    db.add(current_user)
    await db.commit()
    await db.refresh(row)
    return _serialize(row)
