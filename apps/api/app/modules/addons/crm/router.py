"""Industry CRM API — gated by industry_crm add-on."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import CurrentTenantContext
from app.modules.addons.common.constants import FEATURE_INDUSTRY_CRM
from app.modules.addons.common.entitlement import require_addon
from app.modules.addons.crm import service as crm_svc
from app.modules.addons.schemas import MediaTimelineIn, SalonProfileIn

router = APIRouter(
    prefix="/addons/crm",
    tags=["addons-crm"],
    dependencies=[Depends(require_addon(FEATURE_INDUSTRY_CRM))],
)


@router.put("/salon/profile")
async def salon_profile(body: SalonProfileIn, ctx: CurrentTenantContext, db: AsyncSession = Depends(get_db)):
    _, tenant, _ = ctx
    return await crm_svc.upsert_salon_profile(db, tenant, body)


@router.get("/salon/profile/{customer_id}")
async def get_salon(customer_id: uuid.UUID, ctx: CurrentTenantContext, db: AsyncSession = Depends(get_db)):
    _, tenant, _ = ctx
    return await crm_svc.get_salon_profile(db, tenant, customer_id)


@router.post("/salon/media")
async def salon_media(body: MediaTimelineIn, ctx: CurrentTenantContext, db: AsyncSession = Depends(get_db)):
    _, tenant, _ = ctx
    return await crm_svc.add_media(db, tenant, body)


@router.get("/salon/media/{customer_id}")
async def list_media(customer_id: uuid.UUID, ctx: CurrentTenantContext, db: AsyncSession = Depends(get_db)):
    _, tenant, _ = ctx
    return await crm_svc.list_media(db, tenant, customer_id)


@router.post("/salon/rebook/{customer_id}")
async def rebook(customer_id: uuid.UUID, ctx: CurrentTenantContext, db: AsyncSession = Depends(get_db), days: int = 42):
    _, tenant, _ = ctx
    return await crm_svc.schedule_rebook(db, tenant, customer_id, days)


@router.get("/salon/segments")
async def salon_segments(ctx: CurrentTenantContext, db: AsyncSession = Depends(get_db)):
    _, tenant, _ = ctx
    return await crm_svc.list_segments_salon(db, tenant)


@router.get("/garage/vehicles/{vehicle_id}/history")
async def vehicle_history(vehicle_id: uuid.UUID, ctx: CurrentTenantContext, db: AsyncSession = Depends(get_db)):
    _, tenant, _ = ctx
    return await crm_svc.vehicle_history(db, tenant, vehicle_id)


@router.post("/garage/vehicles/{vehicle_id}/predictions")
async def run_predictions(vehicle_id: uuid.UUID, ctx: CurrentTenantContext, db: AsyncSession = Depends(get_db)):
    _, tenant, _ = ctx
    return await crm_svc.run_maintenance_predictions(db, tenant, vehicle_id)


@router.get("/garage/vehicles/{vehicle_id}/predictions")
async def list_predictions(vehicle_id: uuid.UUID, ctx: CurrentTenantContext, db: AsyncSession = Depends(get_db)):
    _, tenant, _ = ctx
    return await crm_svc.list_predictions(db, tenant, vehicle_id)


@router.get("/garage/vehicles/{vehicle_id}/parts-usage")
async def parts_usage(vehicle_id: uuid.UUID, ctx: CurrentTenantContext, db: AsyncSession = Depends(get_db)):
    _, tenant, _ = ctx
    return await crm_svc.parts_usage_history(db, tenant, vehicle_id)


@router.post("/garage/customers/{customer_id}/scores")
async def garage_scores(customer_id: uuid.UUID, ctx: CurrentTenantContext, db: AsyncSession = Depends(get_db)):
    _, tenant, _ = ctx
    return await crm_svc.refresh_garage_scores(db, tenant, customer_id)
