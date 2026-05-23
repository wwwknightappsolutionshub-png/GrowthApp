"""Industry booking API — gated by industry_booking add-on."""

from __future__ import annotations

import uuid
from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import CurrentTenantContext
from app.modules.addons.booking import service as booking_svc
from app.modules.addons.common.constants import FEATURE_INDUSTRY_BOOKING
from app.modules.addons.common.entitlement import require_addon
from app.modules.addons.schemas import (
    MechanicSkillIn,
    MultiServiceSessionCreate,
    PartsInventoryIn,
    ProductCatalogIn,
    ResourceAllocateIn,
    ServiceSkillIn,
    StaffSkillIn,
    UpsellLineIn,
    VehicleEstimateIn,
    VehicleIn,
)

router = APIRouter(
    prefix="/addons/booking",
    tags=["addons-booking"],
    dependencies=[Depends(require_addon(FEATURE_INDUSTRY_BOOKING))],
)


@router.post("/sessions")
async def multi_service_session(body: MultiServiceSessionCreate, ctx: CurrentTenantContext, db: AsyncSession = Depends(get_db)):
    _, tenant, _ = ctx
    return await booking_svc.set_multi_service_session(db, tenant, body)


@router.post("/staff-skills")
async def staff_skill(body: StaffSkillIn, ctx: CurrentTenantContext, db: AsyncSession = Depends(get_db)):
    _, tenant, _ = ctx
    return await booking_svc.upsert_staff_skill(db, tenant, body)


@router.post("/service-skills")
async def service_skill(body: ServiceSkillIn, ctx: CurrentTenantContext, db: AsyncSession = Depends(get_db)):
    _, tenant, _ = ctx
    return await booking_svc.upsert_service_skill(db, tenant, body)


@router.get("/staff/match")
async def staff_match(service_id: uuid.UUID, ctx: CurrentTenantContext, db: AsyncSession = Depends(get_db)):
    _, tenant, _ = ctx
    return await booking_svc.match_staff(db, tenant, service_id)


@router.post("/allocate-resource")
async def allocate_resource(body: ResourceAllocateIn, ctx: CurrentTenantContext, db: AsyncSession = Depends(get_db)):
    _, tenant, _ = ctx
    return await booking_svc.allocate_resource(db, tenant, body)


@router.get("/gap-fill")
async def gap_fill(
    target_date: date,
    ctx: CurrentTenantContext,
    db: AsyncSession = Depends(get_db),
    staff_id: uuid.UUID | None = None,
):
    _, tenant, _ = ctx
    return await booking_svc.gap_fill_suggestions(db, tenant, target_date, staff_id)


@router.post("/{booking_id}/upsells")
async def upsells(booking_id: uuid.UUID, body: UpsellLineIn, ctx: CurrentTenantContext, db: AsyncSession = Depends(get_db)):
    _, tenant, _ = ctx
    return await booking_svc.add_upsell(db, tenant, booking_id, body)


@router.get("/{booking_id}/upsells")
async def list_upsells(booking_id: uuid.UUID, ctx: CurrentTenantContext, db: AsyncSession = Depends(get_db)):
    _, tenant, _ = ctx
    return await booking_svc.list_upsells(db, tenant, booking_id)


@router.post("/products")
async def create_product(body: ProductCatalogIn, ctx: CurrentTenantContext, db: AsyncSession = Depends(get_db)):
    _, tenant, _ = ctx
    return await booking_svc.create_product(db, tenant, body)


@router.get("/products")
async def list_products(ctx: CurrentTenantContext, db: AsyncSession = Depends(get_db)):
    _, tenant, _ = ctx
    return await booking_svc.list_products(db, tenant)


@router.post("/mechanic-skills")
async def mechanic_skill(body: MechanicSkillIn, ctx: CurrentTenantContext, db: AsyncSession = Depends(get_db)):
    _, tenant, _ = ctx
    return await booking_svc.upsert_mechanic_skill(db, tenant, body)


@router.get("/mechanics/match")
async def mechanic_match(
    specialization: str,
    ctx: CurrentTenantContext,
    db: AsyncSession = Depends(get_db),
):
    _, tenant, _ = ctx
    return await booking_svc.match_mechanics(db, tenant, specialization)


@router.get("/estimate-duration")
async def estimate_duration(
    make: str, model: str, service_code: str, ctx: CurrentTenantContext, db: AsyncSession = Depends(get_db)
):
    _, tenant, _ = ctx
    return await booking_svc.estimate_duration(db, tenant, make, model, service_code)


@router.post("/estimates")
async def save_estimate(body: VehicleEstimateIn, ctx: CurrentTenantContext, db: AsyncSession = Depends(get_db)):
    _, tenant, _ = ctx
    return await booking_svc.save_estimate(db, tenant, body)


@router.post("/parts")
async def upsert_parts(body: PartsInventoryIn, ctx: CurrentTenantContext, db: AsyncSession = Depends(get_db)):
    _, tenant, _ = ctx
    return await booking_svc.upsert_parts(db, tenant, body)


@router.get("/parts")
async def list_parts(ctx: CurrentTenantContext, db: AsyncSession = Depends(get_db)):
    _, tenant, _ = ctx
    return await booking_svc.list_parts(db, tenant)


@router.post("/{booking_id}/check-parts")
async def check_parts(
    booking_id: uuid.UUID,
    parts: list[dict],
    ctx: CurrentTenantContext,
    db: AsyncSession = Depends(get_db),
):
    _, tenant, _ = ctx
    return await booking_svc.check_parts_for_booking(db, tenant, booking_id, parts)


@router.post("/vehicles")
async def register_vehicle(body: VehicleIn, ctx: CurrentTenantContext, db: AsyncSession = Depends(get_db)):
    _, tenant, _ = ctx
    return await booking_svc.register_vehicle(db, tenant, body)


@router.get("/vehicles")
async def list_vehicles(
    ctx: CurrentTenantContext,
    db: AsyncSession = Depends(get_db),
    customer_id: uuid.UUID | None = None,
):
    _, tenant, _ = ctx
    return await booking_svc.list_vehicles(db, tenant, customer_id)
