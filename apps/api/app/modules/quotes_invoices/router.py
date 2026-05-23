from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from fastapi.responses import PlainTextResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import CurrentTenantContext
from app.modules.quotes_invoices import service
from app.modules.quotes_invoices.schemas import (
    InvoiceCreate,
    InvoiceListResponse,
    InvoiceResponse,
    InvoiceUpdate,
    QuoteCreate,
    QuoteListResponse,
    QuoteResponse,
    QuoteUpdate,
    RecordPaymentIn,
)

router = APIRouter(tags=["Quotes & Invoices"])


def _quote_response(q, names: dict) -> QuoteResponse:
    data = QuoteResponse.model_validate(q)
    data.customer_name = names.get(q.customer_id)
    return data


def _invoice_response(inv, names: dict) -> InvoiceResponse:
    data = InvoiceResponse.model_validate(inv)
    data.customer_name = names.get(inv.customer_id)
    return data


@router.get("/quotes", response_model=QuoteListResponse)
async def list_quotes(
    ctx: CurrentTenantContext,
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    title: str | None = None,
    quote_number: str | None = None,
    total_min: int | None = None,
    total_max: int | None = None,
    valid_until_from: date | None = None,
    valid_until_to: date | None = None,
):
    _, tenant, _ = ctx
    items, total = await service.list_quotes(
        db,
        tenant.id,
        page,
        title=title,
        quote_number=quote_number,
        total_min=total_min,
        total_max=total_max,
        valid_until_from=valid_until_from,
        valid_until_to=valid_until_to,
    )
    names = await service.load_customer_names(db, tenant.id, [q.customer_id for q in items])
    return {"items": [_quote_response(q, names) for q in items], "total": total}


@router.post("/quotes", response_model=QuoteResponse, status_code=201)
async def create_quote(data: QuoteCreate, ctx: CurrentTenantContext, db: AsyncSession = Depends(get_db)):
    user, tenant, _ = ctx
    q = await service.create_quote(db, tenant.id, data, actor_user_id=user.id)
    names = await service.load_customer_names(db, tenant.id, [q.customer_id])
    return _quote_response(q, names)


@router.get("/quotes/{quote_id}", response_model=QuoteResponse)
async def get_quote(quote_id: UUID, ctx: CurrentTenantContext, db: AsyncSession = Depends(get_db)):
    _, tenant, _ = ctx
    q = await service.get_quote(db, tenant.id, quote_id)
    names = await service.load_customer_names(db, tenant.id, [q.customer_id])
    return _quote_response(q, names)


@router.patch("/quotes/{quote_id}", response_model=QuoteResponse)
async def update_quote(quote_id: UUID, data: QuoteUpdate, ctx: CurrentTenantContext, db: AsyncSession = Depends(get_db)):
    user, tenant, _ = ctx
    q = await service.update_quote(db, tenant.id, quote_id, data, actor_user_id=user.id)
    names = await service.load_customer_names(db, tenant.id, [q.customer_id])
    return _quote_response(q, names)


@router.delete("/quotes/{quote_id}", status_code=204)
async def delete_quote(quote_id: UUID, ctx: CurrentTenantContext, db: AsyncSession = Depends(get_db)):
    user, tenant, _ = ctx
    await service.delete_quote(db, tenant.id, quote_id, actor_user_id=user.id)


@router.post("/quotes/{quote_id}/send", response_model=QuoteResponse)
async def send_quote(quote_id: UUID, ctx: CurrentTenantContext, db: AsyncSession = Depends(get_db)):
    user, tenant, _ = ctx
    q = await service.send_quote(db, tenant.id, quote_id, actor_user_id=user.id)
    names = await service.load_customer_names(db, tenant.id, [q.customer_id])
    return _quote_response(q, names)


@router.post("/quotes/{quote_id}/send-invoice", response_model=InvoiceResponse)
async def send_invoice_from_quote(quote_id: UUID, ctx: CurrentTenantContext, db: AsyncSession = Depends(get_db)):
    user, tenant, _ = ctx
    inv = await service.send_invoice_from_quote(db, tenant.id, quote_id, actor_user_id=user.id)
    inv = await service.get_invoice(db, tenant.id, inv.id)
    names = await service.load_customer_names(db, tenant.id, [inv.customer_id])
    return _invoice_response(inv, names)


@router.get("/invoices", response_model=InvoiceListResponse)
async def list_invoices(
    ctx: CurrentTenantContext,
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    category: str | None = None,
    title: str | None = None,
    invoice_number: str | None = None,
    total_min: int | None = None,
    total_max: int | None = None,
    due_date_from: date | None = None,
    due_date_to: date | None = None,
    payment_channel: str | None = None,
    sort_by: str | None = None,
    sort_dir: str = Query("desc", pattern="^(asc|desc)$"),
):
    _, tenant, _ = ctx
    items, total = await service.list_invoices(
        db,
        tenant.id,
        page,
        category=category,
        title=title,
        invoice_number=invoice_number,
        total_min=total_min,
        total_max=total_max,
        due_date_from=due_date_from,
        due_date_to=due_date_to,
        payment_channel=payment_channel,
        sort_by=sort_by,
        sort_dir=sort_dir,
    )
    names = await service.load_customer_names(db, tenant.id, [i.customer_id for i in items])
    return {"items": [_invoice_response(i, names) for i in items], "total": total}


@router.post("/invoices", response_model=InvoiceResponse, status_code=201)
async def create_invoice(data: InvoiceCreate, ctx: CurrentTenantContext, db: AsyncSession = Depends(get_db)):
    user, tenant, _ = ctx
    inv = await service.create_invoice(db, tenant.id, data, actor_user_id=user.id)
    names = await service.load_customer_names(db, tenant.id, [inv.customer_id])
    return _invoice_response(inv, names)


@router.get("/invoices/{invoice_id}", response_model=InvoiceResponse)
async def get_invoice(invoice_id: UUID, ctx: CurrentTenantContext, db: AsyncSession = Depends(get_db)):
    _, tenant, _ = ctx
    inv = await service.get_invoice(db, tenant.id, invoice_id)
    names = await service.load_customer_names(db, tenant.id, [inv.customer_id])
    return _invoice_response(inv, names)


@router.patch("/invoices/{invoice_id}", response_model=InvoiceResponse)
async def update_invoice(invoice_id: UUID, data: InvoiceUpdate, ctx: CurrentTenantContext, db: AsyncSession = Depends(get_db)):
    user, tenant, _ = ctx
    inv = await service.update_invoice(db, tenant.id, invoice_id, data, actor_user_id=user.id)
    names = await service.load_customer_names(db, tenant.id, [inv.customer_id])
    return _invoice_response(inv, names)


@router.post("/invoices/{invoice_id}/send", response_model=InvoiceResponse)
async def send_invoice(invoice_id: UUID, ctx: CurrentTenantContext, db: AsyncSession = Depends(get_db)):
    user, tenant, _ = ctx
    inv = await service.send_invoice(db, tenant.id, invoice_id, actor_user_id=user.id)
    inv = await service.get_invoice(db, tenant.id, inv.id)
    names = await service.load_customer_names(db, tenant.id, [inv.customer_id])
    return _invoice_response(inv, names)


@router.post("/invoices/{invoice_id}/record-payment", response_model=InvoiceResponse)
async def record_invoice_payment(
    invoice_id: UUID,
    ctx: CurrentTenantContext,
    db: AsyncSession = Depends(get_db),
    body: RecordPaymentIn | None = None,
):
    _, tenant, _ = ctx
    channel = body.payment_channel if body else "cash_deposit"
    inv = await service.record_invoice_paid(db, tenant.id, invoice_id, payment_channel=channel)
    names = await service.load_customer_names(db, tenant.id, [inv.customer_id])
    return _invoice_response(inv, names)


@router.delete("/invoices/{invoice_id}", status_code=204)
async def delete_invoice(invoice_id: UUID, ctx: CurrentTenantContext, db: AsyncSession = Depends(get_db)):
    user, tenant, _ = ctx
    await service.delete_invoice(db, tenant.id, invoice_id, actor_user_id=user.id)
