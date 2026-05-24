"""Customer loyalty notification triggers."""

from __future__ import annotations

import logging
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


async def notify_tier_upgrade(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    customer_id: uuid.UUID,
    tier_name: str,
) -> None:
    """Placeholder for push/email on tier upgrade (Phase 4 PWA)."""
    logger.info(
        "loyalty tier upgrade tenant=%s customer=%s tier=%s",
        tenant_id,
        customer_id,
        tier_name,
    )


async def notify_points_expiring_soon(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    customer_id: uuid.UUID,
    points: int,
    days_left: int,
) -> None:
    """Placeholder for expiring-points reminder (Phase 4 PWA push)."""
    logger.info(
        "loyalty points expiring tenant=%s customer=%s points=%s days=%s",
        tenant_id,
        customer_id,
        points,
        days_left,
    )
