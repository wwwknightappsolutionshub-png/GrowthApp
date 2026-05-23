"""Industry billing API — gated by industry_billing add-on."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import CurrentTenantContext
from app.modules.addons.billing import service as billing_svc
from app.modules.addons.common.constants import FEATURE_INDUSTRY_BILLING
from app.modules.addons.common.entitlement import require_addon
from app.modules.addons.schemas import (
    IndustryInvoiceCreate,
    MarkupRuleIn,
    MembershipIn,
    ServicePackageIn,
    TemplateIn,
    TipIn,
    WarrantyIn,
)

router = APIRouter(
    prefix="/addons/billing",
    tags=["addons-billing"],
    dependencies=[Depends(require_addon(FEATURE_INDUSTRY_BILLING))],
)


@router.post("/invoices/combo")
async def combo_invoice(body: IndustryInvoiceCreate, ctx: CurrentTenantContext, db: AsyncSession = Depends(get_db)):
    _, tenant, _ = ctx
    return await billing_svc.create_combo_invoice(db, tenant, body)


@router.post("/tips")
async def tip(body: TipIn, ctx: CurrentTenantContext, db: AsyncSession = Depends(get_db)):
    _, tenant, _ = ctx
    return await billing_svc.record_tip(db, tenant, body)


@router.post("/memberships")
async def membership(body: MembershipIn, ctx: CurrentTenantContext, db: AsyncSession = Depends(get_db)):
    _, tenant, _ = ctx
    return await billing_svc.create_membership(db, tenant, body)


@router.get("/memberships")
async def list_memberships(ctx: CurrentTenantContext, db: AsyncSession = Depends(get_db)):
    _, tenant, _ = ctx
    return await billing_svc.list_memberships(db, tenant)


@router.post("/packages")
async def package(body: ServicePackageIn, ctx: CurrentTenantContext, db: AsyncSession = Depends(get_db)):
    _, tenant, _ = ctx
    return await billing_svc.create_service_package(db, tenant, body)


@router.post("/packages/{package_id}/redeem")
async def redeem(package_id: uuid.UUID, customer_id: uuid.UUID, ctx: CurrentTenantContext, db: AsyncSession = Depends(get_db)):
    _, tenant, _ = ctx
    return await billing_svc.redeem_package(db, tenant, package_id, customer_id)


@router.post("/templates")
async def template(body: TemplateIn, ctx: CurrentTenantContext, db: AsyncSession = Depends(get_db)):
    _, tenant, _ = ctx
    return await billing_svc.save_template(db, tenant, body)


@router.get("/templates")
async def list_templates(ctx: CurrentTenantContext, db: AsyncSession = Depends(get_db)):
    _, tenant, _ = ctx
    return await billing_svc.list_templates(db, tenant)


@router.post("/markup-rules")
async def markup(body: MarkupRuleIn, ctx: CurrentTenantContext, db: AsyncSession = Depends(get_db)):
    _, tenant, _ = ctx
    return await billing_svc.save_markup_rule(db, tenant, body)


@router.post("/warranties")
async def warranty(body: WarrantyIn, ctx: CurrentTenantContext, db: AsyncSession = Depends(get_db)):
    _, tenant, _ = ctx
    return await billing_svc.add_warranty(db, tenant, body)


@router.get("/vin/{vin}/invoices")
async def vin_invoices(vin: str, ctx: CurrentTenantContext, db: AsyncSession = Depends(get_db)):
    _, tenant, _ = ctx
    return await billing_svc.invoices_by_vin(db, tenant, vin)
