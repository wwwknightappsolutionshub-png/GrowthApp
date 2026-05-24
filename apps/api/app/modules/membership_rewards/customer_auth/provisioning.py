"""Auto-provision customer loyalty portal accounts."""

from __future__ import annotations

import logging
import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.booking.models import Booking
from app.modules.crm.models import Customer
from app.modules.membership_rewards.customer_auth.credentials import ensure_credentials, get_credentials
from app.modules.membership_rewards.customer_auth.magic_link import create_magic_link_token
from app.modules.membership_rewards.engines.reward_rules import (
    has_loyalty_signup_bonus,
    membership_signup_bonus_points,
)
from app.modules.membership_rewards.engines.tier_engine import set_tier
from app.modules.membership_rewards.entitlement import tenant_has_membership_rewards
from app.modules.membership_rewards import service as mr_service
from app.modules.membership_rewards.services.customer_loyalty_service import get_or_create_loyalty
from app.modules.tenants.models import Tenant

logger = logging.getLogger(__name__)


async def _customer_booking_count(
    db: AsyncSession, tenant_id: uuid.UUID, customer_id: uuid.UUID
) -> int:
    return int(
        (
            await db.execute(
                select(func.count())
                .select_from(Booking)
                .where(
                    Booking.tenant_id == tenant_id,
                    Booking.customer_id == customer_id,
                )
            )
        ).scalar()
        or 0
    )


async def should_provision_from_booking(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    customer_id: uuid.UUID,
    join_loyalty_program: bool | None,
) -> bool:
    """Decide whether to create a portal account for this booking."""
    if join_loyalty_program is False:
        return False
    if await get_credentials(db, tenant_id, customer_id):
        return False
    if join_loyalty_program is True:
        return True
    # Automatic on first booking when widget did not send an explicit opt-out.
    return await _customer_booking_count(db, tenant_id, customer_id) <= 1


async def provision_from_booking(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    customer_id: uuid.UUID,
    booking_id: uuid.UUID,
    join_loyalty_program: bool | None = None,
) -> dict | None:
    """Create loyalty portal account after booking when eligible."""
    if not await tenant_has_membership_rewards(db, tenant_id):
        return None

    customer = await db.get(Customer, customer_id)
    if not customer or customer.tenant_id != tenant_id or customer.deleted_at is not None:
        return None

    email = (customer.email or "").strip()
    booking = await db.get(Booking, booking_id)
    if not email and booking and (booking.customer_email or "").strip():
        email = booking.customer_email.strip()
        customer.email = email
        await db.flush()

    if not email:
        return None

    if not await should_provision_from_booking(
        db,
        tenant_id=tenant_id,
        customer_id=customer_id,
        join_loyalty_program=join_loyalty_program,
    ):
        return None

    return await ensure_portal_account(
        db,
        tenant_id=tenant_id,
        customer_id=customer_id,
        email=email,
        customer_name=customer.first_name or customer.email or "there",
        source="booking",
        reference_id=booking_id,
        award_signup_bonus=True,
    )


async def ensure_portal_account(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    customer_id: uuid.UUID,
    email: str,
    customer_name: str,
    tier_code: str | None = None,
    source: str = "manual",
    reference_id: uuid.UUID | None = None,
    award_signup_bonus: bool = False,
) -> dict:
    """Ensure loyalty row + credentials exist; send consolidated welcome email."""
    await get_or_create_loyalty(db, tenant_id, customer_id)
    if tier_code:
        await set_tier(db, tenant_id, customer_id, tier_code)

    _, temp_password = await ensure_credentials(db, tenant_id, customer_id)

    link = await create_magic_link_token(
        db, tenant_id=tenant_id, customer_id=customer_id, email=email
    )
    magic_url = link[1] if link else None

    signup_bonus = 0
    points_balance = 0
    awarded_bonus = False
    if award_signup_bonus:
        signup_bonus = await membership_signup_bonus_points(db, tenant_id)
        if signup_bonus > 0 and not await has_loyalty_signup_bonus(db, tenant_id, customer_id):
            entry = await mr_service.earn_points(
                db,
                tenant_id,
                customer_id,
                signup_bonus,
                source="membership",
                description="Welcome bonus — rewards program signup",
                reference_type="loyalty_signup",
                reference_id=reference_id,
            )
            points_balance = entry.balance_after
            awarded_bonus = True
        else:
            loyalty = await get_or_create_loyalty(db, tenant_id, customer_id)
            points_balance = loyalty.points_balance
            await db.commit()
    else:
        loyalty = await get_or_create_loyalty(db, tenant_id, customer_id)
        points_balance = loyalty.points_balance
        await db.commit()

    tenant = await db.get(Tenant, tenant_id)
    tenant_name = tenant.name if tenant else "Our business"
    tenant_slug = tenant.slug if tenant else str(tenant_id)

    from app.modules.booking.feedback import refer_url_for_slug
    from app.modules.membership_rewards.landing import memberships_public_url, rewards_portal_url
    from app.modules.membership_rewards.loyalty_email import send_portal_welcome_email

    loyalty = await get_or_create_loyalty(db, tenant_id, customer_id)
    tier_name = loyalty.tier_code.replace("_", " ").title() if loyalty.tier_code else None

    try:
        await send_portal_welcome_email(
            to=email,
            customer_name=customer_name,
            tenant_name=tenant_name,
            rewards_portal_url=rewards_portal_url(tenant_slug),
            magic_link_url=magic_url,
            signup_bonus_points=signup_bonus if awarded_bonus else 0,
            points_balance=points_balance,
            refer_win_url=refer_url_for_slug(tenant_slug),
            memberships_url=memberships_public_url(tenant_slug),
            tier_name=tier_name if tier_code else None,
        )
    except Exception:  # noqa: BLE001
        logger.exception(
            "Portal welcome email failed tenant=%s customer=%s source=%s",
            tenant_id,
            customer_id,
            source,
        )

    return {
        "customer_id": str(customer_id),
        "credentials_created": temp_password is not None,
        "magic_link_sent": bool(magic_url),
        "signup_bonus_awarded": awarded_bonus,
        "points_balance": points_balance,
    }
