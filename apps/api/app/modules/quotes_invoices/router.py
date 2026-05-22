from uuid import UUID
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.dependencies import CurrentTenantContext
from app.modules.quotes_invoices import service
from app.modules.quotes_invoices.schemas import (
    QuoteCreate, QuoteResponse, QuoteListResponse,
    InvoiceCreate, InvoiceResponse, InvoiceListResponse,
)
from app.modules.auth.schemas import MessageResponse

router = APIRouter(tags=["Quotes & Invoices"])


@router.get("/quotes", response_model=QuoteListResponse)
async def list_quotes(ctx: CurrentTenantContext, db: AsyncSession = Depends(get_db), page: int = Query(1, ge=1)):
    _, tenant, _ = ctx
    items, total = await service.list_quotes(db, tenant.id, page)
    return {"items": items, "total": total}


@router.post("/quotes", response_model=QuoteResponse, status_code=201)
async def create_quote(data: QuoteCreate, ctx: CurrentTenantContext, db: AsyncSession = Depends(get_db)):
    user, tenant, _ = ctx
    return await service.create_quote(db, tenant.id, data, actor_user_id=user.id)


@router.get("/quotes/{quote_id}", response_model=QuoteResponse)
async def get_quote(quote_id: UUID, ctx: CurrentTenantContext, db: AsyncSession = Depends(get_db)):
    _, tenant, _ = ctx
    return await service.get_quote(db, tenant.id, quote_id)


@router.post("/quotes/{quote_id}/send", response_model=QuoteResponse)
async def send_quote(quote_id: UUID, ctx: CurrentTenantContext, db: AsyncSession = Depends(get_db)):
    user, tenant, _ = ctx
    return await service.send_quote(db, tenant.id, quote_id, actor_user_id=user.id)


@router.get("/invoices", response_model=InvoiceListResponse)
async def list_invoices(ctx: CurrentTenantContext, db: AsyncSession = Depends(get_db), page: int = Query(1, ge=1)):
    _, tenant, _ = ctx
    items, total = await service.list_invoices(db, tenant.id, page)
    return {"items": items, "total": total}


@router.post("/invoices", response_model=InvoiceResponse, status_code=201)
async def create_invoice(data: InvoiceCreate, ctx: CurrentTenantContext, db: AsyncSession = Depends(get_db)):
    user, tenant, _ = ctx
    return await service.create_invoice(db, tenant.id, data, actor_user_id=user.id)


@router.get("/invoices/{invoice_id}", response_model=InvoiceResponse)
async def get_invoice(invoice_id: UUID, ctx: CurrentTenantContext, db: AsyncSession = Depends(get_db)):
    _, tenant, _ = ctx
    return await service.get_invoice(db, tenant.id, invoice_id)


@router.post("/invoices/{invoice_id}/record-payment", response_model=InvoiceResponse)
async def record_invoice_payment(invoice_id: UUID, ctx: CurrentTenantContext, db: AsyncSession = Depends(get_db)):
    _, tenant, _ = ctx
    return await service.record_invoice_paid(db, tenant.id, invoice_id)


@router.delete("/invoices/{invoice_id}", status_code=204)
async def delete_invoice(invoice_id: UUID, ctx: CurrentTenantContext, db: AsyncSession = Depends(get_db)):
    user, tenant, _ = ctx
    await service.delete_invoice(db, tenant.id, invoice_id, actor_user_id=user.id)
