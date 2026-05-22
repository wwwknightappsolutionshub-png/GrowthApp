import uuid
import secrets
from datetime import datetime, timezone
from sqlalchemy import select, func, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.core.audit import log_action
from app.core.exceptions import NotFoundException, BadRequestException
from app.modules.quotes_invoices.models import Quote, QuoteItem, Invoice, InvoiceItem, Payment
from app.modules.quotes_invoices.schemas import QuoteCreate, InvoiceCreate, QuoteItemIn


def _calc_totals(items: list[QuoteItemIn]) -> tuple[int, int, int]:
    subtotal = sum(i.unit_price_pence * i.quantity for i in items)
    vat = sum(int(i.unit_price_pence * i.quantity * i.vat_rate / 100) for i in items)
    return subtotal, vat, subtotal + vat


async def _allocate_number(db: AsyncSession, tenant_id: uuid.UUID, kind: str) -> int:
    """
    Race-free per-tenant counter allocation.

    On PostgreSQL this calls the `next_tenant_number(tenant_id, kind)` SQL
    function which uses `UPDATE ... RETURNING` for atomic increment. On SQLite
    (dev only) we fall back to a transactional update of the tenants row.
    """
    dialect_name = db.get_bind().dialect.name

    if dialect_name == "postgresql":
        result = await db.execute(
            text("SELECT next_tenant_number(CAST(:tid AS uuid), CAST(:kind AS text))"),
            {"tid": str(tenant_id), "kind": kind},
        )
        return int(result.scalar_one())

    # SQLite fallback for local dev / tests.
    if kind not in ("quote", "invoice"):
        raise ValueError(f"unknown numbering kind: {kind}")
    column = "last_quote_number" if kind == "quote" else "last_invoice_number"
    await db.execute(
        text(f"UPDATE tenants SET {column} = {column} + 1 WHERE id = :tid"),
        {"tid": str(tenant_id)},
    )
    row = await db.execute(
        text(f"SELECT {column} FROM tenants WHERE id = :tid"),
        {"tid": str(tenant_id)},
    )
    return int(row.scalar_one())


async def create_quote(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    data: QuoteCreate,
    *,
    actor_user_id: uuid.UUID | None = None,
) -> Quote:
    next_num = await _allocate_number(db, tenant_id, "quote")
    quote_number = f"QT-{next_num:04d}"
    subtotal, vat, total = _calc_totals(data.items)
    quote = Quote(
        id=uuid.uuid4(), tenant_id=tenant_id, customer_id=data.customer_id,
        deal_id=data.deal_id, quote_number=quote_number,
        public_token=secrets.token_urlsafe(32),
        title=data.title, notes=data.notes, valid_until=data.valid_until,
        subtotal_pence=subtotal, vat_pence=vat, total_pence=total,
    )
    db.add(quote)
    await db.flush()
    for i, item_data in enumerate(data.items):
        line_total = item_data.unit_price_pence * item_data.quantity
        item = QuoteItem(id=uuid.uuid4(), quote_id=quote.id, line_total_pence=line_total, sort_order=i, **item_data.model_dump(exclude={"sort_order"}))
        db.add(item)
    await log_action(
        db,
        action="quote.created",
        resource="quote",
        resource_id=quote.id,
        tenant_id=tenant_id,
        user_id=actor_user_id,
        metadata={"quote_number": quote_number, "total_pence": total},
    )
    await db.commit()
    return await get_quote(db, tenant_id, quote.id)


async def get_quote(db: AsyncSession, tenant_id: uuid.UUID, quote_id: uuid.UUID) -> Quote:
    result = await db.execute(select(Quote).options(selectinload(Quote.items)).where(Quote.id == quote_id, Quote.tenant_id == tenant_id))
    q = result.scalar_one_or_none()
    if not q:
        raise NotFoundException("Quote")
    return q


async def get_public_quote(db: AsyncSession, public_token: str) -> dict:
    result = await db.execute(select(Quote).options(selectinload(Quote.items)).where(Quote.public_token == public_token))
    q = result.scalar_one_or_none()
    if not q:
        raise NotFoundException("Quote")
    return {"id": str(q.id), "title": q.title, "status": q.status, "total_pence": q.total_pence, "items": q.items, "valid_until": q.valid_until}


async def respond_to_quote(db: AsyncSession, public_token: str, accepted: bool) -> dict:
    result = await db.execute(select(Quote).where(Quote.public_token == public_token))
    q = result.scalar_one_or_none()
    if not q:
        raise NotFoundException("Quote")
    if q.status not in ("sent", "draft"):
        raise BadRequestException("Quote cannot be responded to in current status")
    now = datetime.now(timezone.utc)
    if accepted:
        q.status = "accepted"
        q.accepted_at = now
        db.add(q)
        await db.flush()
        invoice = await create_invoice_from_quote(db, q.tenant_id, q)
        await log_action(
            db,
            action="quote.accepted",
            resource="quote",
            resource_id=q.id,
            tenant_id=q.tenant_id,
            metadata={"invoice_id": str(invoice.id), "via": "public_link"},
        )
        await db.commit()
        return {"accepted": True, "invoice_id": str(invoice.id), "message": "Quote accepted! An invoice has been raised."}
    else:
        q.status = "declined"
        q.declined_at = now
        db.add(q)
        await log_action(
            db,
            action="quote.declined",
            resource="quote",
            resource_id=q.id,
            tenant_id=q.tenant_id,
            metadata={"via": "public_link"},
        )
        await db.commit()
        return {"accepted": False, "message": "Quote declined. We'll be in touch."}


async def create_invoice_from_quote(db: AsyncSession, tenant_id: uuid.UUID, quote: Quote) -> Invoice:
    next_num = await _allocate_number(db, tenant_id, "invoice")
    inv = Invoice(
        id=uuid.uuid4(), tenant_id=tenant_id, customer_id=quote.customer_id,
        quote_id=quote.id, deal_id=quote.deal_id,
        invoice_number=f"INV-{next_num:04d}",
        public_token=secrets.token_urlsafe(32),
        title=quote.title, notes=quote.notes,
        subtotal_pence=quote.subtotal_pence, vat_pence=quote.vat_pence, total_pence=quote.total_pence,
    )
    db.add(inv)
    await db.flush()
    for qi in quote.items:
        ii = InvoiceItem(id=uuid.uuid4(), invoice_id=inv.id, description=qi.description, quantity=qi.quantity, unit_price_pence=qi.unit_price_pence, vat_rate=qi.vat_rate, line_total_pence=qi.line_total_pence, sort_order=qi.sort_order)
        db.add(ii)
    await db.commit()
    return await get_invoice(db, tenant_id, inv.id)


async def send_quote(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    quote_id: uuid.UUID,
    *,
    actor_user_id: uuid.UUID | None = None,
) -> Quote:
    q = await get_quote(db, tenant_id, quote_id)
    q.status = "sent"
    q.sent_at = datetime.now(timezone.utc)
    db.add(q)
    await log_action(
        db,
        action="quote.sent",
        resource="quote",
        resource_id=q.id,
        tenant_id=tenant_id,
        user_id=actor_user_id,
        metadata={"quote_number": q.quote_number, "total_pence": q.total_pence},
    )
    await db.commit()
    from app.workers.queue import enqueue
    await enqueue("trigger_automation_for_event", tenant_id=str(tenant_id), event="quote_sent", entity_id=str(q.id))
    return q


async def list_quotes(db: AsyncSession, tenant_id: uuid.UUID, page: int = 1, page_size: int = 25) -> tuple[list[Quote], int]:
    q = select(Quote).where(Quote.tenant_id == tenant_id)
    total = (await db.execute(select(func.count()).select_from(q.subquery()))).scalar_one()
    items = (await db.execute(q.options(selectinload(Quote.items)).order_by(Quote.created_at.desc()).offset((page-1)*page_size).limit(page_size))).scalars().all()
    return list(items), total


async def create_invoice(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    data: InvoiceCreate,
    *,
    actor_user_id: uuid.UUID | None = None,
) -> Invoice:
    next_num = await _allocate_number(db, tenant_id, "invoice")
    items_data = data.items
    subtotal, vat, total = _calc_totals(items_data)
    inv = Invoice(id=uuid.uuid4(), tenant_id=tenant_id, customer_id=data.customer_id, quote_id=data.quote_id, deal_id=data.deal_id, invoice_number=f"INV-{next_num:04d}", public_token=secrets.token_urlsafe(32), title=data.title, notes=data.notes, due_date=data.due_date, subtotal_pence=subtotal, vat_pence=vat, total_pence=total)
    db.add(inv)
    await db.flush()
    for i, item_data in enumerate(items_data):
        ii = InvoiceItem(id=uuid.uuid4(), invoice_id=inv.id, line_total_pence=item_data.unit_price_pence*item_data.quantity, sort_order=i, **item_data.model_dump(exclude={"sort_order"}))
        db.add(ii)
    await log_action(
        db,
        action="invoice.created",
        resource="invoice",
        resource_id=inv.id,
        tenant_id=tenant_id,
        user_id=actor_user_id,
        metadata={"invoice_number": inv.invoice_number, "total_pence": total},
    )
    await db.commit()
    return await get_invoice(db, tenant_id, inv.id)


async def get_invoice(db: AsyncSession, tenant_id: uuid.UUID, invoice_id: uuid.UUID) -> Invoice:
    result = await db.execute(select(Invoice).options(selectinload(Invoice.items)).where(Invoice.id == invoice_id, Invoice.tenant_id == tenant_id))
    inv = result.scalar_one_or_none()
    if not inv:
        raise NotFoundException("Invoice")
    return inv


async def list_invoices(db: AsyncSession, tenant_id: uuid.UUID, page: int = 1, page_size: int = 25) -> tuple[list[Invoice], int]:
    q = select(Invoice).where(Invoice.tenant_id == tenant_id)
    total = (await db.execute(select(func.count()).select_from(q.subquery()))).scalar_one()
    items = (await db.execute(q.options(selectinload(Invoice.items)).order_by(Invoice.created_at.desc()).offset((page-1)*page_size).limit(page_size))).scalars().all()
    return list(items), total


async def record_invoice_paid(db: AsyncSession, tenant_id: uuid.UUID, invoice_id: uuid.UUID) -> Invoice:
    """Mark CRM invoice paid and trigger referral automation (invoice paid → eligible)."""
    inv = await get_invoice(db, tenant_id, invoice_id)
    if inv.status == "paid":
        return inv
    now = datetime.now(timezone.utc)
    inv.status = "paid"
    inv.paid_pence = inv.total_pence
    inv.paid_at = now
    db.add(inv)
    await db.commit()
    await db.refresh(inv)
    from app.modules.referrals.service import on_invoice_paid

    await on_invoice_paid(db, tenant_id=tenant_id, invoice_id=invoice_id)
    return inv


async def delete_invoice(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    invoice_id: uuid.UUID,
    *,
    actor_user_id: uuid.UUID | None = None,
) -> None:
    """Hard-delete draft invoices only."""
    from app.core.audit import log_action
    from app.core.exceptions import BadRequestException

    inv = await get_invoice(db, tenant_id, invoice_id)
    if inv.status != "draft":
        raise BadRequestException("Only draft invoices can be deleted. Void sent invoices instead.")
    await log_action(
        db,
        action="invoice.deleted",
        resource="invoice",
        resource_id=invoice_id,
        tenant_id=tenant_id,
        user_id=actor_user_id,
        metadata={"invoice_number": inv.invoice_number},
    )
    await db.delete(inv)
    await db.commit()
