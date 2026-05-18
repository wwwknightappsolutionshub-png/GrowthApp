"""Lead Marketplace router — all endpoints under /api/superadmin/lead-marketplace.

Every route is gated by SuperAdminDep.
"""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import SuperAdmin
from app.modules.lead_marketplace import service as svc
from app.modules.lead_marketplace.schemas import (
    DistributionResult,
    LeadAssignmentRuleCreate,
    LeadAssignmentRuleResponse,
    LeadAssignmentRuleUpdate,
    LeadCategoryCreate,
    LeadCategoryResponse,
    LeadCategoryUpdate,
    LeadPricingCreate,
    LeadPricingResponse,
    LeadPricingUpdate,
    LeadTerritoryCreate,
    LeadTerritoryResponse,
    LeadTerritoryUpdate,
    LeadQualityRuleCreate,
    LeadQualityRuleResponse,
    LeadQualityRuleUpdate,
    MarketplaceAssignBody,
    MarketplaceItemCreate,
    MarketplaceItemDetail,
    MarketplaceItemResponse,
    MarketplaceItemUpdate,
)

router = APIRouter(
    prefix="/superadmin/lead-marketplace",
    tags=["Lead Marketplace (SuperAdmin)"],
)


# ── Lead Categories ───────────────────────────────────────────────────────────

@router.get("/categories", response_model=list[LeadCategoryResponse])
async def list_categories(_: SuperAdmin, db: AsyncSession = Depends(get_db)):
    return await svc.list_categories(db)


@router.post("/categories", response_model=LeadCategoryResponse, status_code=201)
async def create_category(body: LeadCategoryCreate, _: SuperAdmin, db: AsyncSession = Depends(get_db)):
    return await svc.create_category(db, body)


@router.get("/categories/{cat_id}", response_model=LeadCategoryResponse)
async def get_category(cat_id: uuid.UUID, _: SuperAdmin, db: AsyncSession = Depends(get_db)):
    return await svc.get_category(db, cat_id)


@router.patch("/categories/{cat_id}", response_model=LeadCategoryResponse)
async def update_category(cat_id: uuid.UUID, body: LeadCategoryUpdate, _: SuperAdmin, db: AsyncSession = Depends(get_db)):
    return await svc.update_category(db, cat_id, body)


@router.delete("/categories/{cat_id}", status_code=204)
async def delete_category(cat_id: uuid.UUID, _: SuperAdmin, db: AsyncSession = Depends(get_db)):
    await svc.delete_category(db, cat_id)


# ── Lead Quality Rules ────────────────────────────────────────────────────────

@router.get("/quality-rules", response_model=list[LeadQualityRuleResponse])
async def list_quality_rules(_: SuperAdmin, db: AsyncSession = Depends(get_db)):
    return await svc.list_quality_rules(db)


@router.post("/quality-rules", response_model=LeadQualityRuleResponse, status_code=201)
async def create_quality_rule(body: LeadQualityRuleCreate, _: SuperAdmin, db: AsyncSession = Depends(get_db)):
    return await svc.create_quality_rule(db, body)


@router.get("/quality-rules/{rule_id}", response_model=LeadQualityRuleResponse)
async def get_quality_rule(rule_id: uuid.UUID, _: SuperAdmin, db: AsyncSession = Depends(get_db)):
    return await svc.get_quality_rule(db, rule_id)


@router.patch("/quality-rules/{rule_id}", response_model=LeadQualityRuleResponse)
async def update_quality_rule(rule_id: uuid.UUID, body: LeadQualityRuleUpdate, _: SuperAdmin, db: AsyncSession = Depends(get_db)):
    return await svc.update_quality_rule(db, rule_id, body)


@router.delete("/quality-rules/{rule_id}", status_code=204)
async def delete_quality_rule(rule_id: uuid.UUID, _: SuperAdmin, db: AsyncSession = Depends(get_db)):
    await svc.delete_quality_rule(db, rule_id)


# ── Lead Pricing ──────────────────────────────────────────────────────────────

@router.get("/pricing", response_model=list[LeadPricingResponse])
async def list_pricing(_: SuperAdmin, db: AsyncSession = Depends(get_db)):
    return await svc.list_pricing(db)


@router.post("/pricing", response_model=LeadPricingResponse, status_code=201)
async def create_pricing(body: LeadPricingCreate, _: SuperAdmin, db: AsyncSession = Depends(get_db)):
    return await svc.create_pricing(db, body)


@router.get("/pricing/{pricing_id}", response_model=LeadPricingResponse)
async def get_pricing(pricing_id: uuid.UUID, _: SuperAdmin, db: AsyncSession = Depends(get_db)):
    return await svc.get_pricing(db, pricing_id)


@router.patch("/pricing/{pricing_id}", response_model=LeadPricingResponse)
async def update_pricing(pricing_id: uuid.UUID, body: LeadPricingUpdate, _: SuperAdmin, db: AsyncSession = Depends(get_db)):
    return await svc.update_pricing(db, pricing_id, body)


@router.delete("/pricing/{pricing_id}", status_code=204)
async def delete_pricing(pricing_id: uuid.UUID, _: SuperAdmin, db: AsyncSession = Depends(get_db)):
    await svc.delete_pricing(db, pricing_id)


# ── Lead Territories ──────────────────────────────────────────────────────────

@router.get("/territories", response_model=list[LeadTerritoryResponse])
async def list_territories(_: SuperAdmin, db: AsyncSession = Depends(get_db)):
    return await svc.list_territories(db)


@router.post("/territories", response_model=LeadTerritoryResponse, status_code=201)
async def create_territory(body: LeadTerritoryCreate, _: SuperAdmin, db: AsyncSession = Depends(get_db)):
    return await svc.create_territory(db, body)


@router.get("/territories/{territory_id}", response_model=LeadTerritoryResponse)
async def get_territory(territory_id: uuid.UUID, _: SuperAdmin, db: AsyncSession = Depends(get_db)):
    return await svc.get_territory(db, territory_id)


@router.patch("/territories/{territory_id}", response_model=LeadTerritoryResponse)
async def update_territory(territory_id: uuid.UUID, body: LeadTerritoryUpdate, _: SuperAdmin, db: AsyncSession = Depends(get_db)):
    return await svc.update_territory(db, territory_id, body)


@router.delete("/territories/{territory_id}", status_code=204)
async def delete_territory(territory_id: uuid.UUID, _: SuperAdmin, db: AsyncSession = Depends(get_db)):
    await svc.delete_territory(db, territory_id)


# ── Lead Assignment Rules ─────────────────────────────────────────────────────

@router.get("/assignment-rules", response_model=list[LeadAssignmentRuleResponse])
async def list_assignment_rules(_: SuperAdmin, db: AsyncSession = Depends(get_db)):
    return await svc.list_assignment_rules(db)


@router.post("/assignment-rules", response_model=LeadAssignmentRuleResponse, status_code=201)
async def create_assignment_rule(body: LeadAssignmentRuleCreate, _: SuperAdmin, db: AsyncSession = Depends(get_db)):
    return await svc.create_assignment_rule(db, body)


@router.get("/assignment-rules/{rule_id}", response_model=LeadAssignmentRuleResponse)
async def get_assignment_rule(rule_id: uuid.UUID, _: SuperAdmin, db: AsyncSession = Depends(get_db)):
    return await svc.get_assignment_rule(db, rule_id)


@router.patch("/assignment-rules/{rule_id}", response_model=LeadAssignmentRuleResponse)
async def update_assignment_rule(rule_id: uuid.UUID, body: LeadAssignmentRuleUpdate, _: SuperAdmin, db: AsyncSession = Depends(get_db)):
    return await svc.update_assignment_rule(db, rule_id, body)


@router.delete("/assignment-rules/{rule_id}", status_code=204)
async def delete_assignment_rule(rule_id: uuid.UUID, _: SuperAdmin, db: AsyncSession = Depends(get_db)):
    await svc.delete_assignment_rule(db, rule_id)


# ── Marketplace Inventory ─────────────────────────────────────────────────────

@router.get("/inventory", response_model=list[MarketplaceItemDetail])
async def list_inventory(
    _: SuperAdmin,
    db: AsyncSession = Depends(get_db),
    status: str | None = Query(None),
    category_id: uuid.UUID | None = Query(None),
    territory_id: uuid.UUID | None = Query(None),
    limit: int = Query(200, ge=1, le=1000),
    offset: int = Query(0, ge=0),
):
    return await svc.list_marketplace(db, status=status, category_id=category_id,
                                      territory_id=territory_id, limit=limit, offset=offset)


@router.post("/inventory", response_model=MarketplaceItemResponse, status_code=201)
async def create_inventory_item(body: MarketplaceItemCreate, _: SuperAdmin, db: AsyncSession = Depends(get_db)):
    return await svc.create_marketplace_item(db, body)


@router.get("/inventory/{item_id}", response_model=MarketplaceItemDetail)
async def get_inventory_item(item_id: uuid.UUID, _: SuperAdmin, db: AsyncSession = Depends(get_db)):
    row = await svc.get_marketplace_item(db, item_id)
    items = await svc.list_marketplace(db, limit=1, offset=0)
    # Fetch detail with joined names
    details = await svc.list_marketplace(db, limit=1000, offset=0)
    for d in details:
        if d.id == item_id:
            return d
    return MarketplaceItemDetail.model_validate(row)


@router.patch("/inventory/{item_id}", response_model=MarketplaceItemResponse)
async def update_inventory_item(item_id: uuid.UUID, body: MarketplaceItemUpdate, _: SuperAdmin, db: AsyncSession = Depends(get_db)):
    return await svc.update_marketplace_item(db, item_id, body)


@router.delete("/inventory/{item_id}", status_code=204)
async def delete_inventory_item(item_id: uuid.UUID, _: SuperAdmin, db: AsyncSession = Depends(get_db)):
    await svc.delete_marketplace_item(db, item_id)


@router.post("/inventory/{item_id}/assign", response_model=MarketplaceItemResponse)
async def assign_item(item_id: uuid.UUID, body: MarketplaceAssignBody, _: SuperAdmin, db: AsyncSession = Depends(get_db)):
    """Manually assign a marketplace lead to a tenant (reserve or sell)."""
    return await svc.assign_marketplace_item(db, item_id, body.tenant_id, body.status)


@router.post("/inventory/{item_id}/release", response_model=MarketplaceItemResponse)
async def release_item(item_id: uuid.UUID, _: SuperAdmin, db: AsyncSession = Depends(get_db)):
    """Release a reserved lead back to 'available'."""
    return await svc.release_marketplace_item(db, item_id)


@router.post("/inventory/{item_id}/mark-sold", response_model=MarketplaceItemResponse)
async def mark_item_sold(item_id: uuid.UUID, _: SuperAdmin, db: AsyncSession = Depends(get_db)):
    """Mark a marketplace lead as sold."""
    return await svc.mark_sold(db, item_id)


@router.post("/inventory/{item_id}/distribute", response_model=DistributionResult)
async def distribute_item(item_id: uuid.UUID, _: SuperAdmin, db: AsyncSession = Depends(get_db)):
    """Run the distribution engine on an available marketplace lead."""
    result = await svc.run_distribution(db, item_id)
    if not result:
        from fastapi import HTTPException
        raise HTTPException(status_code=422, detail="No eligible tenant found for distribution")
    return DistributionResult(**result)

