"""Assignment Engine — automatic lead-to-tenant distribution."""
from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.lead_marketplace import service as _svc


async def run_distribution(
    db: AsyncSession,
    marketplace_id: uuid.UUID,
) -> dict[str, Any] | None:
    """Run the automatic distribution engine for a marketplace item.

    Priority = subscription_level * rule.priority_weight + ai_score
    """
    return await _svc.run_distribution(db, marketplace_id)


async def bulk_distribute(
    db: AsyncSession,
    marketplace_ids: list[uuid.UUID],
) -> list[dict[str, Any]]:
    """Attempt distribution for multiple items; returns successful assignments."""
    results = []
    for mid in marketplace_ids:
        result = await run_distribution(db, mid)
        if result:
            results.append(result)
    return results
