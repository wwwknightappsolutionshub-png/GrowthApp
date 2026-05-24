"""Customer loyalty profile and ledger reads."""

from __future__ import annotations

import logging
import uuid

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.crm.models import Customer
from app.modules.membership_rewards.customer_auth.credentials import get_credentials
from app.modules.membership_rewards.engines.reward_rules import has_loyalty_signup_bonus
from app.modules.membership_rewards.models import MrCustomerLoyalty, MrPointsLedger

logger = logging.getLogger(__name__)


async def get_or_create_loyalty(
    db: AsyncSession, tenant_id: uuid.UUID, customer_id: uuid.UUID
) -> MrCustomerLoyalty:
    row = await db.get(MrCustomerLoyalty, {"tenant_id": tenant_id, "customer_id": customer_id})
    if not row:
        row = MrCustomerLoyalty(tenant_id=tenant_id, customer_id=customer_id)
        db.add(row)
        await db.flush()
    return row


async def get_customer_loyalty(
    db: AsyncSession, tenant_id: uuid.UUID, customer_id: uuid.UUID
) -> MrCustomerLoyalty:
    return await get_or_create_loyalty(db, tenant_id, customer_id)


async def list_ledger(
    db: AsyncSession, tenant_id: uuid.UUID, customer_id: uuid.UUID, *, limit: int = 50
) -> list[MrPointsLedger]:
    q = (
        select(MrPointsLedger)
        .where(
            MrPointsLedger.tenant_id == tenant_id,
            MrPointsLedger.customer_id == customer_id,
        )
        .order_by(MrPointsLedger.created_at.desc())
        .limit(min(limit, 200))
    )
    return list((await db.execute(q)).scalars().all())


async def list_loyalty_leaderboard(
    db: AsyncSession, tenant_id: uuid.UUID, *, limit: int = 20
) -> list[dict]:
    q = (
        select(MrCustomerLoyalty, Customer)
        .join(Customer, Customer.id == MrCustomerLoyalty.customer_id)
        .where(MrCustomerLoyalty.tenant_id == tenant_id)
        .order_by(MrCustomerLoyalty.points_lifetime.desc())
        .limit(min(limit, 100))
    )
    rows = (await db.execute(q)).all()
    return [
        {
            "customer_id": str(loyalty.customer_id),
            "customer_name": f"{cust.first_name or ''} {cust.last_name or ''}".strip() or cust.email,
            "points_balance": loyalty.points_balance,
            "points_lifetime": loyalty.points_lifetime,
            "tier_code": loyalty.tier_code,
        }
        for loyalty, cust in rows
    ]


async def count_members_with_points(db: AsyncSession, tenant_id: uuid.UUID) -> int:
    return int(
        (
            await db.execute(
                select(func.count())
                .select_from(MrCustomerLoyalty)
                .where(
                    MrCustomerLoyalty.tenant_id == tenant_id,
                    MrCustomerLoyalty.points_balance > 0,
                )
            )
        ).scalar()
        or 0
    )


async def find_customer_by_contact(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    *,
    email: str | None,
    phone: str | None,
) -> Customer | None:
    """Find an existing CRM customer by normalized email and/or phone."""
    normalized_email = (email or "").strip().lower() or None
    normalized_phone = (phone or "").strip() or None
    if not normalized_email and not normalized_phone:
        return None

    clauses = []
    if normalized_email:
        clauses.append(func.lower(Customer.email) == normalized_email)
    if normalized_phone:
        clauses.append(Customer.phone == normalized_phone)

    return (
        await db.execute(
            select(Customer).where(
                Customer.tenant_id == tenant_id,
                Customer.deleted_at.is_(None),
                or_(*clauses),
            )
        )
    ).scalar_one_or_none()


async def contact_already_enrolled_in_loyalty(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    *,
    email: str | None,
    phone: str | None,
) -> bool:
    """Return True if any customer matching email or phone is already in the loyalty program."""
    normalized_email = (email or "").strip().lower() or None
    normalized_phone = (phone or "").strip() or None

    if normalized_email:
        matches = (
            await db.execute(
                select(Customer).where(
                    Customer.tenant_id == tenant_id,
                    Customer.deleted_at.is_(None),
                    func.lower(Customer.email) == normalized_email,
                )
            )
        ).scalars().all()
        for customer in matches:
            if await is_loyalty_program_enrolled(db, tenant_id, customer.id):
                return True

    if normalized_phone:
        matches = (
            await db.execute(
                select(Customer).where(
                    Customer.tenant_id == tenant_id,
                    Customer.deleted_at.is_(None),
                    Customer.phone == normalized_phone,
                )
            )
        ).scalars().all()
        for customer in matches:
            if await is_loyalty_program_enrolled(db, tenant_id, customer.id):
                return True

    return False


async def _has_portal_credentials(
    db: AsyncSession, tenant_id: uuid.UUID, customer_id: uuid.UUID
) -> bool:
    """Best-effort portal credential check; never raises on missing migration/table."""
    try:
        return await get_credentials(db, tenant_id, customer_id) is not None
    except Exception:  # noqa: BLE001
        logger.exception(
            "Portal credentials lookup failed tenant=%s customer=%s",
            tenant_id,
            customer_id,
        )
        return False


async def is_loyalty_program_enrolled(
    db: AsyncSession, tenant_id: uuid.UUID, customer_id: uuid.UUID
) -> bool:
    """True if the customer already completed public loyalty tier enrollment."""
    loyalty = await db.get(MrCustomerLoyalty, {"tenant_id": tenant_id, "customer_id": customer_id})
    if loyalty and loyalty.tier_updated_at is not None:
        return True
    if await has_loyalty_signup_bonus(db, tenant_id, customer_id):
        return True
    return await _has_portal_credentials(db, tenant_id, customer_id)
