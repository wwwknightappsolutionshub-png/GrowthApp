"""Link bookings to CRM customers (and leads when appropriate)."""
from __future__ import annotations

import uuid

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.crm.models import Customer
from app.modules.crm.schemas import CustomerCreate
from app.modules.crm import service as crm_service
from app.modules.leads.models import Lead


def _split_name(full_name: str) -> tuple[str, str | None]:
    parts = (full_name or "").strip().split(maxsplit=1)
    if not parts:
        return "Guest", None
    if len(parts) == 1:
        return parts[0], None
    return parts[0], parts[1]


async def resolve_customer_for_booking(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    *,
    customer_id: uuid.UUID | None,
    customer_name: str,
    customer_email: str | None,
    customer_phone: str | None,
    channel: str | None = None,
) -> uuid.UUID | None:
    """Return customer_id — existing, matched, or newly created."""
    if customer_id:
        row = (
            await db.execute(
                select(Customer.id).where(
                    Customer.id == customer_id,
                    Customer.tenant_id == tenant_id,
                    Customer.deleted_at.is_(None),
                )
            )
        ).scalar_one_or_none()
        if row:
            return customer_id

    email = (customer_email or "").strip().lower() or None
    phone = (customer_phone or "").strip() or None
    if email or phone:
        clauses = []
        if email:
            clauses.append(Customer.email == email)
        if phone:
            clauses.append(Customer.phone == phone)
        existing = (
            await db.execute(
                select(Customer).where(
                    Customer.tenant_id == tenant_id,
                    Customer.deleted_at.is_(None),
                    or_(*clauses),
                )
            )
        ).scalar_one_or_none()
        if existing:
            return existing.id

    first, last = _split_name(customer_name)
    created = await crm_service.create_customer(
        db,
        tenant_id,
        CustomerCreate(
            first_name=first,
            last_name=last,
            email=customer_email,
            phone=customer_phone,
            source=channel or "booking",
        ),
        commit=False,
    )
    return created.id


async def ensure_lead_for_booking(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    *,
    customer_email: str | None,
    customer_phone: str | None,
    customer_name: str,
    channel: str | None,
) -> uuid.UUID | None:
    """Create a lead when we have contact details and no duplicate open lead."""
    email = (customer_email or "").strip().lower() or None
    phone = (customer_phone or "").strip() or None
    if not email and not phone:
        return None

    q = select(Lead).where(Lead.tenant_id == tenant_id, Lead.deleted_at.is_(None))
    if email and phone:
        q = q.where(or_(Lead.email == email, Lead.phone == phone))
    elif email:
        q = q.where(Lead.email == email)
    else:
        q = q.where(Lead.phone == phone)

    existing = (await db.execute(q.limit(1))).scalar_one_or_none()
    if existing:
        return existing.id

    first, last = _split_name(customer_name)
    lead = Lead(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        first_name=first,
        last_name=last,
        email=customer_email,
        phone=customer_phone,
        source=channel or "booking_widget",
        status="new",
    )
    db.add(lead)
    await db.flush()
    return lead.id
