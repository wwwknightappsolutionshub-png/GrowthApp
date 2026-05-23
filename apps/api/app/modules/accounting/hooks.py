from __future__ import annotations

import logging

from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


async def maybe_auto_invoice_booking(db: AsyncSession, *, tenant_id, booking) -> None:
    try:
        from app.modules.accounting.service import auto_invoice_from_booking

        await auto_invoice_from_booking(db, tenant_id, booking)
    except Exception:
        logger.exception("auto_invoice_from_booking failed booking=%s", booking.id)
