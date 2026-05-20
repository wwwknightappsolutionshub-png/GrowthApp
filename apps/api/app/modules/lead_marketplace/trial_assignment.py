"""Trial period: 2 leads/day matched by trade + postcode."""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.modules.lead_marketplace.geo import (
    business_type_to_category_name,
    postcodes_match,
)
from app.modules.lead_marketplace.models import LeadCategory, LeadMarketplace
from app.modules.lead_marketplace.trial_models import TrialLeadDelivery
from app.modules.leads.models import Lead
from app.modules.tenants.models import Tenant

logger = logging.getLogger(__name__)


def _trial_window_start() -> datetime:
    return datetime.now(timezone.utc) - timedelta(days=settings.TRIAL_LEAD_DAYS)


async def _deliveries_today(db: AsyncSession, tenant_id: uuid.UUID) -> int:
    start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    return int(
        (
            await db.execute(
                select(func.count(TrialLeadDelivery.id)).where(
                    TrialLeadDelivery.tenant_id == tenant_id,
                    TrialLeadDelivery.delivered_at >= start,
                )
            )
        ).scalar()
        or 0
    )


async def _copy_lead_to_tenant(
    db: AsyncSession,
    *,
    pool_lead: Lead,
    tenant_id: uuid.UUID,
) -> Lead:
    copy = Lead(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        location_id=None,
        first_name=pool_lead.first_name,
        last_name=pool_lead.last_name,
        email=pool_lead.email,
        phone=pool_lead.phone,
        message=pool_lead.message,
        service_needed=pool_lead.service_needed,
        postcode=pool_lead.postcode,
        source="trial_marketplace",
        status="new",
        is_spam=False,
        tags=[*(pool_lead.tags or []), "trial_auto"],
        extra_data={
            **(pool_lead.extra_data or {}),
            "trial_delivery": True,
            "pool_lead_id": str(pool_lead.id),
        },
        score=pool_lead.score,
        score_label=pool_lead.score_label,
    )
    db.add(copy)
    await db.flush()
    return copy


async def assign_trial_leads_for_tenant(
    db: AsyncSession,
    tenant: Tenant,
    *,
    limit: int | None = None,
) -> int:
    """Assign up to `limit` marketplace leads to this tenant (default: remaining daily quota)."""
    if tenant.is_managed_client:
        return 0

    already_today = await _deliveries_today(db, tenant.id)
    cap = limit if limit is not None else max(0, settings.TRIAL_LEADS_PER_DAY - already_today)
    if cap <= 0:
        return 0

    if tenant.created_at.replace(tzinfo=timezone.utc) < _trial_window_start():
        return 0

    category_name = business_type_to_category_name(tenant.business_type)
    cat_id = (
        await db.execute(
            select(LeadCategory.id).where(
                func.lower(LeadCategory.name) == category_name.lower()
            )
        )
    ).scalar_one_or_none()
    if not cat_id:
        cat_id = (
            await db.execute(
                select(LeadCategory.id).where(
                    func.lower(LeadCategory.name).contains(tenant.business_type.lower()[:6])
                )
            )
        ).scalar_one_or_none()

    stmt = (
        select(LeadMarketplace, Lead)
        .join(Lead, Lead.id == LeadMarketplace.lead_id)
        .where(LeadMarketplace.status == "available")
        .order_by(LeadMarketplace.ai_score.desc(), LeadMarketplace.created_at.asc())
        .limit(80)
    )
    if cat_id:
        stmt = stmt.where(LeadMarketplace.category_id == cat_id)
    candidates = (await db.execute(stmt)).all()

    delivered = 0
    for item, pool_lead in candidates:
        if delivered >= cap:
            break
        if cat_id and item.category_id != cat_id:
            continue
        if not postcodes_match(tenant.postcode, pool_lead.postcode):
            continue

        copy = await _copy_lead_to_tenant(db, pool_lead=pool_lead, tenant_id=tenant.id)
        item.assigned_tenant_id = tenant.id
        item.status = "sold"
        db.add(item)
        db.add(
            TrialLeadDelivery(
                id=uuid.uuid4(),
                tenant_id=tenant.id,
                marketplace_item_id=item.id,
                pool_lead_id=pool_lead.id,
                tenant_lead_id=copy.id,
            )
        )
        delivered += 1

    if delivered:
        await db.commit()
        logger.info("Trial leads delivered tenant=%s count=%s", tenant.id, delivered)
    return delivered


async def run_daily_trial_assignments(db: AsyncSession) -> dict[str, int]:
    """Cron: assign trial leads for all eligible tenants."""
    tenants = (
        await db.execute(
            select(Tenant).where(
                Tenant.is_active == True,  # noqa: E712
                Tenant.is_managed_client == False,
                Tenant.created_at >= _trial_window_start(),
            )
        )
    ).scalars().all()

    total = 0
    for tenant in tenants:
        try:
            total += await assign_trial_leads_for_tenant(db, tenant)
        except Exception:  # noqa: BLE001
            logger.exception("trial assign failed tenant=%s", tenant.id)
            await db.rollback()
    return {"tenants_checked": len(tenants), "leads_delivered": total}
