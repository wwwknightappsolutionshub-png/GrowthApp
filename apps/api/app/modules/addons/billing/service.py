"""Industry billing: salon + garage."""

from __future__ import annotations

import uuid
from datetime import date, timedelta
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequestException, NotFoundException
from app.modules.addons.common.constants import Vertical
from app.modules.addons.common.vertical import get_tenant_vertical
from app.modules.addons.industry_models import (
    IndustryInvoiceTemplate,
    IndustryServicePackage,
    InvoiceTip,
    InvoiceWarranty,
    Membership,
    MembershipBenefit,
    PackageRedemption,
    PartsMarkupRule,
    Vehicle,
    VehicleServiceRecord,
)
from app.modules.addons.schemas import (
    IndustryInvoiceCreate,
    MarkupRuleIn,
    MembershipIn,
    ServicePackageIn,
    TemplateIn,
    TipIn,
    WarrantyIn,
)
from app.modules.quotes_invoices.models import Invoice, InvoiceItem
from app.modules.quotes_invoices.schemas import InvoiceCreate, QuoteItemIn
from app.modules.quotes_invoices import service as qi_service
from app.modules.tenants.models import Tenant


async def _vertical(db: AsyncSession, tenant: Tenant) -> Vertical:
    v = await get_tenant_vertical(db, tenant)
    if v not in (Vertical.SALON, Vertical.GARAGE):
        raise BadRequestException("Industry billing requires salon or garage vertical.")
    return v


async def create_combo_invoice(db: AsyncSession, tenant: Tenant, payload: IndustryInvoiceCreate) -> dict[str, Any]:
    await _vertical(db, tenant)
    data = InvoiceCreate(
        customer_id=payload.customer_id,
        deal_id=payload.deal_id,
        title=payload.title,
        items=[
            QuoteItemIn(
                description=i.description,
                quantity=i.quantity,
                unit_price_pence=i.unit_price_pence,
                vat_rate=i.vat_rate,
            )
            for i in payload.items
        ],
    )
    inv = await qi_service.create_invoice(db, tenant.id, data)
    items_db = (
        await db.execute(
            select(InvoiceItem)
            .where(InvoiceItem.invoice_id == inv.id)
            .order_by(InvoiceItem.sort_order)
        )
    ).scalars().all()
    for idx, line in enumerate(payload.items):
        if idx < len(items_db):
            items_db[idx].line_kind = line.line_kind
    if payload.vehicle_id:
        rec = VehicleServiceRecord(
            tenant_id=tenant.id,
            vehicle_id=payload.vehicle_id,
            booking_id=payload.booking_id,
            service_date=date.today(),
            description=payload.title,
        )
        db.add(rec)
    await db.commit()
    return await qi_service.get_invoice(db, tenant.id, inv.id)


async def record_tip(db: AsyncSession, tenant: Tenant, payload: TipIn) -> dict:
    await _vertical(db, tenant)
    inv = await _invoice(db, tenant.id, payload.invoice_id)
    row = InvoiceTip(
        tenant_id=tenant.id,
        invoice_id=inv.id,
        amount_pence=payload.amount_pence,
        method=payload.method,
    )
    db.add(row)
    await db.commit()
    return {"id": str(row.id)}


async def create_membership(db: AsyncSession, tenant: Tenant, payload: MembershipIn) -> dict:
    if await _vertical(db, tenant) != Vertical.SALON:
        raise BadRequestException("Salon vertical only.")
    m = Membership(
        tenant_id=tenant.id,
        customer_id=payload.customer_id,
        name=payload.name,
        price_pence=payload.monthly_price_pence,
        status="active",
        started_at=date.today(),
    )
    db.add(m)
    await db.flush()
    for b in payload.benefits:
        db.add(
            MembershipBenefit(
                membership_id=m.id,
                benefit_type="included_service",
                config={"label": b},
            )
        )
    await db.commit()
    return {"id": str(m.id)}


async def list_memberships(db: AsyncSession, tenant: Tenant) -> list[dict]:
    rows = (
        await db.execute(select(Membership).where(Membership.tenant_id == tenant.id))
    ).scalars().all()
    return [{"id": str(r.id), "name": r.name, "price_pence": r.price_pence, "status": r.status} for r in rows]


async def create_service_package(db: AsyncSession, tenant: Tenant, payload: ServicePackageIn) -> dict:
    await _vertical(db, tenant)
    row = IndustryServicePackage(
        tenant_id=tenant.id,
        name=payload.name,
        sessions_included=payload.sessions_included,
        price_pence=payload.price_pence,
        valid_days=payload.valid_days,
    )
    db.add(row)
    await db.commit()
    return {"id": str(row.id)}


async def redeem_package(
    db: AsyncSession, tenant: Tenant, package_id: uuid.UUID, customer_id: uuid.UUID
) -> dict:
    pkg = (
        await db.execute(
            select(IndustryServicePackage).where(
                IndustryServicePackage.tenant_id == tenant.id,
                IndustryServicePackage.id == package_id,
            )
        )
    ).scalar_one_or_none()
    if not pkg:
        raise NotFoundException("Package not found")
    row = PackageRedemption(
        tenant_id=tenant.id,
        package_id=pkg.id,
        customer_id=customer_id,
    )
    db.add(row)
    await db.commit()
    return {"id": str(row.id)}


async def save_template(db: AsyncSession, tenant: Tenant, payload: TemplateIn) -> dict:
    if await _vertical(db, tenant) != Vertical.GARAGE:
        raise BadRequestException("Garage vertical only.")
    row = IndustryInvoiceTemplate(
        tenant_id=tenant.id,
        name=payload.name,
        vertical=payload.vertical,
        template_body={"line_items": payload.line_items},
    )
    db.add(row)
    await db.commit()
    return {"id": str(row.id)}


async def list_templates(db: AsyncSession, tenant: Tenant) -> list[dict]:
    rows = (
        await db.execute(
            select(IndustryInvoiceTemplate).where(IndustryInvoiceTemplate.tenant_id == tenant.id)
        )
    ).scalars().all()
    return [{"id": str(r.id), "name": r.name, "vertical": r.vertical} for r in rows]


async def save_markup_rule(db: AsyncSession, tenant: Tenant, payload: MarkupRuleIn) -> dict:
    if await _vertical(db, tenant) != Vertical.GARAGE:
        raise BadRequestException("Garage vertical only.")
    row = PartsMarkupRule(
        tenant_id=tenant.id, category=payload.category, markup_percent=payload.markup_percent
    )
    db.add(row)
    await db.commit()
    return {"id": str(row.id)}


async def add_warranty(db: AsyncSession, tenant: Tenant, payload: WarrantyIn) -> dict:
    if await _vertical(db, tenant) != Vertical.GARAGE:
        raise BadRequestException("Garage vertical only.")
    inv = await _invoice(db, tenant.id, payload.invoice_id)
    row = InvoiceWarranty(
        tenant_id=tenant.id,
        invoice_id=inv.id,
        warranty_months=payload.months,
        terms=payload.terms,
    )
    db.add(row)
    await db.commit()
    return {"id": str(row.id)}


async def invoices_by_vin(db: AsyncSession, tenant: Tenant, vin: str) -> list[dict]:
    if await _vertical(db, tenant) != Vertical.GARAGE:
        raise BadRequestException("Garage vertical only.")
    vehicle = (
        await db.execute(
            select(Vehicle).where(Vehicle.tenant_id == tenant.id, Vehicle.vin == vin.upper())
        )
    ).scalar_one_or_none()
    if not vehicle:
        return []
    records = (
        await db.execute(
            select(VehicleServiceRecord).where(
                VehicleServiceRecord.tenant_id == tenant.id,
                VehicleServiceRecord.vehicle_id == vehicle.id,
            )
        )
    ).scalars().all()
    booking_ids = [r.booking_id for r in records if r.booking_id]
    if not booking_ids:
        return [{"vehicle_id": str(vehicle.id), "service_records": len(records)}]
    invoices = (
        await db.execute(select(Invoice).where(Invoice.booking_id.in_(booking_ids)))
    ).scalars().all()
    return [
        {"invoice_id": str(i.id), "invoice_number": i.invoice_number, "total_pence": i.total_pence}
        for i in invoices
    ]


async def _invoice(db: AsyncSession, tenant_id: uuid.UUID, invoice_id: uuid.UUID) -> Invoice:
    inv = (
        await db.execute(
            select(Invoice).where(Invoice.tenant_id == tenant_id, Invoice.id == invoice_id)
        )
    ).scalar_one_or_none()
    if not inv:
        raise NotFoundException("Invoice not found")
    return inv
