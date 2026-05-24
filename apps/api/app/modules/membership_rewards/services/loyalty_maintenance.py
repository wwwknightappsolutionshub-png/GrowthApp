"""Scheduled loyalty maintenance — birthday bonuses and expiring-point reminders."""

from __future__ import annotations

import logging
import uuid
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import extract, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.accounting.models import TenantAddon
from app.modules.crm.models import Customer
from app.modules.membership_rewards.constants import FEATURE_MEMBERSHIP_REWARDS
from app.modules.membership_rewards.engines.purchase_earn import birthday_reference_id, is_birthday_today
from app.modules.membership_rewards.entitlement import tenant_has_membership_rewards
from app.modules.membership_rewards.models import MrCustomerPreferences, MrPointsLedger
from app.modules.membership_rewards import service as mr_service
from app.modules.membership_rewards.services.customer_preferences_service import get_or_create_preferences
from app.modules.membership_rewards.services.notification_triggers import notify_points_expiring_soon

logger = logging.getLogger(__name__)

EXPIRING_NOTICE_COOLDOWN_DAYS = 7
EXPIRING_LOOKAHEAD_DAYS = 7


async def _active_loyalty_tenant_ids(db: AsyncSession) -> list[uuid.UUID]:
    rows = (
        await db.execute(
            select(TenantAddon.tenant_id).where(
                TenantAddon.feature_code == FEATURE_MEMBERSHIP_REWARDS,
                TenantAddon.status == "active",
            )
        )
    ).scalars().all()
    entitled: list[uuid.UUID] = []
    for tenant_id in rows:
        if await tenant_has_membership_rewards(db, tenant_id):
            entitled.append(tenant_id)
    return entitled


async def sweep_birthday_bonuses(db: AsyncSession, *, today: date | None = None) -> int:
    """Award birthday bonus points once per customer per calendar year."""
    ref_day = today or date.today()
    year = ref_day.year
    awarded = 0

    for tenant_id in await _active_loyalty_tenant_ids(db):
        bonus = 0
        try:
            settings = await mr_service.get_settings(db, tenant_id)
            bonus = int((settings.earn_rules or {}).get("birthday_bonus", 0))
        except (TypeError, ValueError):
            bonus = 0
        if bonus <= 0:
            continue

        customers = (
            await db.execute(
                select(Customer)
                .outerjoin(
                    MrCustomerPreferences,
                    (MrCustomerPreferences.tenant_id == Customer.tenant_id)
                    & (MrCustomerPreferences.customer_id == Customer.id),
                )
                .where(
                    Customer.tenant_id == tenant_id,
                    Customer.deleted_at.is_(None),
                    Customer.date_of_birth.isnot(None),
                    extract("month", Customer.date_of_birth) == ref_day.month,
                    extract("day", Customer.date_of_birth) == ref_day.day,
                    or_(
                        MrCustomerPreferences.birthday_participation.is_(None),
                        MrCustomerPreferences.birthday_participation.is_(True),
                    ),
                )
            )
        ).scalars().all()

        for customer in customers:
            if not customer.date_of_birth or not is_birthday_today(customer.date_of_birth, today=ref_day):
                continue
            ref_id = birthday_reference_id(tenant_id, customer.id, year)
            existing = (
                await db.execute(
                    select(MrPointsLedger.id).where(
                        MrPointsLedger.tenant_id == tenant_id,
                        MrPointsLedger.customer_id == customer.id,
                        MrPointsLedger.reference_type == "birthday",
                        MrPointsLedger.reference_id == ref_id,
                    )
                )
            ).scalar_one_or_none()
            if existing:
                continue
            try:
                await mr_service.earn_points(
                    db,
                    tenant_id,
                    customer.id,
                    bonus,
                    source="birthday",
                    reference_type="birthday",
                    reference_id=ref_id,
                    description=f"Birthday bonus {year}",
                )
                awarded += 1
            except Exception:  # noqa: BLE001
                logger.exception(
                    "birthday bonus failed tenant=%s customer=%s", tenant_id, customer.id
                )

    logger.info("loyalty_birthday_sweep awarded=%s day=%s", awarded, ref_day.isoformat())
    return awarded


async def sweep_expiring_points_reminders(db: AsyncSession) -> int:
    """Notify customers whose points expire within the next week."""
    now = datetime.now(timezone.utc)
    window_end = now + timedelta(days=EXPIRING_LOOKAHEAD_DAYS)
    cooldown = now - timedelta(days=EXPIRING_NOTICE_COOLDOWN_DAYS)
    sent = 0

    rows = (
        await db.execute(
            select(
                MrPointsLedger.tenant_id,
                MrPointsLedger.customer_id,
                func.min(MrPointsLedger.expires_at).label("first_expiry"),
                func.sum(MrPointsLedger.amount).label("points_total"),
            )
            .where(
                MrPointsLedger.amount > 0,
                MrPointsLedger.expires_at.isnot(None),
                MrPointsLedger.expires_at > now,
                MrPointsLedger.expires_at <= window_end,
            )
            .group_by(MrPointsLedger.tenant_id, MrPointsLedger.customer_id)
        )
    ).all()

    for tenant_id, customer_id, first_expiry, points_total in rows:
        if not await tenant_has_membership_rewards(db, tenant_id):
            continue
        prefs = await get_or_create_preferences(db, tenant_id, customer_id)
        if not prefs.expiring_points_reminders:
            continue
        last = prefs.last_expiring_points_notice_at
        if last:
            if last.tzinfo is None:
                last = last.replace(tzinfo=timezone.utc)
            if last > cooldown:
                continue

        points = int(points_total or 0)
        if points <= 0 or not first_expiry:
            continue

        expiry = first_expiry
        if expiry.tzinfo is None:
            expiry = expiry.replace(tzinfo=timezone.utc)
        days_left = max(1, (expiry.date() - now.date()).days)

        try:
            await notify_points_expiring_soon(
                db,
                tenant_id=tenant_id,
                customer_id=customer_id,
                points=points,
                days_left=days_left,
            )
            prefs.last_expiring_points_notice_at = now
            await db.commit()
            sent += 1
        except Exception:  # noqa: BLE001
            logger.exception(
                "expiring points reminder failed tenant=%s customer=%s",
                tenant_id,
                customer_id,
            )

    logger.info("loyalty_expiring_reminders sent=%s", sent)
    return sent
