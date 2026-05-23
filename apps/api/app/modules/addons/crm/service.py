"""Industry CRM: salon + garage."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequestException
from app.modules.addons.common.constants import Vertical
from app.modules.addons.common.vertical import get_tenant_vertical
from app.modules.addons.industry_models import (
    CustomerGarageScore,
    CustomerMediaTimeline,
    CustomerSalonProfile,
    IndustryRebookReminder,
    MaintenancePrediction,
    Vehicle,
    VehiclePartsUsage,
    VehicleServiceRecord,
)
from app.modules.addons.schemas import MediaTimelineIn, SalonProfileIn
from app.modules.crm.models import Customer
from app.modules.quotes_invoices.models import Invoice
from app.modules.tenants.models import Tenant


async def _vertical(db: AsyncSession, tenant: Tenant) -> Vertical:
    v = await get_tenant_vertical(db, tenant)
    if v not in (Vertical.SALON, Vertical.GARAGE):
        raise BadRequestException("Industry CRM requires salon or garage vertical.")
    return v


async def upsert_salon_profile(db: AsyncSession, tenant: Tenant, payload: SalonProfileIn) -> dict:
    if await _vertical(db, tenant) != Vertical.SALON:
        raise BadRequestException("Salon vertical only.")
    row = (
        await db.execute(
            select(CustomerSalonProfile).where(CustomerSalonProfile.customer_id == payload.customer_id)
        )
    ).scalar_one_or_none()
    formula = {"notes": payload.color_formula} if payload.color_formula else {}
    if payload.stylist_notes:
        formula["stylist_notes"] = payload.stylist_notes
    if row:
        row.formula = formula
        row.allergies = payload.allergies
        row.preferences = {"segment_tags": payload.segment_tags}
    else:
        row = CustomerSalonProfile(
            tenant_id=tenant.id,
            customer_id=payload.customer_id,
            formula=formula,
            allergies=payload.allergies,
            preferences={"segment_tags": payload.segment_tags},
        )
        db.add(row)
    await db.commit()
    return {"customer_id": str(payload.customer_id)}


async def get_salon_profile(db: AsyncSession, tenant: Tenant, customer_id: uuid.UUID) -> dict | None:
    if await _vertical(db, tenant) != Vertical.SALON:
        raise BadRequestException("Salon vertical only.")
    row = (
        await db.execute(
            select(CustomerSalonProfile).where(
                CustomerSalonProfile.tenant_id == tenant.id,
                CustomerSalonProfile.customer_id == customer_id,
            )
        )
    ).scalar_one_or_none()
    if not row:
        return None
    return {
        "customer_id": str(customer_id),
        "formula": row.formula,
        "allergies": row.allergies,
        "preferences": row.preferences,
    }


async def add_media(db: AsyncSession, tenant: Tenant, payload: MediaTimelineIn) -> dict:
    if await _vertical(db, tenant) != Vertical.SALON:
        raise BadRequestException("Salon vertical only.")
    row = CustomerMediaTimeline(
        tenant_id=tenant.id,
        customer_id=payload.customer_id,
        media_url=payload.image_url,
        caption=payload.caption,
        taken_at=payload.taken_at or datetime.now(timezone.utc),
    )
    db.add(row)
    await db.commit()
    return {"id": str(row.id)}


async def list_media(db: AsyncSession, tenant: Tenant, customer_id: uuid.UUID) -> list[dict]:
    rows = (
        await db.execute(
            select(CustomerMediaTimeline)
            .where(
                CustomerMediaTimeline.tenant_id == tenant.id,
                CustomerMediaTimeline.customer_id == customer_id,
            )
            .order_by(CustomerMediaTimeline.taken_at.desc())
        )
    ).scalars().all()
    return [{"id": str(r.id), "media_url": r.media_url, "caption": r.caption} for r in rows]


async def schedule_rebook(
    db: AsyncSession, tenant: Tenant, customer_id: uuid.UUID, days_ahead: int = 42
) -> dict:
    if await _vertical(db, tenant) != Vertical.SALON:
        raise BadRequestException("Salon vertical only.")
    due = datetime.now(timezone.utc) + timedelta(days=days_ahead)
    row = IndustryRebookReminder(
        tenant_id=tenant.id,
        customer_id=customer_id,
        due_at=due,
        status="pending",
    )
    db.add(row)
    await db.commit()
    return {"id": str(row.id), "due_at": due.isoformat()}


async def list_segments_salon(db: AsyncSession, tenant: Tenant) -> list[dict]:
    if await _vertical(db, tenant) != Vertical.SALON:
        raise BadRequestException("Salon vertical only.")
    rows = (
        await db.execute(select(CustomerSalonProfile).where(CustomerSalonProfile.tenant_id == tenant.id))
    ).scalars().all()
    tags: dict[str, int] = {}
    for r in rows:
        for t in (r.preferences or {}).get("segment_tags", []):
            tags[t] = tags.get(t, 0) + 1
    return [{"tag": k, "count": v} for k, v in tags.items()]


async def vehicle_history(db: AsyncSession, tenant: Tenant, vehicle_id: uuid.UUID) -> list[dict]:
    if await _vertical(db, tenant) != Vertical.GARAGE:
        raise BadRequestException("Garage vertical only.")
    rows = (
        await db.execute(
            select(VehicleServiceRecord).where(
                VehicleServiceRecord.tenant_id == tenant.id,
                VehicleServiceRecord.vehicle_id == vehicle_id,
            )
        )
    ).scalars().all()
    return [
        {
            "id": str(r.id),
            "service_date": r.service_date.isoformat(),
            "description": r.description,
            "mileage": r.mileage_at_service,
        }
        for r in rows
    ]


async def run_maintenance_predictions(db: AsyncSession, tenant: Tenant, vehicle_id: uuid.UUID) -> list[dict]:
    if await _vertical(db, tenant) != Vertical.GARAGE:
        raise BadRequestException("Garage vertical only.")
    vehicle = await db.get(Vehicle, vehicle_id)
    if not vehicle or vehicle.tenant_id != tenant.id:
        raise BadRequestException("Vehicle not found")
    mileage = vehicle.mileage or 0
    predictions = []
    for label, interval in (("oil_change", 10000), ("brake_check", 20000), ("timing_belt", 60000)):
        due_mileage = ((mileage // interval) + 1) * interval
        row = MaintenancePrediction(
            tenant_id=tenant.id,
            vehicle_id=vehicle_id,
            prediction_type=label,
            due_date=datetime.now(timezone.utc).date() + timedelta(days=90),
            confidence=min(95, 50 + mileage // 1000),
            notes=f"Estimated at {due_mileage} miles",
        )
        db.add(row)
        predictions.append({"type": label, "due_mileage": due_mileage})
    await db.commit()
    return predictions


async def list_predictions(db: AsyncSession, tenant: Tenant, vehicle_id: uuid.UUID) -> list[dict]:
    rows = (
        await db.execute(
            select(MaintenancePrediction).where(
                MaintenancePrediction.tenant_id == tenant.id,
                MaintenancePrediction.vehicle_id == vehicle_id,
            )
        )
    ).scalars().all()
    return [
        {
            "id": str(r.id),
            "prediction_type": r.prediction_type,
            "due_date": r.due_date.isoformat() if r.due_date else None,
            "confidence": r.confidence,
        }
        for r in rows
    ]


async def parts_usage_history(db: AsyncSession, tenant: Tenant, vehicle_id: uuid.UUID) -> list[dict]:
    rows = (
        await db.execute(
            select(VehiclePartsUsage).where(
                VehiclePartsUsage.tenant_id == tenant.id,
                VehiclePartsUsage.vehicle_id == vehicle_id,
            )
        )
    ).scalars().all()
    return [{"id": str(r.id), "part_id": str(r.part_id), "quantity": r.quantity} for r in rows]


async def refresh_garage_scores(db: AsyncSession, tenant: Tenant, customer_id: uuid.UUID) -> dict:
    if await _vertical(db, tenant) != Vertical.GARAGE:
        raise BadRequestException("Garage vertical only.")
    total = (
        await db.execute(
            select(func.coalesce(func.sum(Invoice.total_pence), 0)).where(
                Invoice.tenant_id == tenant.id,
                Invoice.customer_id == customer_id,
                Invoice.status == "paid",
            )
        )
    ).scalar() or 0
    bookings_count = (
        await db.execute(
            select(func.count()).select_from(Vehicle).where(
                Vehicle.tenant_id == tenant.id, Vehicle.customer_id == customer_id
            )
        )
    ).scalar() or 0
    clv = min(100, int(total) // 10000)
    reliability = min(100, 60 + bookings_count * 5)
    row = (
        await db.execute(
            select(CustomerGarageScore).where(CustomerGarageScore.customer_id == customer_id)
        )
    ).scalar_one_or_none()
    if row:
        row.clv_score = clv
        row.reliability_score = reliability
        row.score_metadata = {"lifetime_spend_pence": int(total)}
    else:
        row = CustomerGarageScore(
            tenant_id=tenant.id,
            customer_id=customer_id,
            clv_score=clv,
            reliability_score=reliability,
            score_metadata={"lifetime_spend_pence": int(total)},
        )
        db.add(row)
    await db.commit()
    return {"clv_score": clv, "reliability_score": reliability}
