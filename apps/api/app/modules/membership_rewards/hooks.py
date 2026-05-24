"""Event hooks — award loyalty points via Membership & Rewards."""

from __future__ import annotations

import logging
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.booking.models import Booking
from app.modules.membership_rewards.entitlement import tenant_has_membership_rewards
from app.modules.membership_rewards.models import MrPointsLedger
from app.modules.membership_rewards import service
from app.modules.quotes_invoices.models import Invoice

logger = logging.getLogger(__name__)


async def _already_earned(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    customer_id: uuid.UUID,
    reference_type: str,
    reference_id: uuid.UUID,
) -> bool:
    row = (
        await db.execute(
            select(MrPointsLedger.id).where(
                MrPointsLedger.tenant_id == tenant_id,
                MrPointsLedger.customer_id == customer_id,
                MrPointsLedger.reference_type == reference_type,
                MrPointsLedger.reference_id == reference_id,
                MrPointsLedger.amount > 0,
            )
        )
    ).scalar_one_or_none()
    return row is not None


async def _award_if_new(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    customer_id: uuid.UUID,
    amount: int,
    *,
    source: str,
    reference_type: str,
    reference_id: uuid.UUID,
    description: str,
) -> None:
    if amount <= 0:
        return
    if await _already_earned(db, tenant_id, customer_id, reference_type, reference_id):
        return
    await service.earn_points(
        db,
        tenant_id,
        customer_id,
        amount,
        source=source,
        reference_type=reference_type,
        reference_id=reference_id,
        description=description,
    )


async def _earn_rule_amount(db: AsyncSession, tenant_id: uuid.UUID, rule_key: str) -> int:
    settings = await service.get_settings(db, tenant_id)
    rules = settings.earn_rules or {}
    try:
        return int(rules.get(rule_key, 0))
    except (TypeError, ValueError):
        return 0


async def on_booking_completed(
    db: AsyncSession, *, tenant_id: uuid.UUID, booking: Booking
) -> None:
    """Award points when a booking is marked completed."""
    if not booking.customer_id:
        return
    if not await tenant_has_membership_rewards(db, tenant_id):
        return
    try:
        pts = await _earn_rule_amount(db, tenant_id, "booking_completed")
        await _award_if_new(
            db,
            tenant_id,
            booking.customer_id,
            pts,
            source="booking",
            reference_type="booking",
            reference_id=booking.id,
            description="Booking completed",
        )
    except Exception:  # noqa: BLE001
        logger.exception("Membership points booking hook failed tenant=%s booking=%s", tenant_id, booking.id)


async def on_invoice_paid(
    db: AsyncSession, *, tenant_id: uuid.UUID, invoice_id: uuid.UUID
) -> None:
    """Award purchase-based points when an invoice is paid (per line item)."""
    from app.modules.quotes_invoices.models import InvoiceItem

    from app.modules.membership_rewards.engines.purchase_earn import points_for_invoice_item

    inv = (
        await db.execute(
            select(Invoice).where(Invoice.id == invoice_id, Invoice.tenant_id == tenant_id)
        )
    ).scalar_one_or_none()
    if not inv or not inv.customer_id:
        return
    if not await tenant_has_membership_rewards(db, tenant_id):
        return
    try:
        settings = await service.get_settings(db, tenant_id)
        rules = settings.earn_rules or {}
        items = list(
            (
                await db.execute(
                    select(InvoiceItem).where(InvoiceItem.invoice_id == invoice_id).order_by(InvoiceItem.sort_order)
                )
            ).scalars().all()
        )

        if items:
            for item in items:
                pts = points_for_invoice_item(item, rules)
                if pts <= 0:
                    continue
                kind = item.line_kind or "service"
                await _award_if_new(
                    db,
                    tenant_id,
                    inv.customer_id,
                    pts,
                    source="purchase",
                    reference_type="invoice_item",
                    reference_id=item.id,
                    description=f"{'Product' if kind == 'product' else 'Service'}: {item.description}",
                )
            return

        per_pound = await _earn_rule_amount(db, tenant_id, "purchase_per_pound")
        pounds = max(0, inv.total_pence) // 100
        pts = pounds * per_pound if per_pound else 0
        if pts > 0:
            await _award_if_new(
                db,
                tenant_id,
                inv.customer_id,
                pts,
                source="purchase",
                reference_type="invoice",
                reference_id=invoice_id,
                description=f"Purchase ({pounds} GBP)",
            )
    except Exception:  # noqa: BLE001
        logger.exception("Membership points invoice hook failed tenant=%s invoice=%s", tenant_id, invoice_id)


async def on_subscription_created(
    db: AsyncSession, *, tenant_id: uuid.UUID, subscription_id: uuid.UUID
) -> None:
    """Award signup bonus when a customer subscribes to a membership plan."""
    from app.modules.membership_rewards.models import MrCustomerSubscription

    sub = await db.get(MrCustomerSubscription, subscription_id)
    if not sub or sub.tenant_id != tenant_id:
        return
    if not await tenant_has_membership_rewards(db, tenant_id):
        return
    try:
        pts = await _earn_rule_amount(db, tenant_id, "membership_signup")
        await _award_if_new(
            db,
            tenant_id,
            sub.customer_id,
            pts,
            source="membership",
            reference_type="mr_subscription",
            reference_id=subscription_id,
            description="Membership signup bonus",
        )
    except Exception:  # noqa: BLE001
        logger.exception(
            "Membership points subscription hook failed tenant=%s sub=%s",
            tenant_id,
            subscription_id,
        )


async def on_review_submitted(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    review_id: uuid.UUID,
    customer_id: uuid.UUID | None,
) -> None:
    if not customer_id:
        return
    if not await tenant_has_membership_rewards(db, tenant_id):
        return
    try:
        pts = await _earn_rule_amount(db, tenant_id, "review_left")
        await _award_if_new(
            db,
            tenant_id,
            customer_id,
            pts,
            source="review",
            reference_type="review",
            reference_id=review_id,
            description="Review submitted",
        )
    except Exception:  # noqa: BLE001
        logger.exception("Membership points review hook failed tenant=%s review=%s", tenant_id, review_id)


async def on_refer_win_submitted(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    referrer_customer_id: uuid.UUID,
    lead_id: uuid.UUID,
) -> None:
    """Award loyalty points to the referrer when Refer & Win creates a lead."""
    if not await tenant_has_membership_rewards(db, tenant_id):
        return
    try:
        pts = await _earn_rule_amount(db, tenant_id, "refer_win")
        await _award_if_new(
            db,
            tenant_id,
            referrer_customer_id,
            pts,
            source="refer_win",
            reference_type="refer_win_lead",
            reference_id=lead_id,
            description="Refer & Win submission",
        )
    except Exception:  # noqa: BLE001
        logger.exception(
            "Membership points refer-win hook failed tenant=%s lead=%s",
            tenant_id,
            lead_id,
        )


async def on_booking_created_for_loyalty(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    booking: Booking,
    join_loyalty_program: bool | None = None,
) -> None:
    """Provision customer rewards wallet on first booking or when opted in."""
    if not booking.customer_id:
        return
    if not await tenant_has_membership_rewards(db, tenant_id):
        return
    try:
        from app.modules.membership_rewards.customer_auth.provisioning import provision_from_booking

        await provision_from_booking(
            db,
            tenant_id=tenant_id,
            customer_id=booking.customer_id,
            booking_id=booking.id,
            join_loyalty_program=join_loyalty_program,
        )
    except Exception:  # noqa: BLE001
        logger.exception(
            "Loyalty portal provisioning failed tenant=%s booking=%s",
            tenant_id,
            booking.id,
        )


async def on_tenant_signup(db: AsyncSession, tenant_id: uuid.UUID) -> None:
    """Start 7-day Membership & Rewards trial for new tenants (best-effort)."""
    try:
        await service.start_trial_for_tenant(db, tenant_id)
    except Exception:  # noqa: BLE001
        logger.exception("Membership & Rewards trial start failed for tenant %s", tenant_id)
