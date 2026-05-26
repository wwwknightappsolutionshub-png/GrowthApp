from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException
from app.core.audit import log_action
from app.core.exceptions import NotFoundException
from app.modules.leads.models import Lead, LeadRequest
from app.modules.leads.schemas import LeadCreate, LeadUpdate, LeadRequestCreate, LeadRequestAdminAction
from app.modules.tenants.models import Tenant

if TYPE_CHECKING:
    from app.modules.crm.models import Deal


async def create_lead_public(db: AsyncSession, tenant: Tenant, data: LeadCreate, ip_address: str | None = None) -> Lead:
    from app.modules.crm.pipeline_service import ensure_default_pipeline

    pipeline = await ensure_default_pipeline(db, tenant.id)
    first_stage = sorted(pipeline.stages, key=lambda s: s.position)[0]
    lead = Lead(
        id=uuid.uuid4(),
        tenant_id=tenant.id,
        pipeline_id=pipeline.id,
        stage_id=first_stage.id,
        location_id=data.location_id,
        first_name=data.first_name,
        last_name=data.last_name,
        email=data.email,
        phone=data.phone,
        message=data.message,
        service_needed=data.service_needed,
        postcode=data.postcode,
        source=data.source,
        utm_source=data.utm_source,
        utm_medium=data.utm_medium,
        utm_campaign=data.utm_campaign,
        ip_address=ip_address,
        status="new",
    )
    db.add(lead)
    await log_action(
        db,
        action="lead.created",
        resource="lead",
        resource_id=lead.id,
        tenant_id=tenant.id,
        metadata={"source": lead.source, "ip": ip_address},
    )
    await db.commit()
    await db.refresh(lead)

    from app.workers.queue import enqueue
    await enqueue("trigger_automation_for_event", tenant_id=str(tenant.id), event="lead_created", entity_id=str(lead.id), entity_type="lead")
    await enqueue("score_lead_task", lead_id=str(lead.id), tenant_id=str(tenant.id))
    try:
        from app.modules.pwa.service import maybe_send_first_lead_email

        await maybe_send_first_lead_email(db, tenant_id=tenant.id)
    except Exception:  # noqa: BLE001
        pass
    return lead


async def list_leads(db: AsyncSession, tenant_id: uuid.UUID, page: int = 1, page_size: int = 25, status: str | None = None, source: str | None = None) -> tuple[list[Lead], int]:
    q = select(Lead).where(Lead.tenant_id == tenant_id, Lead.deleted_at.is_(None))
    if status:
        q = q.where(Lead.status == status)
    if source:
        q = q.where(Lead.source == source)
    count_q = select(func.count()).select_from(q.subquery())
    total_result = await db.execute(count_q)
    total = total_result.scalar_one()
    q = q.order_by(desc(Lead.created_at)).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(q)
    return list(result.scalars().all()), total


async def get_lead(db: AsyncSession, tenant_id: uuid.UUID, lead_id: uuid.UUID) -> Lead:
    result = await db.execute(select(Lead).where(Lead.id == lead_id, Lead.tenant_id == tenant_id, Lead.deleted_at.is_(None)))
    lead = result.scalar_one_or_none()
    if not lead:
        raise NotFoundException("Lead")
    return lead


async def update_lead(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    lead_id: uuid.UUID,
    data: LeadUpdate,
    *,
    actor_user_id: uuid.UUID | None = None,
) -> Lead:
    lead = await get_lead(db, tenant_id, lead_id)
    changed = data.model_dump(exclude_none=True)
    for field, value in changed.items():
        setattr(lead, field, value)
    db.add(lead)
    await log_action(
        db,
        action="lead.updated",
        resource="lead",
        resource_id=lead.id,
        tenant_id=tenant_id,
        user_id=actor_user_id,
        metadata={"fields": sorted(changed.keys())},
    )
    await db.commit()
    await db.refresh(lead)
    return lead


async def convert_lead_to_deal(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    lead_id: uuid.UUID,
    *,
    actor_user_id: uuid.UUID | None = None,
) -> Deal:
    from app.modules.crm.models import Deal, Customer
    lead = await get_lead(db, tenant_id, lead_id)

    # Create or find customer
    customer_result = await db.execute(
        select(Customer).where(Customer.tenant_id == tenant_id, Customer.email == lead.email)
    ) if lead.email else (await db.execute(select(Customer).where(Customer.id == uuid.uuid4())))
    customer = None
    if lead.email:
        customer = (await db.execute(select(Customer).where(Customer.tenant_id == tenant_id, Customer.email == lead.email))).scalar_one_or_none()

    if not customer:
        customer = Customer(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            first_name=lead.first_name,
            last_name=lead.last_name,
            email=lead.email,
            phone=lead.phone,
            postcode=lead.postcode,
            source=lead.source,
        )
        db.add(customer)
        await db.flush()

    # Create deal
    deal = Deal(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        customer_id=customer.id,
        lead_id=lead.id,
        title=f"{lead.first_name} - {lead.service_needed or 'Enquiry'}",
        stage="New",
        service_type=lead.service_needed,
        source=lead.source,
    )
    db.add(deal)
    lead.status = "in_crm"
    lead.converted_at = datetime.now(timezone.utc)
    db.add(lead)
    await log_action(
        db,
        action="lead.converted",
        resource="lead",
        resource_id=lead.id,
        tenant_id=tenant_id,
        user_id=actor_user_id,
        metadata={"deal_id": str(deal.id), "customer_id": str(customer.id)},
    )
    await db.commit()
    await db.refresh(deal)
    return deal


async def delete_lead(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    lead_id: uuid.UUID,
    *,
    actor_user_id: uuid.UUID | None = None,
) -> None:
    lead = await get_lead(db, tenant_id, lead_id)
    lead.deleted_at = datetime.now(timezone.utc)
    db.add(lead)
    await log_action(
        db,
        action="lead.deleted",
        resource="lead",
        resource_id=lead.id,
        tenant_id=tenant_id,
        user_id=actor_user_id,
    )
    await db.commit()


# ── Lead Request helpers ──────────────────────────────────────────────────────

def _current_month() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m")


async def get_plan_quota(db: AsyncSession, tenant_id: uuid.UUID) -> int:
    """Return the ai_lead_requests_per_month for the tenant's active plan (0 if none)."""
    from app.modules.billing.models import Subscription, SubscriptionPlan
    row = (await db.execute(
        select(SubscriptionPlan.ai_lead_requests_per_month)
        .join(Subscription, Subscription.plan_id == SubscriptionPlan.id)
        .where(
            Subscription.tenant_id == tenant_id,
            Subscription.status.in_(("active", "trialing")),
        )
    )).scalar_one_or_none()
    return int(row or 0)


async def get_lead_quota(db: AsyncSession, tenant_id: uuid.UUID):
    """Return quota info for the current calendar month."""
    from app.modules.leads.schemas import LeadQuotaResponse
    month = _current_month()
    plan_quota = await get_plan_quota(db, tenant_id)
    count = (await db.execute(
        select(func.count(LeadRequest.id)).where(
            LeadRequest.tenant_id == tenant_id,
            LeadRequest.month_year == month,
        )
    )).scalar_one()
    current = (await db.execute(
        select(LeadRequest).where(
            LeadRequest.tenant_id == tenant_id,
            LeadRequest.month_year == month,
        ).order_by(desc(LeadRequest.created_at)).limit(1)
    )).scalar_one_or_none()
    return LeadQuotaResponse(
        month_year=month,
        plan_quota=plan_quota,
        requests_this_month=int(count),
        remaining=max(0, plan_quota - int(count)),
        current_request=current,
    )


async def submit_lead_request(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    data: LeadRequestCreate,
    actor_user_id: uuid.UUID | None = None,
) -> LeadRequest:
    month = _current_month()
    plan_quota = await get_plan_quota(db, tenant_id)
    if plan_quota == 0:
        raise HTTPException(status_code=402, detail="Your current plan does not include lead requests. Please upgrade.")
    existing_count = (await db.execute(
        select(func.count(LeadRequest.id)).where(
            LeadRequest.tenant_id == tenant_id,
            LeadRequest.month_year == month,
        )
    )).scalar_one()
    if int(existing_count) >= plan_quota:
        raise HTTPException(
            status_code=429,
            detail=f"You have used all {plan_quota} lead request(s) for {month}. Quota resets next month.",
        )
    if data.requested_count > plan_quota:
        raise HTTPException(
            status_code=422,
            detail=f"Your plan allows a maximum of {plan_quota} leads per request this month.",
        )
    req = LeadRequest(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        month_year=month,
        requested_count=data.requested_count,
        tenant_notes=data.tenant_notes,
        status="pending",
    )
    db.add(req)
    await log_action(
        db,
        action="lead_request.created",
        resource="lead_request",
        resource_id=req.id,
        tenant_id=tenant_id,
        user_id=actor_user_id,
        metadata={"count": data.requested_count, "month": month},
    )
    await db.commit()
    await db.refresh(req)
    return req


async def list_lead_requests(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    limit: int = 12,
) -> list[LeadRequest]:
    result = await db.execute(
        select(LeadRequest)
        .where(LeadRequest.tenant_id == tenant_id)
        .order_by(desc(LeadRequest.created_at))
        .limit(limit)
    )
    return list(result.scalars().all())


# ── Admin-level lead request management ──────────────────────────────────────

async def admin_list_lead_requests(
    db: AsyncSession,
    status: str | None = None,
    limit: int = 100,
) -> list[LeadRequest]:
    import logging as _logging
    _log = _logging.getLogger(__name__)
    try:
        q = select(LeadRequest)
        if status:
            q = q.where(LeadRequest.status == status)
        q = q.order_by(desc(LeadRequest.created_at)).limit(limit)
        return list((await db.execute(q)).scalars().all())
    except Exception as exc:
        _log.warning("admin_list_lead_requests failed (table may not exist yet): %s", exc)
        return []


async def admin_action_lead_request(
    db: AsyncSession,
    request_id: uuid.UUID,
    action: str,
    data: LeadRequestAdminAction,
) -> LeadRequest:
    req = (await db.execute(
        select(LeadRequest).where(LeadRequest.id == request_id)
    )).scalar_one_or_none()
    if not req:
        raise NotFoundException("LeadRequest")
    if action == "approve":
        req.status = "approved"
        req.approved_count = data.approved_count if data.approved_count is not None else req.requested_count
    elif action == "reject":
        req.status = "rejected"
    elif action == "fulfill":
        req.status = "fulfilled"
        req.fulfilled_at = datetime.now(timezone.utc)
    else:
        raise HTTPException(status_code=400, detail=f"Unknown action: {action}")
    if data.admin_notes:
        req.admin_notes = data.admin_notes
    db.add(req)
    await db.commit()
    await db.refresh(req)
    return req
