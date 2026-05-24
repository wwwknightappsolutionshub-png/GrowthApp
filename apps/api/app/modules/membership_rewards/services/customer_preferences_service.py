"""Customer loyalty portal preferences."""

from __future__ import annotations

import uuid
from datetime import date, datetime, timezone
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.crm.models import Customer
from app.modules.membership_rewards.models import MrCustomerPreferences


async def get_or_create_preferences(
    db: AsyncSession, tenant_id: uuid.UUID, customer_id: uuid.UUID
) -> MrCustomerPreferences:
    row = await db.get(MrCustomerPreferences, {"tenant_id": tenant_id, "customer_id": customer_id})
    if row:
        return row
    row = MrCustomerPreferences(tenant_id=tenant_id, customer_id=customer_id)
    db.add(row)
    await db.flush()
    return row


def preferences_payload(
    prefs: MrCustomerPreferences, customer: Customer
) -> dict[str, Any]:
    return {
        "date_of_birth": customer.date_of_birth,
        "marketing_email": prefs.marketing_email,
        "marketing_sms": prefs.marketing_sms,
        "birthday_participation": prefs.birthday_participation,
        "expiring_points_reminders": prefs.expiring_points_reminders,
    }


async def update_preferences(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    customer: Customer,
    date_of_birth: date | None = None,
    marketing_email: bool | None = None,
    marketing_sms: bool | None = None,
    birthday_participation: bool | None = None,
    expiring_points_reminders: bool | None = None,
    update_dob: bool = False,
) -> dict[str, Any]:
    prefs = await get_or_create_preferences(db, tenant_id, customer.id)

    if update_dob:
        customer.date_of_birth = date_of_birth
    if marketing_email is not None:
        prefs.marketing_email = marketing_email
    if marketing_sms is not None:
        prefs.marketing_sms = marketing_sms
    if birthday_participation is not None:
        prefs.birthday_participation = birthday_participation
    if expiring_points_reminders is not None:
        prefs.expiring_points_reminders = expiring_points_reminders

    prefs.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(prefs)
    await db.refresh(customer)
    return preferences_payload(prefs, customer)
