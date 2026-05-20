"""Lead Marketplace service layer.

Covers:
  - CRUD for all 6 tables
  - Auto-ingest: receive a cleaned lead → apply quality rules → assign
    category/territory → calculate price → insert into lead_marketplace
  - Lead Distribution Engine:
      Priority = tenant.subscription_level * rule.priority_weight + ai_score
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone, timedelta
from typing import Any

from fastapi import HTTPException
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.lead_marketplace.models import (
    LeadAssignmentRule,
    LeadCategory,
    LeadMarketplace,
    LeadPricing,
    LeadQualityRule,
    LeadTerritory,
)
from app.modules.lead_marketplace.schemas import (
    LeadAssignmentRuleCreate,
    LeadAssignmentRuleUpdate,
    LeadCategoryCreate,
    LeadCategoryUpdate,
    LeadPricingCreate,
    LeadPricingUpdate,
    LeadQualityRuleCreate,
    LeadQualityRuleUpdate,
    LeadTerritoryCreate,
    LeadTerritoryUpdate,
    MarketplaceItemCreate,
    MarketplaceItemDetail,
    MarketplaceItemUpdate,
)


# ── Helper ────────────────────────────────────────────────────────────────────

def _not_found(label: str) -> HTTPException:
    return HTTPException(status_code=404, detail=f"{label} not found")


# ── LeadCategory CRUD ─────────────────────────────────────────────────────────

async def list_categories(db: AsyncSession) -> list[LeadCategory]:
    return list((await db.execute(select(LeadCategory).order_by(LeadCategory.name))).scalars())


async def create_category(db: AsyncSession, body: LeadCategoryCreate) -> LeadCategory:
    row = LeadCategory(**body.model_dump())
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return row


async def get_category(db: AsyncSession, cat_id: uuid.UUID) -> LeadCategory:
    row = (await db.execute(select(LeadCategory).where(LeadCategory.id == cat_id))).scalar_one_or_none()
    if not row:
        raise _not_found("LeadCategory")
    return row


async def update_category(db: AsyncSession, cat_id: uuid.UUID, body: LeadCategoryUpdate) -> LeadCategory:
    row = await get_category(db, cat_id)
    for k, v in body.model_dump(exclude_none=True).items():
        setattr(row, k, v)
    await db.commit()
    await db.refresh(row)
    return row


async def delete_category(db: AsyncSession, cat_id: uuid.UUID) -> None:
    row = await get_category(db, cat_id)
    await db.delete(row)
    await db.commit()


# ── LeadQualityRule CRUD ──────────────────────────────────────────────────────

async def list_quality_rules(db: AsyncSession) -> list[LeadQualityRule]:
    return list((await db.execute(select(LeadQualityRule).order_by(LeadQualityRule.name))).scalars())


async def create_quality_rule(db: AsyncSession, body: LeadQualityRuleCreate) -> LeadQualityRule:
    row = LeadQualityRule(**body.model_dump())
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return row


async def get_quality_rule(db: AsyncSession, rule_id: uuid.UUID) -> LeadQualityRule:
    row = (await db.execute(select(LeadQualityRule).where(LeadQualityRule.id == rule_id))).scalar_one_or_none()
    if not row:
        raise _not_found("LeadQualityRule")
    return row


async def update_quality_rule(db: AsyncSession, rule_id: uuid.UUID, body: LeadQualityRuleUpdate) -> LeadQualityRule:
    row = await get_quality_rule(db, rule_id)
    for k, v in body.model_dump(exclude_none=True).items():
        setattr(row, k, v)
    await db.commit()
    await db.refresh(row)
    return row


async def delete_quality_rule(db: AsyncSession, rule_id: uuid.UUID) -> None:
    row = await get_quality_rule(db, rule_id)
    await db.delete(row)
    await db.commit()


# ── LeadPricing CRUD ──────────────────────────────────────────────────────────

async def list_pricing(db: AsyncSession) -> list[LeadPricing]:
    return list((await db.execute(select(LeadPricing).order_by(LeadPricing.created_at))).scalars())


async def create_pricing(db: AsyncSession, body: LeadPricingCreate) -> LeadPricing:
    row = LeadPricing(**body.model_dump())
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return row


async def get_pricing(db: AsyncSession, pricing_id: uuid.UUID) -> LeadPricing:
    row = (await db.execute(select(LeadPricing).where(LeadPricing.id == pricing_id))).scalar_one_or_none()
    if not row:
        raise _not_found("LeadPricing")
    return row


async def update_pricing(db: AsyncSession, pricing_id: uuid.UUID, body: LeadPricingUpdate) -> LeadPricing:
    row = await get_pricing(db, pricing_id)
    for k, v in body.model_dump(exclude_none=True).items():
        setattr(row, k, v)
    await db.commit()
    await db.refresh(row)
    return row


async def delete_pricing(db: AsyncSession, pricing_id: uuid.UUID) -> None:
    row = await get_pricing(db, pricing_id)
    await db.delete(row)
    await db.commit()


# ── LeadTerritory CRUD ────────────────────────────────────────────────────────

async def list_territories(db: AsyncSession) -> list[LeadTerritory]:
    return list((await db.execute(select(LeadTerritory).order_by(LeadTerritory.name))).scalars())


async def create_territory(db: AsyncSession, body: LeadTerritoryCreate) -> LeadTerritory:
    row = LeadTerritory(**body.model_dump())
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return row


async def get_territory(db: AsyncSession, territory_id: uuid.UUID) -> LeadTerritory:
    row = (await db.execute(select(LeadTerritory).where(LeadTerritory.id == territory_id))).scalar_one_or_none()
    if not row:
        raise _not_found("LeadTerritory")
    return row


async def update_territory(db: AsyncSession, territory_id: uuid.UUID, body: LeadTerritoryUpdate) -> LeadTerritory:
    row = await get_territory(db, territory_id)
    for k, v in body.model_dump(exclude_none=True).items():
        setattr(row, k, v)
    await db.commit()
    await db.refresh(row)
    return row


async def delete_territory(db: AsyncSession, territory_id: uuid.UUID) -> None:
    row = await get_territory(db, territory_id)
    await db.delete(row)
    await db.commit()


# ── LeadAssignmentRule CRUD ───────────────────────────────────────────────────

async def list_assignment_rules(db: AsyncSession) -> list[LeadAssignmentRule]:
    return list((await db.execute(select(LeadAssignmentRule).order_by(LeadAssignmentRule.rule_name))).scalars())


async def create_assignment_rule(db: AsyncSession, body: LeadAssignmentRuleCreate) -> LeadAssignmentRule:
    row = LeadAssignmentRule(**body.model_dump())
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return row


async def get_assignment_rule(db: AsyncSession, rule_id: uuid.UUID) -> LeadAssignmentRule:
    row = (await db.execute(select(LeadAssignmentRule).where(LeadAssignmentRule.id == rule_id))).scalar_one_or_none()
    if not row:
        raise _not_found("LeadAssignmentRule")
    return row


async def update_assignment_rule(db: AsyncSession, rule_id: uuid.UUID, body: LeadAssignmentRuleUpdate) -> LeadAssignmentRule:
    row = await get_assignment_rule(db, rule_id)
    for k, v in body.model_dump(exclude_none=True).items():
        setattr(row, k, v)
    await db.commit()
    await db.refresh(row)
    return row


async def delete_assignment_rule(db: AsyncSession, rule_id: uuid.UUID) -> None:
    row = await get_assignment_rule(db, rule_id)
    await db.delete(row)
    await db.commit()


# ── Marketplace Inventory CRUD ────────────────────────────────────────────────

async def list_marketplace(
    db: AsyncSession,
    status: str | None = None,
    category_id: uuid.UUID | None = None,
    territory_id: uuid.UUID | None = None,
    limit: int = 200,
    offset: int = 0,
) -> list[MarketplaceItemDetail]:
    from app.modules.lead_marketplace.models import LeadCategory, LeadTerritory
    q = select(LeadMarketplace).order_by(LeadMarketplace.created_at.desc())
    if status:
        q = q.where(LeadMarketplace.status == status)
    if category_id:
        q = q.where(LeadMarketplace.category_id == category_id)
    if territory_id:
        q = q.where(LeadMarketplace.territory_id == territory_id)
    q = q.limit(limit).offset(offset)
    rows = list((await db.execute(q)).scalars())

    # Load category/territory names in bulk
    cat_ids = {r.category_id for r in rows}
    ter_ids = {r.territory_id for r in rows}

    cats: dict[uuid.UUID, str] = {}
    if cat_ids:
        for c in (await db.execute(select(LeadCategory).where(LeadCategory.id.in_(cat_ids)))).scalars():
            cats[c.id] = c.name

    ters: dict[uuid.UUID, str] = {}
    if ter_ids:
        for t in (await db.execute(select(LeadTerritory).where(LeadTerritory.id.in_(ter_ids)))).scalars():
            ters[t.id] = t.name

    out: list[MarketplaceItemDetail] = []
    for r in rows:
        d = MarketplaceItemDetail.model_validate(r)
        d.category_name = cats.get(r.category_id)
        d.territory_name = ters.get(r.territory_id)
        out.append(d)
    return out


async def get_marketplace_item(db: AsyncSession, item_id: uuid.UUID) -> LeadMarketplace:
    row = (await db.execute(select(LeadMarketplace).where(LeadMarketplace.id == item_id))).scalar_one_or_none()
    if not row:
        raise _not_found("LeadMarketplace item")
    return row


async def create_marketplace_item(db: AsyncSession, body: MarketplaceItemCreate) -> LeadMarketplace:
    row = LeadMarketplace(**body.model_dump())
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return row


async def update_marketplace_item(db: AsyncSession, item_id: uuid.UUID, body: MarketplaceItemUpdate) -> LeadMarketplace:
    row = await get_marketplace_item(db, item_id)
    for k, v in body.model_dump(exclude_none=True).items():
        setattr(row, k, v)
    await db.commit()
    await db.refresh(row)
    return row


async def delete_marketplace_item(db: AsyncSession, item_id: uuid.UUID) -> None:
    row = await get_marketplace_item(db, item_id)
    await db.delete(row)
    await db.commit()


async def assign_marketplace_item(
    db: AsyncSession,
    item_id: uuid.UUID,
    tenant_id: uuid.UUID,
    status: str = "reserved",
) -> LeadMarketplace:
    row = await get_marketplace_item(db, item_id)
    if row.status not in ("available", "reserved"):
        raise HTTPException(status_code=409, detail=f"Cannot assign a lead with status '{row.status}'")
    row.assigned_tenant_id = tenant_id
    row.status = status
    await db.commit()
    await db.refresh(row)
    return row


async def release_marketplace_item(db: AsyncSession, item_id: uuid.UUID) -> LeadMarketplace:
    """Release a reserved lead back to 'available'."""
    row = await get_marketplace_item(db, item_id)
    if row.status not in ("reserved",):
        raise HTTPException(status_code=409, detail=f"Only reserved leads can be released (current: '{row.status}')")
    row.status = "available"
    row.assigned_tenant_id = None
    await db.commit()
    await db.refresh(row)
    return row


async def mark_sold(db: AsyncSession, item_id: uuid.UUID) -> LeadMarketplace:
    row = await get_marketplace_item(db, item_id)
    row.status = "sold"
    await db.commit()
    await db.refresh(row)
    return row


# ── Auto-ingest pipeline ──────────────────────────────────────────────────────

async def _find_category_by_hint(db: AsyncSession, hint: str | None) -> uuid.UUID | None:
    from app.modules.lead_marketplace.geo import business_type_to_category_name

    if hint:
        hint = business_type_to_category_name(hint)
    """Match a category by name hint (case-insensitive prefix)."""
    if not hint:
        return None
    rows = list((await db.execute(select(LeadCategory))).scalars())
    hint_lower = hint.lower()
    for r in rows:
        if hint_lower in r.name.lower():
            return r.id
    # fallback: first category alphabetically
    if rows:
        rows.sort(key=lambda x: x.name)
        return rows[0].id
    return None


async def _find_territory_by_hint(db: AsyncSession, hint: str | None) -> uuid.UUID | None:
    """Match a territory by region_code or name hint."""
    if not hint:
        return None
    rows = list((await db.execute(select(LeadTerritory))).scalars())
    hint_lower = hint.lower()
    for r in rows:
        if hint_lower in r.region_code.lower() or hint_lower in r.name.lower():
            return r.id
    if rows:
        rows.sort(key=lambda x: x.name)
        return rows[0].id
    return None


async def _calculate_price(
    db: AsyncSession,
    category_id: uuid.UUID,
    ai_score: int,
    exclusivity: str,
) -> float:
    """Apply pricing rules for a category. Falls back to 0 if no rule exists."""
    row = (await db.execute(
        select(LeadPricing).where(LeadPricing.category_id == category_id)
    )).scalar_one_or_none()
    if not row:
        return 0.0
    price = float(row.base_price)
    if ai_score >= 70:
        price *= float(row.high_quality_multiplier)
    if exclusivity == "exclusive":
        price *= float(row.exclusive_multiplier)
    elif exclusivity == "semi-exclusive":
        price *= (1.0 + (float(row.exclusive_multiplier) - 1.0) / 2.0)
    return round(price, 2)


async def _passes_quality_rules(
    db: AsyncSession,
    category_id: uuid.UUID,
    ai_score: int,
    has_phone: bool,
    has_email: bool,
    lead_age_days: int,
) -> bool:
    """Return True if the lead passes all applicable quality rules."""
    rules = list((await db.execute(
        select(LeadQualityRule).where(
            (LeadQualityRule.apply_to_category == category_id)
            | (LeadQualityRule.apply_to_category.is_(None))
        )
    )).scalars())
    for rule in rules:
        if ai_score < rule.min_ai_score:
            return False
        if lead_age_days > rule.max_age_days:
            return False
        if rule.requires_phone and not has_phone:
            return False
        if rule.requires_email and not has_email:
            return False
    return True


async def ingest_lead_detailed(
    db: AsyncSession,
    lead_id: uuid.UUID,
    ai_score: int,
    category_hint: str | None,
    territory_hint: str | None,
    has_phone: bool = False,
    has_email: bool = False,
    lead_age_days: int = 0,
) -> "MarketplaceIngestResult":
    """
    Auto-ingest pipeline called by the AI scraper worker.

    Returns a structured result so scraper runs can log why ingest was skipped.
    """
    from app.modules.lead_marketplace.ingest_types import MarketplaceIngestResult

    existing = (
        await db.execute(select(LeadMarketplace).where(LeadMarketplace.lead_id == lead_id))
    ).scalar_one_or_none()
    if existing:
        return MarketplaceIngestResult(
            marketplace=existing,
            status="already_listed",
            detail="Lead already has a marketplace row",
        )

    category_id = await _find_category_by_hint(db, category_hint)
    if not category_id:
        return MarketplaceIngestResult(
            marketplace=None,
            status="no_category",
            detail=f"No marketplace category matched hint={category_hint!r}",
        )

    territory_id = await _find_territory_by_hint(db, territory_hint)
    if not territory_id:
        return MarketplaceIngestResult(
            marketplace=None,
            status="no_territory",
            detail=f"No marketplace territory matched hint={territory_hint!r}",
        )

    if not await _passes_quality_rules(
        db, category_id, ai_score, has_phone, has_email, lead_age_days
    ):
        return MarketplaceIngestResult(
            marketplace=None,
            status="quality_failed",
            detail=(
                f"Lead failed quality rules (score={ai_score}, "
                f"phone={has_phone}, email={has_email})"
            ),
        )

    exclusivity: str = "shared"
    price = await _calculate_price(db, category_id, ai_score, exclusivity)

    row = LeadMarketplace(
        id=uuid.uuid4(),
        lead_id=lead_id,
        category_id=category_id,
        territory_id=territory_id,
        ai_score=ai_score,
        price=price,
        exclusivity=exclusivity,
        status="available",
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return MarketplaceIngestResult(
        marketplace=row,
        status="ingested",
        detail=None,
    )


async def ingest_lead(
    db: AsyncSession,
    lead_id: uuid.UUID,
    ai_score: int,
    category_hint: str | None,
    territory_hint: str | None,
    has_phone: bool = False,
    has_email: bool = False,
    lead_age_days: int = 0,
) -> LeadMarketplace | None:
    """Backward-compatible wrapper — returns the marketplace row or None."""
    result = await ingest_lead_detailed(
        db,
        lead_id=lead_id,
        ai_score=ai_score,
        category_hint=category_hint,
        territory_hint=territory_hint,
        has_phone=has_phone,
        has_email=has_email,
        lead_age_days=lead_age_days,
    )
    return result.marketplace


# ── Distribution Engine ───────────────────────────────────────────────────────

async def run_distribution(
    db: AsyncSession,
    marketplace_id: uuid.UUID,
) -> dict[str, Any] | None:
    """
    Distribution Engine for a single marketplace item.

    Priority = tenant.subscription_level * rule.priority_weight + ai_score

    Finds the best-matched tenant based on assignment rules and subscription
    level, then marks the item as reserved for that tenant.

    Returns a dict with assignment details or None if no eligible tenant found.
    """
    from app.modules.tenants.models import Tenant
    from app.modules.billing.models import SubscriptionPlan

    item = await get_marketplace_item(db, marketplace_id)
    if item.status != "available":
        raise HTTPException(status_code=409, detail="Only 'available' leads can be distributed")

    # Load applicable assignment rules (match category/territory or global)
    rules = list((await db.execute(
        select(LeadAssignmentRule).where(
            (
                (LeadAssignmentRule.category_id == item.category_id)
                | (LeadAssignmentRule.category_id.is_(None))
            ) & (
                (LeadAssignmentRule.territory_id == item.territory_id)
                | (LeadAssignmentRule.territory_id.is_(None))
            )
        )
    )).scalars())

    if not rules:
        return None

    # Load all active tenants with their subscription level
    tenants = list((await db.execute(
        select(Tenant).where(Tenant.is_active == True)  # noqa: E712
    )).scalars())

    if not tenants:
        return None

    # Build plan_id → subscription_level lookup
    plan_ids = {t.plan_id for t in tenants if t.plan_id}
    plan_levels: dict[uuid.UUID, int] = {}
    if plan_ids:
        for plan in (await db.execute(
            select(SubscriptionPlan).where(SubscriptionPlan.id.in_(plan_ids))
        )).scalars():
            # Use price_gbp_monthly as the subscription level proxy
            # (e.g. £50 plan = level 50, £200 plan = level 200)
            plan_levels[plan.id] = plan.price_gbp_monthly

    best_priority: float = -1.0
    best_tenant: Tenant | None = None
    best_rule: LeadAssignmentRule | None = None

    for rule in rules:
        for tenant in tenants:
            sub_level = plan_levels.get(tenant.plan_id, 0) if tenant.plan_id else 0
            if sub_level < rule.min_subscription_level:
                continue
            priority = sub_level * rule.priority_weight + item.ai_score
            if priority > best_priority:
                best_priority = priority
                best_tenant = tenant
                best_rule = rule

    if not best_tenant:
        return None

    item.assigned_tenant_id = best_tenant.id
    item.status = "reserved"
    await db.commit()
    await db.refresh(item)

    return {
        "marketplace_id": str(item.id),
        "assigned_tenant_id": str(best_tenant.id),
        "priority_score": best_priority,
        "status": item.status,
    }
