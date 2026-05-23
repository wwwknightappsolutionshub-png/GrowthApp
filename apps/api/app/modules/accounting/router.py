from __future__ import annotations

from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from fastapi.responses import PlainTextResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import CurrentTenantContext, OwnerContext
from app.modules.accounting import service
from app.modules.accounting.entitlement import require_accounting
from app.modules.accounting.schemas import (
    AccountingCheckoutRequest,
    AccountingCheckoutResponse,
    AccountingSettingsResponse,
    AccountingSettingsUpdate,
    AccountingStatusResponse,
    CustomerFinancialsResponse,
    ExpenseCreate,
    ExpenseListResponse,
    ExpenseResponse,
    RecurringScheduleCreate,
    RecurringScheduleListResponse,
    RecurringScheduleResponse,
    TaxSummaryResponse,
)
from app.modules.quotes_invoices.schemas import InvoiceResponse

router = APIRouter(prefix="/accounting", tags=["Accounting"])


@router.get("/status", response_model=AccountingStatusResponse)
async def accounting_status(ctx: CurrentTenantContext, db: AsyncSession = Depends(get_db)):
    _, tenant, _ = ctx
    return await service.get_status(db, tenant.id)


@router.post("/checkout", response_model=AccountingCheckoutResponse)
async def accounting_checkout(
    data: AccountingCheckoutRequest,
    ctx: OwnerContext,
    db: AsyncSession = Depends(get_db),
):
    _, tenant, _ = ctx
    url = await service.create_accounting_checkout(db, tenant, success_url=data.success_url, cancel_url=data.cancel_url)
    return AccountingCheckoutResponse(checkout_url=url)


@router.get("/settings", response_model=AccountingSettingsResponse, dependencies=[Depends(require_accounting)])
async def get_accounting_settings(ctx: CurrentTenantContext, db: AsyncSession = Depends(get_db)):
    _, tenant, _ = ctx
    row = await service.get_settings(db, tenant.id)
    return row


@router.patch("/settings", response_model=AccountingSettingsResponse, dependencies=[Depends(require_accounting)])
async def patch_accounting_settings(
    data: AccountingSettingsUpdate,
    ctx: CurrentTenantContext,
    db: AsyncSession = Depends(get_db),
):
    _, tenant, _ = ctx
    return await service.update_settings(db, tenant.id, data)


@router.post("/invoices/{invoice_id}/send", response_model=InvoiceResponse, dependencies=[Depends(require_accounting)])
async def send_invoice(
    invoice_id: UUID,
    ctx: CurrentTenantContext,
    db: AsyncSession = Depends(get_db),
):
    user, tenant, _ = ctx
    return await service.send_invoice(db, tenant.id, invoice_id, actor_user_id=user.id)


@router.get("/expenses", response_model=ExpenseListResponse, dependencies=[Depends(require_accounting)])
async def list_expenses(
    ctx: CurrentTenantContext,
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
):
    _, tenant, _ = ctx
    items, total = await service.list_expenses(db, tenant.id, page)
    return {"items": items, "total": total}


@router.post("/expenses", response_model=ExpenseResponse, status_code=201, dependencies=[Depends(require_accounting)])
async def create_expense(
    data: ExpenseCreate,
    ctx: CurrentTenantContext,
    db: AsyncSession = Depends(get_db),
):
    _, tenant, _ = ctx
    return await service.create_expense(db, tenant.id, data)


@router.delete("/expenses/{expense_id}", status_code=204, dependencies=[Depends(require_accounting)])
async def delete_expense(expense_id: UUID, ctx: CurrentTenantContext, db: AsyncSession = Depends(get_db)):
    _, tenant, _ = ctx
    await service.delete_expense(db, tenant.id, expense_id)


@router.get("/recurring", response_model=RecurringScheduleListResponse, dependencies=[Depends(require_accounting)])
async def list_recurring(ctx: CurrentTenantContext, db: AsyncSession = Depends(get_db)):
    _, tenant, _ = ctx
    items = await service.list_recurring(db, tenant.id)
    return {"items": items, "total": len(items)}


@router.post("/recurring", response_model=RecurringScheduleResponse, status_code=201, dependencies=[Depends(require_accounting)])
async def create_recurring(
    data: RecurringScheduleCreate,
    ctx: CurrentTenantContext,
    db: AsyncSession = Depends(get_db),
):
    _, tenant, _ = ctx
    return await service.create_recurring(db, tenant.id, data)


@router.delete("/recurring/{schedule_id}", status_code=204, dependencies=[Depends(require_accounting)])
async def delete_recurring(schedule_id: UUID, ctx: CurrentTenantContext, db: AsyncSession = Depends(get_db)):
    _, tenant, _ = ctx
    await service.delete_recurring(db, tenant.id, schedule_id)


@router.get("/tax-summary", response_model=TaxSummaryResponse, dependencies=[Depends(require_accounting)])
async def get_tax_summary(
    ctx: CurrentTenantContext,
    db: AsyncSession = Depends(get_db),
    year: int | None = None,
):
    _, tenant, _ = ctx
    y = year or date.today().year
    return await service.tax_summary(db, tenant.id, y)


@router.get("/export/accountant-pack", dependencies=[Depends(require_accounting)])
async def export_accountant_pack(
    ctx: CurrentTenantContext,
    db: AsyncSession = Depends(get_db),
    year: int | None = None,
):
    _, tenant, _ = ctx
    y = year or date.today().year
    csv_data = await service.export_accountant_csv(db, tenant.id, y)
    return PlainTextResponse(
        csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="accountant-pack-{y}.csv"'},
    )


@router.get("/customers/{customer_id}/financials", response_model=CustomerFinancialsResponse, dependencies=[Depends(require_accounting)])
async def customer_financials(customer_id: UUID, ctx: CurrentTenantContext, db: AsyncSession = Depends(get_db)):
    _, tenant, _ = ctx
    return await service.customer_financials(db, tenant.id, customer_id)
