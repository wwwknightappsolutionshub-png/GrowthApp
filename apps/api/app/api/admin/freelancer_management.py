"""Super Admin — Freelancer Management → Billing Inspector.

Allows a super-admin to:
  - View every freelancer's estimated_client_count + calculated_price.
  - Manually override the calculated_price via the optional `override_price`
    field; clearing the override returns the row to the auto-calculated value.

Endpoints
---------
GET   /api/admin/freelancer-management/billings
PATCH /api/admin/freelancer-management/billings/{billing_id}
"""
from __future__ import annotations

from decimal import Decimal
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import SuperAdmin
from app.modules.admin.tool_config import (
    BusinessCategoryConfig,
    FREELANCER_TOOL_HREFS,
    TOOL_LABELS,
)
from app.modules.admin.deletion import active_users_filter
from app.modules.auth.models import User
from app.modules.billing.models import FreelancerBilling


router = APIRouter(
    prefix="/api/admin/freelancer-management",
    tags=["Admin — Freelancer Management"],
)


class FreelancerBillingRow(BaseModel):
    id: UUID
    user_id: UUID
    user_email: str
    user_full_name: str
    estimated_client_count: int
    calculated_price: Decimal
    override_price: Optional[Decimal]
    effective_price: Decimal
    calculation_source: str
    created_at: str


class UpdateOverrideIn(BaseModel):
    """Pass a number to set the override; pass `null` to clear it."""

    override_price: Optional[Decimal] = Field(default=None, ge=0)


class FreelancerModuleVisibilityOut(BaseModel):
    enabled_tools: list[str]
    is_customised: bool
    updated_at: str | None = None


class FreelancerModuleVisibilityUpdate(BaseModel):
    enabled_tools: list[str]


def _row(billing: FreelancerBilling, user: User) -> FreelancerBillingRow:
    effective = billing.override_price if billing.override_price is not None else billing.calculated_price
    return FreelancerBillingRow(
        id=billing.id,
        user_id=billing.user_id,
        user_email=user.email,
        user_full_name=user.full_name,
        estimated_client_count=billing.estimated_client_count,
        calculated_price=billing.calculated_price,
        override_price=billing.override_price,
        effective_price=effective,
        calculation_source=billing.calculation_source,
        created_at=billing.created_at.isoformat() if billing.created_at else "",
    )


def _freelancer_default_tools() -> list[str]:
    return list(FREELANCER_TOOL_HREFS)


def _freelancer_tool_meta() -> list[dict[str, str]]:
    return [
        {"href": href, "label": TOOL_LABELS.get(href, href.replace("/dashboard/", "").replace("-", " ").title())}
        for href in FREELANCER_TOOL_HREFS
    ]


async def _freelancer_visibility_row(db: AsyncSession) -> BusinessCategoryConfig | None:
    return (
        await db.execute(
            select(BusinessCategoryConfig).where(BusinessCategoryConfig.category == "freelancer")
        )
    ).scalar_one_or_none()


def _serialize_visibility(row: BusinessCategoryConfig | None) -> FreelancerModuleVisibilityOut:
    return FreelancerModuleVisibilityOut(
        enabled_tools=list(row.enabled_tools) if row else _freelancer_default_tools(),
        is_customised=row is not None,
        updated_at=row.updated_at.isoformat() if row and row.updated_at else None,
    )


@router.get("/module-visibility/meta")
async def freelancer_module_visibility_meta(_: SuperAdmin):
    return {"tools": _freelancer_tool_meta(), "default_enabled_tools": _freelancer_default_tools()}


@router.get("/module-visibility", response_model=FreelancerModuleVisibilityOut)
async def get_freelancer_module_visibility(
    _: SuperAdmin,
    db: AsyncSession = Depends(get_db),
) -> FreelancerModuleVisibilityOut:
    return _serialize_visibility(await _freelancer_visibility_row(db))


@router.put("/module-visibility", response_model=FreelancerModuleVisibilityOut)
async def update_freelancer_module_visibility(
    body: FreelancerModuleVisibilityUpdate,
    admin: SuperAdmin,
    db: AsyncSession = Depends(get_db),
) -> FreelancerModuleVisibilityOut:
    unknown = [href for href in body.enabled_tools if href not in FREELANCER_TOOL_HREFS]
    if unknown:
        raise HTTPException(status_code=422, detail=f"Unknown freelancer module hrefs: {unknown}")

    row = await _freelancer_visibility_row(db)
    if row:
        row.enabled_tools = body.enabled_tools
        row.updated_by = admin.id
    else:
        row = BusinessCategoryConfig(
            category="freelancer",
            enabled_tools=body.enabled_tools,
            updated_by=admin.id,
        )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return _serialize_visibility(row)


@router.delete("/module-visibility", response_model=FreelancerModuleVisibilityOut)
async def reset_freelancer_module_visibility(
    _: SuperAdmin,
    db: AsyncSession = Depends(get_db),
) -> FreelancerModuleVisibilityOut:
    row = await _freelancer_visibility_row(db)
    if row:
        await db.delete(row)
        await db.commit()
    return _serialize_visibility(None)


@router.get("/billings", response_model=list[FreelancerBillingRow])
async def list_billings(
    _: SuperAdmin,
    db: AsyncSession = Depends(get_db),
) -> list[FreelancerBillingRow]:
    """Every freelancer billing snapshot with the linked user details."""
    result = await db.execute(
        select(FreelancerBilling, User)
        .join(User, User.id == FreelancerBilling.user_id)
        .where(User.user_type == "freelancer", active_users_filter())
        .order_by(FreelancerBilling.created_at.desc())
    )
    return [_row(b, u) for (b, u) in result.all()]


@router.patch("/billings/{billing_id}", response_model=FreelancerBillingRow)
async def update_override(
    billing_id: UUID,
    body: UpdateOverrideIn,
    _: SuperAdmin,
    db: AsyncSession = Depends(get_db),
) -> FreelancerBillingRow:
    """Set `override_price` (or clear it by sending null).

    Setting an override flips `calculation_source` to `"manual"`. Clearing the
    override restores `calculation_source` to `"auto"` — the auto-calculated
    `calculated_price` itself is never mutated.
    """
    billing = (
        await db.execute(select(FreelancerBilling).where(FreelancerBilling.id == billing_id))
    ).scalar_one_or_none()
    if not billing:
        raise HTTPException(status_code=404, detail="Billing row not found")

    user = (
        await db.execute(select(User).where(User.id == billing.user_id))
    ).scalar_one_or_none()
    if not user or user.user_type != "freelancer":
        raise HTTPException(status_code=404, detail="Linked freelancer user not found")

    if body.override_price is None:
        billing.override_price = None
        billing.calculation_source = "auto"
    else:
        billing.override_price = body.override_price
        billing.calculation_source = "manual"

    db.add(billing)
    await db.commit()
    await db.refresh(billing)
    return _row(billing, user)
