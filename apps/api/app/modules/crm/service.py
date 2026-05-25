import uuid
from datetime import datetime, timezone
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.core.audit import log_action
from app.core.exceptions import NotFoundException
from app.modules.crm.models import Customer, Deal, DealActivity
from app.modules.crm.schemas import CustomerCreate, CustomerUpdate, DealCreate, DealUpdate

STAGES = ["New", "Contacted", "Quoted", "Booked", "Completed", "Lost"]


async def list_customers(db: AsyncSession, tenant_id: uuid.UUID, page: int = 1, page_size: int = 25) -> tuple[list[Customer], int]:
    q = select(Customer).where(Customer.tenant_id == tenant_id, Customer.deleted_at.is_(None))
    total = (await db.execute(select(func.count()).select_from(q.subquery()))).scalar_one()
    items = (await db.execute(q.order_by(Customer.created_at.desc()).offset((page-1)*page_size).limit(page_size))).scalars().all()
    return list(items), total


async def create_customer(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    data: CustomerCreate,
    *,
    actor_user_id: uuid.UUID | None = None,
    commit: bool = True,
) -> Customer:
    c = Customer(id=uuid.uuid4(), tenant_id=tenant_id, **data.model_dump())
    db.add(c)
    await log_action(
        db,
        action="customer.created",
        resource="customer",
        resource_id=c.id,
        tenant_id=tenant_id,
        user_id=actor_user_id,
        metadata={"source": getattr(data, "source", None)},
    )
    if commit:
        await db.commit()
    else:
        await db.flush()
    await db.refresh(c)
    return c


async def get_customer(db: AsyncSession, tenant_id: uuid.UUID, customer_id: uuid.UUID) -> Customer:
    result = await db.execute(select(Customer).where(Customer.id == customer_id, Customer.tenant_id == tenant_id))
    c = result.scalar_one_or_none()
    if not c:
        raise NotFoundException("Customer")
    return c


async def update_customer(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    customer_id: uuid.UUID,
    data: CustomerUpdate,
    *,
    actor_user_id: uuid.UUID | None = None,
) -> Customer:
    c = await get_customer(db, tenant_id, customer_id)
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(c, field, value)
    await log_action(
        db,
        action="customer.updated",
        resource="customer",
        resource_id=c.id,
        tenant_id=tenant_id,
        user_id=actor_user_id,
        metadata={"fields": sorted(data.model_dump(exclude_none=True).keys())},
    )
    await db.commit()
    await db.refresh(c)
    return c


async def delete_customer(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    customer_id: uuid.UUID,
    *,
    actor_user_id: uuid.UUID | None = None,
) -> None:
    c = await get_customer(db, tenant_id, customer_id)
    c.deleted_at = datetime.now(timezone.utc)
    await log_action(
        db,
        action="customer.deleted",
        resource="customer",
        resource_id=c.id,
        tenant_id=tenant_id,
        user_id=actor_user_id,
    )
    await db.commit()


async def get_pipeline(db: AsyncSession, tenant_id: uuid.UUID) -> dict:
    result = await db.execute(
        select(Deal).options(selectinload(Deal.customer), selectinload(Deal.activities))
        .where(Deal.tenant_id == tenant_id, Deal.deleted_at.is_(None))
        .order_by(Deal.stage_order)
    )
    deals = result.scalars().all()
    columns: dict[str, list] = {s: [] for s in STAGES}
    total_value = 0
    for d in deals:
        if d.stage in columns:
            columns[d.stage].append(d)
        total_value += d.value_pence
    return {"columns": columns, "total_deals": len(deals), "total_value_pence": total_value}


async def create_deal(db: AsyncSession, tenant_id: uuid.UUID, data: DealCreate, user_id: uuid.UUID | None = None) -> Deal:
    from app.modules.crm.pipeline_service import ensure_default_pipeline

    payload = data.model_dump()
    if not payload.get("pipeline_id") or not payload.get("stage_id"):
        pipeline = await ensure_default_pipeline(db, tenant_id)
        stage = next((s for s in pipeline.stages if s.name == payload.get("stage", "New")), None)
        if not stage and pipeline.stages:
            stage = sorted(pipeline.stages, key=lambda s: s.position)[0]
        if stage:
            payload["pipeline_id"] = pipeline.id
            payload["stage_id"] = stage.id
            payload["stage"] = stage.name
    deal = Deal(id=uuid.uuid4(), tenant_id=tenant_id, **payload)
    db.add(deal)
    await db.flush()
    activity = DealActivity(id=uuid.uuid4(), tenant_id=tenant_id, deal_id=deal.id, user_id=user_id, type="created", body="Deal created")
    db.add(activity)
    await log_action(
        db,
        action="deal.created",
        resource="deal",
        resource_id=deal.id,
        tenant_id=tenant_id,
        user_id=user_id,
        metadata={"value_pence": deal.value_pence, "stage": deal.stage},
    )
    await db.commit()
    await db.refresh(deal)
    return deal


async def get_deal(db: AsyncSession, tenant_id: uuid.UUID, deal_id: uuid.UUID) -> Deal:
    result = await db.execute(
        select(Deal).options(selectinload(Deal.customer), selectinload(Deal.activities))
        .where(Deal.id == deal_id, Deal.tenant_id == tenant_id, Deal.deleted_at.is_(None))
    )
    deal = result.scalar_one_or_none()
    if not deal:
        raise NotFoundException("Deal")
    return deal


async def move_deal(db: AsyncSession, tenant_id: uuid.UUID, deal_id: uuid.UUID, stage: str, stage_order: int, user_id: uuid.UUID | None = None) -> Deal:
    deal = await get_deal(db, tenant_id, deal_id)
    old_stage = deal.stage
    deal.stage = stage
    deal.stage_order = stage_order
    if stage == "Completed" and not deal.completed_at:
        deal.completed_at = datetime.now(timezone.utc)
        from app.workers.queue import enqueue
        from app.modules.automation import service as automation_service

        has_review_automation = await automation_service.tenant_has_active_automation(
            db, tenant_id, "job_completed"
        )
        if not has_review_automation:
            await enqueue("send_review_request", deal_id=str(deal.id), tenant_id=str(tenant_id), _defer_by=7200)
        await enqueue("generate_social_post", deal_id=str(deal.id), tenant_id=str(tenant_id))
        await enqueue("trigger_automation_for_event", tenant_id=str(tenant_id), event="job_completed", entity_id=str(deal.id))
    db.add(deal)
    activity = DealActivity(id=uuid.uuid4(), tenant_id=tenant_id, deal_id=deal.id, user_id=user_id, type="stage_changed", body=f"Moved from {old_stage} to {stage}", metadata={"from": old_stage, "to": stage})
    db.add(activity)
    await log_action(
        db,
        action="deal.stage_changed",
        resource="deal",
        resource_id=deal.id,
        tenant_id=tenant_id,
        user_id=user_id,
        metadata={"from": old_stage, "to": stage},
    )
    await db.commit()
    await db.refresh(deal)
    return deal


async def update_deal(db: AsyncSession, tenant_id: uuid.UUID, deal_id: uuid.UUID, data: DealUpdate, user_id: uuid.UUID | None = None) -> Deal:
    deal = await get_deal(db, tenant_id, deal_id)
    changed = data.model_dump(exclude_none=True)
    for field, value in changed.items():
        setattr(deal, field, value)
    activity = DealActivity(id=uuid.uuid4(), tenant_id=tenant_id, deal_id=deal.id, user_id=user_id, type="updated", body="Deal updated")
    db.add(activity)
    db.add(deal)
    await log_action(
        db,
        action="deal.updated",
        resource="deal",
        resource_id=deal.id,
        tenant_id=tenant_id,
        user_id=user_id,
        metadata={"fields": sorted(changed.keys())},
    )
    await db.commit()
    await db.refresh(deal)
    return deal


async def add_note(db: AsyncSession, tenant_id: uuid.UUID, deal_id: uuid.UUID, note: str, user_id: uuid.UUID | None = None) -> DealActivity:
    deal = await get_deal(db, tenant_id, deal_id)
    activity = DealActivity(id=uuid.uuid4(), tenant_id=tenant_id, deal_id=deal.id, user_id=user_id, type="note", body=note)
    db.add(activity)
    await db.commit()
    await db.refresh(activity)
    return activity
