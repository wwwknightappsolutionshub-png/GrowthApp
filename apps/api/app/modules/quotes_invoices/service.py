import csv
import io
import uuid
import secrets
from datetime import date, datetime, timezone
from sqlalchemy import delete, select, func, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.core.audit import log_action
from app.core.exceptions import NotFoundException, BadRequestException
from app.modules.crm.models import Customer
from app.modules.quotes_invoices.models import Quote, QuoteItem, Invoice, InvoiceItem, Payment
from app.modules.quotes_invoices.schemas import QuoteCreate, QuoteUpdate, InvoiceCreate, InvoiceUpdate, QuoteItemIn
from app.modules.quotes_invoices.delivery import deliver_invoice_email, deliver_quote_email
from app.modules.quotes_invoices.recurrency import (
    apply_invoice_renewal_schedule,
    sync_customer_service_renewal,
    validate_recurrency,
)


def _calc_totals(items: list[QuoteItemIn]) -> tuple[int, int, int]:
    subtotal = sum(i.unit_price_pence * i.quantity for i in items)
    vat = sum(int(i.unit_price_pence * i.quantity * i.vat_rate / 100) for i in items)
    return subtotal, vat, subtotal + vat


def _line_total_pence(item: QuoteItemIn) -> int:
    return item.unit_price_pence * item.quantity


async def _replace_quote_items(db: AsyncSession, quote_id: uuid.UUID, items: list[QuoteItemIn]) -> None:
    await db.execute(delete(QuoteItem).where(QuoteItem.quote_id == quote_id))
    await db.flush()
    for i, item_data in enumerate(items):
        line_total = _line_total_pence(item_data)
        db.add(
            QuoteItem(
                id=uuid.uuid4(),
                quote_id=quote_id,
                line_total_pence=line_total,
                sort_order=i,
                **item_data.model_dump(exclude={"sort_order"}),
            )
        )


async def _replace_invoice_items(db: AsyncSession, invoice_id: uuid.UUID, items: list[QuoteItemIn]) -> None:
    await db.execute(delete(InvoiceItem).where(InvoiceItem.invoice_id == invoice_id))
    await db.flush()
    for i, item_data in enumerate(items):
        line_total = _line_total_pence(item_data)
        db.add(
            InvoiceItem(
                id=uuid.uuid4(),
                invoice_id=invoice_id,
                line_total_pence=line_total,
                sort_order=i,
                **item_data.model_dump(exclude={"sort_order"}),
            )
        )


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
    from app.modules.accounting.service import mark_quote_viewed

    await mark_quote_viewed(db, q)
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
        from app.modules.accounting.service import move_deal_on_quote_accept

        await move_deal_on_quote_accept(db, q.tenant_id, q)
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


async def update_quote(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    quote_id: uuid.UUID,
    data: QuoteUpdate,
    *,
    actor_user_id: uuid.UUID | None = None,
) -> Quote:
    q = await get_quote(db, tenant_id, quote_id)
    if q.status not in ("draft", "sent"):
        raise BadRequestException("Only draft or sent quotes can be edited.")
    if data.items is not None and q.status != "draft":
        raise BadRequestException("Line items can only be changed on draft quotes.")

    if data.title is not None:
        q.title = data.title
    if data.notes is not None:
        q.notes = data.notes
    if data.valid_until is not None:
        q.valid_until = data.valid_until
    if data.deal_id is not None:
        q.deal_id = data.deal_id
    if data.items is not None:
        await _replace_quote_items(db, q.id, data.items)
        subtotal, vat, total = _calc_totals(data.items)
        q.subtotal_pence = subtotal
        q.vat_pence = vat
        q.total_pence = total

    await log_action(
        db,
        action="quote.updated",
        resource="quote",
        resource_id=q.id,
        tenant_id=tenant_id,
        user_id=actor_user_id,
        metadata={"quote_number": q.quote_number},
    )
    await db.commit()
    return await get_quote(db, tenant_id, quote_id)


async def delete_quote(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    quote_id: uuid.UUID,
    *,
    actor_user_id: uuid.UUID | None = None,
) -> None:
    q = await get_quote(db, tenant_id, quote_id)
    if q.status != "draft":
        raise BadRequestException("Only draft quotes can be deleted.")
    await log_action(
        db,
        action="quote.deleted",
        resource="quote",
        resource_id=quote_id,
        tenant_id=tenant_id,
        user_id=actor_user_id,
        metadata={"quote_number": q.quote_number},
    )
    await db.delete(q)
    await db.commit()


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
    await deliver_quote_email(db, tenant_id, q, actor_user_id=actor_user_id)
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
    return await get_quote(db, tenant_id, quote_id)


async def send_invoice(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    invoice_id: uuid.UUID,
    *,
    actor_user_id: uuid.UUID | None = None,
) -> Invoice:
    inv = await get_invoice(db, tenant_id, invoice_id)
    return await deliver_invoice_email(db, tenant_id, inv, actor_user_id=actor_user_id)


async def send_invoice_from_quote(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    quote_id: uuid.UUID,
    *,
    actor_user_id: uuid.UUID | None = None,
) -> Invoice:
    q = await get_quote(db, tenant_id, quote_id)
    existing = (
        await db.execute(
            select(Invoice).where(Invoice.tenant_id == tenant_id, Invoice.quote_id == q.id)
        )
    ).scalar_one_or_none()
    if existing:
        inv = existing
    else:
        inv = await create_invoice_from_quote(db, tenant_id, q)
        inv = await get_invoice(db, tenant_id, inv.id)
    if inv.due_date is None and q.valid_until is not None:
        inv.due_date = q.valid_until
        db.add(inv)
        await db.flush()
    return await deliver_invoice_email(db, tenant_id, inv, actor_user_id=actor_user_id)


def _apply_invoice_category(stmt, category: str | None, today: date):
    if category == "cash_in":
        return stmt.where(Invoice.status == "paid")
    if category == "cash_pending":
        return stmt.where(
            Invoice.status.in_(("sent", "viewed", "partial")),
            Invoice.paid_pence < Invoice.total_pence,
        )
    if category == "cash_out":
        return stmt.where(
            Invoice.status.in_(("sent", "viewed", "overdue", "partial")),
            Invoice.due_date.is_not(None),
            Invoice.due_date < today,
            Invoice.paid_pence < Invoice.total_pence,
        )
    return stmt


async def list_quotes(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    page: int = 1,
    page_size: int = 25,
    *,
    title: str | None = None,
    quote_number: str | None = None,
    total_min: int | None = None,
    total_max: int | None = None,
    valid_until_from: date | None = None,
    valid_until_to: date | None = None,
) -> tuple[list[Quote], int]:
    q = select(Quote).where(Quote.tenant_id == tenant_id)
    if title:
        q = q.where(Quote.title.ilike(f"%{title}%"))
    if quote_number:
        q = q.where(Quote.quote_number.ilike(f"%{quote_number}%"))
    if total_min is not None:
        q = q.where(Quote.total_pence >= total_min)
    if total_max is not None:
        q = q.where(Quote.total_pence <= total_max)
    if valid_until_from is not None:
        q = q.where(Quote.valid_until >= valid_until_from)
    if valid_until_to is not None:
        q = q.where(Quote.valid_until <= valid_until_to)
    total = (await db.execute(select(func.count()).select_from(q.subquery()))).scalar_one()
    items = (
        await db.execute(
            q.options(selectinload(Quote.items))
            .order_by(Quote.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
    ).scalars().all()
    return list(items), total


def _parse_recurrency(value: str | None) -> str | None:
    if value is None:
        return None
    try:
        return validate_recurrency(value)
    except ValueError as e:
        raise BadRequestException(str(e)) from e


async def _apply_renewal_to_invoice(
    db: AsyncSession, tenant_id: uuid.UUID, inv: Invoice
) -> None:
    apply_invoice_renewal_schedule(inv)
    db.add(inv)
    await db.flush()
    if inv.recurrency and inv.renewal_due_date:
        await sync_customer_service_renewal(db, tenant_id, inv)


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
    recurrency = _parse_recurrency(data.recurrency)
    inv = Invoice(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        customer_id=data.customer_id,
        quote_id=data.quote_id,
        deal_id=data.deal_id,
        invoice_number=f"INV-{next_num:04d}",
        public_token=secrets.token_urlsafe(32),
        title=data.title,
        notes=data.notes,
        due_date=data.due_date,
        recurrency=recurrency,
        subtotal_pence=subtotal,
        vat_pence=vat,
        total_pence=total,
    )
    db.add(inv)
    await db.flush()
    await _apply_renewal_to_invoice(db, tenant_id, inv)
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


async def list_invoices(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    page: int = 1,
    page_size: int = 25,
    *,
    category: str | None = None,
    title: str | None = None,
    invoice_number: str | None = None,
    total_min: int | None = None,
    total_max: int | None = None,
    due_date_from: date | None = None,
    due_date_to: date | None = None,
    paid_from: date | None = None,
    paid_to: date | None = None,
    payment_channel: str | None = None,
    sort_by: str | None = None,
    sort_dir: str = "desc",
) -> tuple[list[Invoice], int]:
    today = date.today()
    q = select(Invoice).where(Invoice.tenant_id == tenant_id)
    q = _apply_invoice_category(q, category, today)
    if title:
        q = q.where(Invoice.title.ilike(f"%{title}%"))
    if invoice_number:
        q = q.where(Invoice.invoice_number.ilike(f"%{invoice_number}%"))
    if total_min is not None:
        q = q.where(Invoice.total_pence >= total_min)
    if total_max is not None:
        q = q.where(Invoice.total_pence <= total_max)
    if due_date_from is not None:
        q = q.where(Invoice.due_date >= due_date_from)
    if due_date_to is not None:
        q = q.where(Invoice.due_date <= due_date_to)
    if paid_from is not None:
        q = q.where(func.date(Invoice.paid_at) >= paid_from)
    if paid_to is not None:
        q = q.where(func.date(Invoice.paid_at) <= paid_to)
    if payment_channel:
        q = q.where(Invoice.payment_channel == payment_channel)
    order_col = Invoice.created_at
    if sort_by == "amount":
        order_col = Invoice.total_pence
    elif sort_by == "due_date":
        order_col = Invoice.due_date
    elif sort_by == "deposit_date":
        order_col = Invoice.paid_at
    elif sort_by == "channel":
        order_col = Invoice.payment_channel
    if sort_dir == "asc":
        q = q.order_by(order_col.asc().nulls_last())
    else:
        q = q.order_by(order_col.desc().nulls_last())
    total = (await db.execute(select(func.count()).select_from(q.subquery()))).scalar_one()
    items = (
        await db.execute(
            q.options(selectinload(Invoice.items))
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
    ).scalars().all()
    return list(items), total


async def list_cash_saved(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    page: int = 1,
    page_size: int = 50,
    *,
    payment_channel: str | None = None,
    total_min: int | None = None,
    total_max: int | None = None,
    deposit_from: date | None = None,
    deposit_to: date | None = None,
    sort_by: str | None = None,
    sort_dir: str = "desc",
) -> tuple[list[Invoice], int]:
    return await list_invoices(
        db,
        tenant_id,
        page,
        page_size,
        category="cash_in",
        payment_channel=payment_channel,
        total_min=total_min,
        total_max=total_max,
        paid_from=deposit_from,
        paid_to=deposit_to,
        sort_by=sort_by or "deposit_date",
        sort_dir=sort_dir,
    )


async def load_customer_names(
    db: AsyncSession, tenant_id: uuid.UUID, customer_ids: list[uuid.UUID]
) -> dict[uuid.UUID, str]:
    if not customer_ids:
        return {}
    rows = (
        await db.execute(
            select(Customer).where(
                Customer.tenant_id == tenant_id,
                Customer.id.in_(customer_ids),
            )
        )
    ).scalars().all()
    out: dict[uuid.UUID, str] = {}
    for c in rows:
        out[c.id] = f"{c.first_name} {c.last_name or ''}".strip() or "Customer"
    return out


async def export_accounts_report_csv(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    *,
    category: str,
    date_from: date | None = None,
    date_to: date | None = None,
) -> str:
    """CSV export for accounts reports (invoices or quotes)."""
    today = date.today()
    buf = io.StringIO()
    writer = csv.writer(buf)
    if category == "quotes":
        stmt = select(Quote).where(Quote.tenant_id == tenant_id)
        if date_from:
            stmt = stmt.where(func.date(Quote.created_at) >= date_from)
        if date_to:
            stmt = stmt.where(func.date(Quote.created_at) <= date_to)
        rows = (await db.execute(stmt.order_by(Quote.created_at.desc()))).scalars().all()
        writer.writerow(["quote_number", "title", "status", "total_pence", "valid_until", "created_at"])
        for r in rows:
            writer.writerow(
                [r.quote_number, r.title, r.status, r.total_pence, r.valid_until, r.created_at]
            )
        return buf.getvalue()

    stmt = select(Invoice).where(Invoice.tenant_id == tenant_id)
    stmt = _apply_invoice_category(stmt, category if category != "cash_saved" else "cash_in", today)
    if date_from:
        stmt = stmt.where(func.date(Invoice.created_at) >= date_from)
    if date_to:
        stmt = stmt.where(func.date(Invoice.created_at) <= date_to)
    rows = (await db.execute(stmt.order_by(Invoice.created_at.desc()))).scalars().all()
    writer.writerow(
        ["invoice_number", "title", "status", "total_pence", "paid_pence", "due_date", "payment_channel", "paid_at"]
    )
    for r in rows:
        writer.writerow(
            [
                r.invoice_number,
                r.title,
                r.status,
                r.total_pence,
                r.paid_pence,
                r.due_date,
                r.payment_channel,
                r.paid_at,
            ]
        )
    return buf.getvalue()


async def update_invoice(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    invoice_id: uuid.UUID,
    data: InvoiceUpdate,
    *,
    actor_user_id: uuid.UUID | None = None,
) -> Invoice:
    inv = await get_invoice(db, tenant_id, invoice_id)
    if inv.status != "draft":
        raise BadRequestException("Only draft invoices can be edited.")
    if data.title is not None:
        inv.title = data.title
    if data.notes is not None:
        inv.notes = data.notes
    if data.due_date is not None:
        inv.due_date = data.due_date
    if data.deal_id is not None:
        inv.deal_id = data.deal_id
    if "recurrency" in data.model_fields_set:
        inv.recurrency = _parse_recurrency(data.recurrency)
    if data.items is not None:
        await _replace_invoice_items(db, inv.id, data.items)
        subtotal, vat, total = _calc_totals(data.items)
        inv.subtotal_pence = subtotal
        inv.vat_pence = vat
        inv.total_pence = total

    await _apply_renewal_to_invoice(db, tenant_id, inv)

    await log_action(
        db,
        action="invoice.updated",
        resource="invoice",
        resource_id=inv.id,
        tenant_id=tenant_id,
        user_id=actor_user_id,
        metadata={"invoice_number": inv.invoice_number},
    )
    await db.commit()
    return await get_invoice(db, tenant_id, invoice_id)


async def record_invoice_paid(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    invoice_id: uuid.UUID,
    *,
    payment_channel: str = "cash_deposit",
) -> Invoice:
    """Mark CRM invoice paid and award loyalty points when applicable."""
    inv = await get_invoice(db, tenant_id, invoice_id)
    if inv.status == "paid":
        return inv
    now = datetime.now(timezone.utc)
    amount_due = max(0, inv.total_pence - inv.paid_pence)
    inv.status = "paid"
    inv.paid_pence = inv.total_pence
    inv.paid_at = now
    inv.payment_channel = payment_channel
    db.add(inv)
    if amount_due > 0:
        method = "stripe" if payment_channel == "online" else "manual"
        db.add(
            Payment(
                id=uuid.uuid4(),
                tenant_id=tenant_id,
                invoice_id=invoice_id,
                amount_pence=amount_due,
                method=method,
                status="succeeded",
            )
        )
    await db.commit()
    await db.refresh(inv)
    if inv.recurrency and inv.renewal_due_date:
        await sync_customer_service_renewal(db, tenant_id, inv)
        await db.commit()
    from app.modules.membership_rewards.hooks import on_invoice_paid as mr_invoice_points

    await mr_invoice_points(db, tenant_id=tenant_id, invoice_id=invoice_id)
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
