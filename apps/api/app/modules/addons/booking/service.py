"""Industry booking: salon + garage."""

from __future__ import annotations

import uuid
from datetime import date, datetime, time, timedelta, timezone
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequestException, NotFoundException
from app.modules.addons.common.constants import Vertical
from app.modules.addons.common.vertical import get_tenant_vertical
from app.modules.addons.industry_models import (
    BookingPartsReservation,
    BookingProductCatalog,
    BookingResourceAllocation,
    BookingSessionService,
    BookingUpsellLine,
    MechanicSkill,
    PartsInventory,
    ServiceRequiredSkill,
    StaffSkill,
    Vehicle,
    VehicleServiceEstimate,
)
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
from app.modules.booking.enterprise_models import BookingResource, BookingService
from app.modules.booking.models import Booking, Staff
from app.modules.tenants.models import Tenant


async def _vertical(db: AsyncSession, tenant: Tenant) -> Vertical:
    v = await get_tenant_vertical(db, tenant)
    if v not in (Vertical.SALON, Vertical.GARAGE):
        raise BadRequestException("Industry booking requires salon or garage vertical.")
    return v


async def set_multi_service_session(
    db: AsyncSession, tenant: Tenant, payload: MultiServiceSessionCreate
) -> list[dict[str, Any]]:
    await _vertical(db, tenant)
    booking = await _booking(db, tenant.id, payload.booking_id)
    await db.execute(
        delete(BookingSessionService).where(
            BookingSessionService.tenant_id == tenant.id,
            BookingSessionService.booking_id == booking.id,
        )
    )
    rows = []
    for i, s in enumerate(payload.services):
        row = BookingSessionService(
            tenant_id=tenant.id,
            booking_id=booking.id,
            service_id=s.service_id,
            sort_order=s.sort_order or i,
            duration_minutes=s.duration_minutes,
        )
        db.add(row)
        rows.append(row)
    total_mins = sum(r.duration_minutes or 60 for r in rows)
    booking.duration_minutes = total_mins
    await db.commit()
    return [{"service_id": str(r.service_id), "sort_order": r.sort_order} for r in rows]


async def upsert_staff_skill(db: AsyncSession, tenant: Tenant, payload: StaffSkillIn) -> dict:
    await _vertical(db, tenant)
    row = StaffSkill(
        tenant_id=tenant.id,
        staff_id=payload.staff_id,
        skill_code=payload.skill_code.lower(),
        proficiency_level=payload.proficiency_level,
    )
    db.add(row)
    await db.commit()
    return {"id": str(row.id)}


async def upsert_service_skill(db: AsyncSession, tenant: Tenant, payload: ServiceSkillIn) -> dict:
    await _vertical(db, tenant)
    row = ServiceRequiredSkill(
        tenant_id=tenant.id,
        service_id=payload.service_id,
        skill_code=payload.skill_code.lower(),
        min_proficiency=payload.min_proficiency,
    )
    db.add(row)
    await db.commit()
    return {"id": str(row.id)}


async def match_staff(db: AsyncSession, tenant: Tenant, service_id: uuid.UUID) -> list[dict[str, Any]]:
    await _vertical(db, tenant)
    required = (
        await db.execute(
            select(ServiceRequiredSkill).where(
                ServiceRequiredSkill.tenant_id == tenant.id,
                ServiceRequiredSkill.service_id == service_id,
            )
        )
    ).scalars().all()
    staff_list = (
        await db.execute(select(Staff).where(Staff.tenant_id == tenant.id, Staff.is_active.is_(True)))
    ).scalars().all()
    if not required:
        return [{"staff_id": str(s.id), "name": s.name, "match_score": 1.0} for s in staff_list]
    results = []
    for s in staff_list:
        skills = (
            await db.execute(
                select(StaffSkill).where(StaffSkill.tenant_id == tenant.id, StaffSkill.staff_id == s.id)
            )
        ).scalars().all()
        skill_map = {sk.skill_code: sk.proficiency_level for sk in skills}
        ok = all(skill_map.get(r.skill_code, 0) >= r.min_proficiency for r in required)
        score = sum(skill_map.get(r.skill_code, 0) for r in required) / max(len(required), 1)
        if ok:
            results.append({"staff_id": str(s.id), "name": s.name, "match_score": round(score, 2)})
    return sorted(results, key=lambda x: -x["match_score"])


async def allocate_resource(db: AsyncSession, tenant: Tenant, payload: ResourceAllocateIn) -> dict:
    await _vertical(db, tenant)
    booking = await _booking(db, tenant.id, payload.booking_id)
    resource = (
        await db.execute(
            select(BookingResource).where(
                BookingResource.tenant_id == tenant.id,
                BookingResource.id == payload.resource_id,
            )
        )
    ).scalar_one_or_none()
    if not resource:
        raise NotFoundException("Resource not found")
    start = datetime.combine(booking.booking_date, booking.start_time, tzinfo=timezone.utc)
    end = start + timedelta(minutes=booking.duration_minutes or 60)
    row = BookingResourceAllocation(
        tenant_id=tenant.id,
        booking_id=booking.id,
        resource_id=resource.id,
        allocated_from=start,
        allocated_to=end,
    )
    db.add(row)
    booking.resource_id = resource.id
    await db.commit()
    return {"allocation_id": str(row.id), "resource_name": resource.name}


async def gap_fill_suggestions(
    db: AsyncSession, tenant: Tenant, target_date: date, staff_id: uuid.UUID | None = None
) -> list[dict[str, Any]]:
    await _vertical(db, tenant)
    q = select(Booking).where(
        Booking.tenant_id == tenant.id,
        Booking.booking_date == target_date,
        Booking.status.in_(("confirmed", "completed", "in_progress")),
    )
    if staff_id:
        q = q.where(Booking.staff_id == staff_id)
    bookings = (await db.execute(q.order_by(Booking.start_time))).scalars().all()
    gaps: list[dict[str, Any]] = []
    cursor = time(9, 0)
    for b in bookings:
        if b.start_time > cursor:
            gaps.append(
                {
                    "start": cursor.isoformat(),
                    "end": b.start_time.isoformat(),
                    "duration_minutes": _minutes_between(cursor, b.start_time),
                }
            )
        cursor = b.end_time or b.start_time
    if cursor < time(18, 0):
        gaps.append(
            {
                "start": cursor.isoformat(),
                "end": time(18, 0).isoformat(),
                "duration_minutes": _minutes_between(cursor, time(18, 0)),
            }
        )
    return gaps


async def add_upsell(db: AsyncSession, tenant: Tenant, booking_id: uuid.UUID, payload: UpsellLineIn) -> dict:
    await _vertical(db, tenant)
    booking = await _booking(db, tenant.id, booking_id)
    product_id = payload.product_id
    if not product_id:
        prod = (
            await db.execute(
                select(BookingProductCatalog).where(
                    BookingProductCatalog.tenant_id == tenant.id,
                    BookingProductCatalog.name == payload.description,
                )
            )
        ).scalar_one_or_none()
        if not prod:
            raise BadRequestException("product_id required or add product to catalog first")
        product_id = prod.id
    unit = payload.unit_price_pence
    qty = payload.quantity
    row = BookingUpsellLine(
        tenant_id=tenant.id,
        booking_id=booking.id,
        product_id=product_id,
        quantity=qty,
        unit_price_pence=unit,
        line_total_pence=unit * qty,
    )
    db.add(row)
    await db.commit()
    return {"id": str(row.id)}


async def list_upsells(db: AsyncSession, tenant: Tenant, booking_id: uuid.UUID) -> list[dict]:
    await _vertical(db, tenant)
    rows = (
        await db.execute(
            select(BookingUpsellLine).where(
                BookingUpsellLine.tenant_id == tenant.id,
                BookingUpsellLine.booking_id == booking_id,
            )
        )
    ).scalars().all()
    return [{"id": str(r.id), "quantity": r.quantity, "line_total_pence": r.line_total_pence} for r in rows]


async def create_product(db: AsyncSession, tenant: Tenant, payload: ProductCatalogIn) -> dict:
    await _vertical(db, tenant)
    row = BookingProductCatalog(
        tenant_id=tenant.id,
        sku=payload.sku,
        name=payload.name,
        description=payload.description,
        unit_price_pence=payload.unit_price_pence,
    )
    db.add(row)
    await db.commit()
    return {"id": str(row.id)}


async def list_products(db: AsyncSession, tenant: Tenant) -> list[dict]:
    rows = (
        await db.execute(
            select(BookingProductCatalog).where(
                BookingProductCatalog.tenant_id == tenant.id,
                BookingProductCatalog.is_active.is_(True),
            )
        )
    ).scalars().all()
    return [{"id": str(r.id), "sku": r.sku, "name": r.name, "unit_price_pence": r.unit_price_pence} for r in rows]


async def upsert_mechanic_skill(db: AsyncSession, tenant: Tenant, payload: MechanicSkillIn) -> dict:
    if await _vertical(db, tenant) != Vertical.GARAGE:
        raise BadRequestException("Garage vertical only.")
    row = MechanicSkill(
        tenant_id=tenant.id,
        staff_id=payload.staff_id,
        skill_code=payload.specialization.lower(),
        certification_level=str(payload.proficiency_level),
    )
    db.add(row)
    await db.commit()
    return {"id": str(row.id)}


async def match_mechanics(db: AsyncSession, tenant: Tenant, specialization: str) -> list[dict[str, Any]]:
    if await _vertical(db, tenant) != Vertical.GARAGE:
        raise BadRequestException("Garage vertical only.")
    spec = specialization.lower()
    rows = (
        await db.execute(
            select(MechanicSkill, Staff)
            .join(Staff, Staff.id == MechanicSkill.staff_id)
            .where(
                MechanicSkill.tenant_id == tenant.id,
                MechanicSkill.skill_code == spec,
                Staff.is_active.is_(True),
            )
        )
    ).all()
    return [{"staff_id": str(st.id), "name": st.name, "skill": sk.skill_code} for sk, st in rows]


async def estimate_duration(
    db: AsyncSession, tenant: Tenant, make: str, model: str, service_code: str
) -> dict:
    if await _vertical(db, tenant) != Vertical.GARAGE:
        raise BadRequestException("Garage vertical only.")
    row = (
        await db.execute(
            select(VehicleServiceEstimate).where(
                VehicleServiceEstimate.tenant_id == tenant.id,
                VehicleServiceEstimate.make.ilike(make),
                VehicleServiceEstimate.model.ilike(model),
                VehicleServiceEstimate.service_name.ilike(f"%{service_code}%"),
            )
        )
    ).scalar_one_or_none()
    if row:
        return {"duration_minutes": row.estimated_minutes, "source": "catalog"}
    svc = (
        await db.execute(
            select(BookingService).where(
                BookingService.tenant_id == tenant.id,
                BookingService.name.ilike(f"%{service_code}%"),
            )
        )
    ).scalar_one_or_none()
    return {"duration_minutes": svc.duration_minutes if svc else 90, "source": "default"}


async def save_estimate(db: AsyncSession, tenant: Tenant, payload: VehicleEstimateIn) -> dict:
    if await _vertical(db, tenant) != Vertical.GARAGE:
        raise BadRequestException("Garage vertical only.")
    row = VehicleServiceEstimate(
        tenant_id=tenant.id,
        make=payload.make,
        model=payload.model,
        service_name=payload.service_code,
        estimated_minutes=payload.duration_minutes,
    )
    db.add(row)
    await db.commit()
    return {"id": str(row.id)}


async def upsert_parts(db: AsyncSession, tenant: Tenant, payload: PartsInventoryIn) -> dict:
    if await _vertical(db, tenant) != Vertical.GARAGE:
        raise BadRequestException("Garage vertical only.")
    existing = (
        await db.execute(
            select(PartsInventory).where(
                PartsInventory.tenant_id == tenant.id, PartsInventory.sku == payload.sku
            )
        )
    ).scalar_one_or_none()
    if existing:
        existing.name = payload.name
        existing.category = payload.category
        existing.qty_on_hand = payload.quantity_on_hand
        existing.unit_cost_pence = payload.unit_cost_pence
        existing.reorder_level = payload.reorder_level
        await db.commit()
        return {"id": str(existing.id)}
    row = PartsInventory(
        tenant_id=tenant.id,
        sku=payload.sku,
        name=payload.name,
        category=payload.category,
        qty_on_hand=payload.quantity_on_hand,
        unit_cost_pence=payload.unit_cost_pence,
        reorder_level=payload.reorder_level,
    )
    db.add(row)
    await db.commit()
    return {"id": str(row.id)}


async def list_parts(db: AsyncSession, tenant: Tenant) -> list[dict]:
    rows = (
        await db.execute(select(PartsInventory).where(PartsInventory.tenant_id == tenant.id))
    ).scalars().all()
    return [
        {"id": str(r.id), "sku": r.sku, "name": r.name, "qty_on_hand": r.qty_on_hand}
        for r in rows
    ]


async def check_parts_for_booking(
    db: AsyncSession, tenant: Tenant, booking_id: uuid.UUID, parts: list[dict[str, Any]]
) -> dict:
    if await _vertical(db, tenant) != Vertical.GARAGE:
        raise BadRequestException("Garage vertical only.")
    booking = await _booking(db, tenant.id, booking_id)
    shortages = []
    for p in parts:
        sku = p["sku"]
        qty = int(p.get("quantity", 1))
        inv = (
            await db.execute(
                select(PartsInventory).where(
                    PartsInventory.tenant_id == tenant.id, PartsInventory.sku == sku
                )
            )
        ).scalar_one_or_none()
        if not inv or inv.qty_on_hand < qty:
            shortages.append({"sku": sku, "available": inv.qty_on_hand if inv else 0})
            continue
        inv.qty_on_hand -= qty
        db.add(
            BookingPartsReservation(
                tenant_id=tenant.id,
                booking_id=booking.id,
                part_id=inv.id,
                quantity_reserved=qty,
                status="reserved",
            )
        )
    await db.commit()
    return {"approved": len(shortages) == 0, "shortages": shortages}


async def register_vehicle(db: AsyncSession, tenant: Tenant, payload: VehicleIn) -> dict:
    if await _vertical(db, tenant) != Vertical.GARAGE:
        raise BadRequestException("Garage vertical only.")
    row = Vehicle(
        tenant_id=tenant.id,
        customer_id=payload.customer_id,
        vin=payload.vin,
        make=payload.make,
        model=payload.model,
        model_year=payload.year,
        mileage=payload.mileage,
        registration=payload.registration,
    )
    db.add(row)
    await db.commit()
    return {"id": str(row.id)}


async def list_vehicles(db: AsyncSession, tenant: Tenant, customer_id: uuid.UUID | None = None) -> list[dict]:
    q = select(Vehicle).where(Vehicle.tenant_id == tenant.id)
    if customer_id:
        q = q.where(Vehicle.customer_id == customer_id)
    rows = (await db.execute(q)).scalars().all()
    return [
        {
            "id": str(r.id),
            "vin": r.vin,
            "make": r.make,
            "model": r.model,
            "registration": r.registration,
        }
        for r in rows
    ]


async def _booking(db: AsyncSession, tenant_id: uuid.UUID, booking_id: uuid.UUID) -> Booking:
    booking = (
        await db.execute(
            select(Booking).where(Booking.tenant_id == tenant_id, Booking.id == booking_id)
        )
    ).scalar_one_or_none()
    if not booking:
        raise NotFoundException("Booking not found")
    return booking


def _minutes_between(a: time, b: time) -> int:
    return max(int((datetime.combine(date.today(), b) - datetime.combine(date.today(), a)).total_seconds() // 60), 0)
