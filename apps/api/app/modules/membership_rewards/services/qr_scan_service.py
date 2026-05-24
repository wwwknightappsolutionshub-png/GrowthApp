"""Staff QR scan — validate customer wallet codes and award check-in points."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequestException, ForbiddenException, NotFoundException
from app.modules.crm.models import Customer
from app.modules.membership_rewards.customer_auth.qr_tokens import record_scan, validate_qr_token
from app.modules.membership_rewards.engines.earning_engine import earn_points
from app.modules.membership_rewards.engines.reward_rules import earn_rule_amount
from app.modules.membership_rewards.models import MrQrScanEvent
from app.modules.membership_rewards.services.customer_loyalty_service import get_customer_loyalty

QR_PREFIX = "cf-loyalty:"


def parse_loyalty_qr_payload(payload: str) -> tuple[uuid.UUID, uuid.UUID, str]:
    """Parse `cf-loyalty:{tenant_id}:{customer_id}:{token}` from a scanned QR."""
    raw = payload.strip()
    if not raw:
        raise BadRequestException("Empty QR payload")

    body = raw[len(QR_PREFIX) :] if raw.startswith(QR_PREFIX) else raw
    parts = body.split(":", 2)
    if len(parts) != 3:
        raise BadRequestException("Unrecognized loyalty QR code")

    try:
        tenant_id = uuid.UUID(parts[0])
        customer_id = uuid.UUID(parts[1])
        token = parts[2]
    except ValueError as exc:
        raise BadRequestException("Unrecognized loyalty QR code") from exc

    if not token:
        raise BadRequestException("Unrecognized loyalty QR code")
    return tenant_id, customer_id, token


async def _checked_in_today(
    db: AsyncSession, tenant_id: uuid.UUID, customer_id: uuid.UUID
) -> bool:
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    row = (
        await db.execute(
            select(MrQrScanEvent.id)
            .where(
                MrQrScanEvent.tenant_id == tenant_id,
                MrQrScanEvent.customer_id == customer_id,
                MrQrScanEvent.scanned_at >= today_start,
                MrQrScanEvent.points_awarded.isnot(None),
                MrQrScanEvent.points_awarded > 0,
            )
            .limit(1)
        )
    ).scalar_one_or_none()
    return row is not None


async def staff_scan_qr(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    payload: str,
    staff_user_id: uuid.UUID,
) -> dict:
    """Validate a customer QR, log the scan, and optionally award check-in points."""
    parsed_tenant, customer_id, raw_token = parse_loyalty_qr_payload(payload)
    if parsed_tenant != tenant_id:
        raise ForbiddenException("This QR code belongs to another business")

    customer = (
        await db.execute(
            select(Customer).where(
                Customer.id == customer_id,
                Customer.tenant_id == tenant_id,
                Customer.deleted_at.is_(None),
            )
        )
    ).scalar_one_or_none()
    if not customer:
        raise NotFoundException("Customer not found")

    qr_token = await validate_qr_token(db, tenant_id, raw_token)
    if qr_token.customer_id != customer_id:
        raise BadRequestException("QR code does not match customer")

    checkin_points = await earn_rule_amount(db, tenant_id, "qr_checkin")
    points_awarded = 0
    message = "Check-in recorded"

    if checkin_points > 0:
        if await _checked_in_today(db, tenant_id, customer_id):
            message = "Check-in recorded — visit points already awarded today"
        else:
            points_awarded = checkin_points
            message = f"Check-in complete — {points_awarded} points awarded"

    event = await record_scan(
        db,
        tenant_id=tenant_id,
        customer_id=customer_id,
        qr_token=qr_token,
        staff_user_id=staff_user_id,
        points_awarded=points_awarded if points_awarded else None,
    )

    if points_awarded > 0:
        await earn_points(
            db,
            tenant_id,
            customer_id,
            points_awarded,
            source="qr_checkin",
            description="In-store visit check-in",
            reference_type="qr_scan",
            reference_id=event.id,
        )

    loyalty = await get_customer_loyalty(db, tenant_id, customer_id)
    name = f"{customer.first_name or ''} {customer.last_name or ''}".strip() or customer.email

    return {
        "scan_id": event.id,
        "customer_id": customer_id,
        "customer_name": name,
        "points_awarded": points_awarded,
        "points_balance": loyalty.points_balance,
        "tier_code": loyalty.tier_code,
        "message": message,
    }
