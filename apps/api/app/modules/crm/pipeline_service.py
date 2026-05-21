"""CRM pipelines, stages, and unified lead+deal board."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.audit import log_action
from app.core.exceptions import NotFoundException, ValidationException
from app.modules.crm.enterprise_schemas import (
    BoardCardDeal,
    BoardCardLead,
    BoardColumn,
    BoardResponse,
    PipelineCreate,
    PipelineResponse,
    PipelineUpdate,
    StageCreate,
    StageResponse,
    StageUpdate,
)
from app.modules.crm.models import Deal, DealActivity
from app.modules.crm.pipeline_models import (
    CrmActivity,
    CrmPipeline,
    CrmStage,
    DEFAULT_PIPELINE_STAGES,
)
from app.modules.leads.models import Lead

LEGACY_STAGES = [s[0] for s in DEFAULT_PIPELINE_STAGES]


async def _get_pipeline_row(db: AsyncSession, tenant_id: uuid.UUID, pipeline_id: uuid.UUID) -> CrmPipeline:
    row = (
        await db.execute(
            select(CrmPipeline)
            .options(selectinload(CrmPipeline.stages))
            .where(CrmPipeline.id == pipeline_id, CrmPipeline.tenant_id == tenant_id)
        )
    ).scalar_one_or_none()
    if not row:
        raise NotFoundException("Pipeline")
    return row


async def _get_stage_row(db: AsyncSession, tenant_id: uuid.UUID, stage_id: uuid.UUID) -> CrmStage:
    row = (
        await db.execute(
            select(CrmStage).where(CrmStage.id == stage_id, CrmStage.tenant_id == tenant_id)
        )
    ).scalar_one_or_none()
    if not row:
        raise NotFoundException("Stage")
    return row


async def ensure_default_pipeline(db: AsyncSession, tenant_id: uuid.UUID) -> CrmPipeline:
    existing = (
        await db.execute(
            select(CrmPipeline)
            .options(selectinload(CrmPipeline.stages))
            .where(CrmPipeline.tenant_id == tenant_id, CrmPipeline.is_default == True)  # noqa: E712
        )
    ).scalar_one_or_none()
    if existing:
        return existing

    pipeline = CrmPipeline(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        name="Sales",
        is_default=True,
        is_active=True,
    )
    db.add(pipeline)
    await db.flush()
    for name, position, is_won, is_lost in DEFAULT_PIPELINE_STAGES:
        db.add(
            CrmStage(
                id=uuid.uuid4(),
                tenant_id=tenant_id,
                pipeline_id=pipeline.id,
                name=name,
                position=position,
                applies_to="both",
                is_won=is_won,
                is_lost=is_lost,
            )
        )
    await db.commit()
    await db.refresh(pipeline)
    result = await db.execute(
        select(CrmPipeline)
        .options(selectinload(CrmPipeline.stages))
        .where(CrmPipeline.id == pipeline.id)
    )
    return result.scalar_one()


def _pipeline_response(p: CrmPipeline) -> PipelineResponse:
    stages = sorted(p.stages, key=lambda s: s.position)
    return PipelineResponse(
        id=p.id,
        tenant_id=p.tenant_id,
        name=p.name,
        description=p.description,
        is_default=p.is_default,
        is_active=p.is_active,
        created_at=p.created_at,
        updated_at=p.updated_at,
        stages=[StageResponse.model_validate(s) for s in stages],
    )


async def list_pipelines(db: AsyncSession, tenant_id: uuid.UUID) -> list[PipelineResponse]:
    rows = (
        await db.execute(
            select(CrmPipeline)
            .options(selectinload(CrmPipeline.stages))
            .where(CrmPipeline.tenant_id == tenant_id, CrmPipeline.is_active == True)  # noqa: E712
            .order_by(CrmPipeline.is_default.desc(), CrmPipeline.name)
        )
    ).scalars().all()
    if not rows:
        await ensure_default_pipeline(db, tenant_id)
        return await list_pipelines(db, tenant_id)
    return [_pipeline_response(p) for p in rows]


async def create_pipeline(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    data: PipelineCreate,
    *,
    actor_user_id: uuid.UUID | None = None,
) -> PipelineResponse:
    if data.is_default:
        await db.execute(
            update(CrmPipeline)
            .where(CrmPipeline.tenant_id == tenant_id, CrmPipeline.is_default == True)  # noqa: E712
            .values(is_default=False)
        )
    pipeline = CrmPipeline(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        name=data.name,
        description=data.description,
        is_default=data.is_default,
    )
    db.add(pipeline)
    await db.flush()
    for name, position, is_won, is_lost in DEFAULT_PIPELINE_STAGES:
        db.add(
            CrmStage(
                id=uuid.uuid4(),
                tenant_id=tenant_id,
                pipeline_id=pipeline.id,
                name=name,
                position=position,
                applies_to="both",
                is_won=is_won,
                is_lost=is_lost,
            )
        )
    await log_action(
        db,
        action="crm.pipeline.created",
        resource="crm_pipeline",
        resource_id=pipeline.id,
        tenant_id=tenant_id,
        user_id=actor_user_id,
    )
    await db.commit()
    return _pipeline_response(await _get_pipeline_row(db, tenant_id, pipeline.id))


async def update_pipeline(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    pipeline_id: uuid.UUID,
    data: PipelineUpdate,
    *,
    actor_user_id: uuid.UUID | None = None,
) -> PipelineResponse:
    pipeline = await _get_pipeline_row(db, tenant_id, pipeline_id)
    if data.is_default:
        await db.execute(
            update(CrmPipeline)
            .where(CrmPipeline.tenant_id == tenant_id, CrmPipeline.id != pipeline_id)
            .values(is_default=False)
        )
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(pipeline, field, value)
    await db.commit()
    return _pipeline_response(await _get_pipeline_row(db, tenant_id, pipeline_id))


async def delete_pipeline(db: AsyncSession, tenant_id: uuid.UUID, pipeline_id: uuid.UUID) -> None:
    pipeline = await _get_pipeline_row(db, tenant_id, pipeline_id)
    if pipeline.is_default:
        raise ValidationException("Cannot delete the default pipeline")
    count = (
        await db.execute(
            select(func.count()).select_from(CrmPipeline).where(
                CrmPipeline.tenant_id == tenant_id, CrmPipeline.is_active == True  # noqa: E712
            )
        )
    ).scalar_one()
    if count <= 1:
        raise ValidationException("At least one pipeline must remain")
    pipeline.is_active = False
    await db.commit()


async def create_stage(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    pipeline_id: uuid.UUID,
    data: StageCreate,
) -> StageResponse:
    await _get_pipeline_row(db, tenant_id, pipeline_id)
    stage = CrmStage(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        pipeline_id=pipeline_id,
        **data.model_dump(),
    )
    db.add(stage)
    await db.commit()
    await db.refresh(stage)
    return StageResponse.model_validate(stage)


async def update_stage(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    stage_id: uuid.UUID,
    data: StageUpdate,
) -> StageResponse:
    stage = await _get_stage_row(db, tenant_id, stage_id)
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(stage, field, value)
    await db.commit()
    await db.refresh(stage)
    return StageResponse.model_validate(stage)


async def reorder_stages(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    pipeline_id: uuid.UUID,
    items: list[tuple[uuid.UUID, int]],
) -> list[StageResponse]:
    await _get_pipeline_row(db, tenant_id, pipeline_id)
    for stage_id, position in items:
        stage = await _get_stage_row(db, tenant_id, stage_id)
        if stage.pipeline_id != pipeline_id:
            raise ValidationException("Stage does not belong to this pipeline")
        stage.position = position
    await db.commit()
    pipeline = await _get_pipeline_row(db, tenant_id, pipeline_id)
    return [StageResponse.model_validate(s) for s in sorted(pipeline.stages, key=lambda x: x.position)]


async def resolve_pipeline(
    db: AsyncSession, tenant_id: uuid.UUID, pipeline_id: uuid.UUID | None
) -> CrmPipeline:
    if pipeline_id:
        return await _get_pipeline_row(db, tenant_id, pipeline_id)
    return await ensure_default_pipeline(db, tenant_id)


async def get_board(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    pipeline_id: uuid.UUID | None = None,
) -> BoardResponse:
    pipeline = await resolve_pipeline(db, tenant_id, pipeline_id)
    stages = sorted(pipeline.stages, key=lambda s: s.position)
    stage_ids = [s.id for s in stages]

    leads_q = select(Lead).where(
        Lead.tenant_id == tenant_id,
        Lead.deleted_at.is_(None),
        Lead.pipeline_id == pipeline.id,
    )
    if stage_ids:
        leads_q = leads_q.where(Lead.stage_id.in_(stage_ids))
    leads = (await db.execute(leads_q.order_by(Lead.stage_order, Lead.created_at.desc()))).scalars().all()

    deals_q = (
        select(Deal)
        .options(selectinload(Deal.customer))
        .where(Deal.tenant_id == tenant_id, Deal.deleted_at.is_(None), Deal.pipeline_id == pipeline.id)
    )
    if stage_ids:
        deals_q = deals_q.where(Deal.stage_id.in_(stage_ids))
    deals = (await db.execute(deals_q.order_by(Deal.stage_order, Deal.created_at.desc()))).scalars().all()

    leads_by_stage: dict[uuid.UUID, list[BoardCardLead]] = {s.id: [] for s in stages}
    deals_by_stage: dict[uuid.UUID, list[BoardCardDeal]] = {s.id: [] for s in stages}
    total_value = 0

    for lead in leads:
        sid = lead.stage_id or (stages[0].id if stages else None)
        if sid and sid in leads_by_stage:
            leads_by_stage[sid].append(
                BoardCardLead(
                    id=lead.id,
                    title=f"{lead.first_name} {lead.last_name or ''}".strip(),
                    stage_id=lead.stage_id,
                    stage_order=lead.stage_order,
                    email=lead.email,
                    phone=lead.phone,
                    source=lead.source,
                    score=lead.score,
                    score_label=lead.score_label,
                    assigned_user_id=lead.assigned_user_id,
                    created_at=lead.created_at,
                )
            )

    for deal in deals:
        sid = deal.stage_id or (stages[0].id if stages else None)
        total_value += deal.value_pence
        if sid and sid in deals_by_stage:
            customer_name = None
            if deal.customer:
                customer_name = f"{deal.customer.first_name} {deal.customer.last_name or ''}".strip()
            deals_by_stage[sid].append(
                BoardCardDeal(
                    id=deal.id,
                    title=deal.title,
                    stage_id=deal.stage_id,
                    stage_order=deal.stage_order,
                    stage=deal.stage,
                    customer_name=customer_name,
                    value_pence=deal.value_pence,
                    assigned_user_id=deal.assigned_user_id,
                    created_at=deal.created_at,
                )
            )

    columns = [
        BoardColumn(
            stage=StageResponse.model_validate(stage),
            leads=leads_by_stage.get(stage.id, []),
            deals=deals_by_stage.get(stage.id, []),
        )
        for stage in stages
    ]

    return BoardResponse(
        pipeline=_pipeline_response(pipeline),
        columns=columns,
        total_leads=len(leads),
        total_deals=len(deals),
        total_value_pence=total_value,
    )


async def _record_activity(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    entity_type: str,
    entity_id: uuid.UUID,
    activity_type: str,
    body: str,
    user_id: uuid.UUID | None,
    metadata: dict | None = None,
) -> None:
    db.add(
        CrmActivity(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            entity_type=entity_type,
            entity_id=entity_id,
            activity_type=activity_type,
            body=body,
            user_id=user_id,
            extra_metadata=metadata or {},
        )
    )


async def move_board_card(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    card_type: str,
    card_id: uuid.UUID,
    stage_id: uuid.UUID,
    stage_order: int,
    user_id: uuid.UUID | None = None,
) -> None:
    stage = await _get_stage_row(db, tenant_id, stage_id)
    old_stage_name: str | None = None

    if card_type == "lead":
        lead = (
            await db.execute(
                select(Lead).where(Lead.id == card_id, Lead.tenant_id == tenant_id, Lead.deleted_at.is_(None))
            )
        ).scalar_one_or_none()
        if not lead:
            raise NotFoundException("Lead")
        if lead.stage_id:
            prev = await _get_stage_row(db, tenant_id, lead.stage_id)
            old_stage_name = prev.name
        lead.pipeline_id = stage.pipeline_id
        lead.stage_id = stage.id
        lead.stage_order = stage_order
        await _record_activity(
            db,
            tenant_id,
            "lead",
            lead.id,
            "stage_changed",
            f"Moved from {old_stage_name or 'unknown'} to {stage.name}",
            user_id,
            {"from": old_stage_name, "to": stage.name, "stage_id": str(stage.id)},
        )
        await log_action(
            db,
            action="lead.stage_changed",
            resource="lead",
            resource_id=lead.id,
            tenant_id=tenant_id,
            user_id=user_id,
            metadata={"stage": stage.name},
        )
        from app.workers.queue import enqueue

        await enqueue(
            "trigger_automation_for_event",
            tenant_id=str(tenant_id),
            event="lead_stage_changed",
            entity_id=str(lead.id),
            entity_type="lead",
        )

    elif card_type == "deal":
        deal = (
            await db.execute(
                select(Deal).where(Deal.id == card_id, Deal.tenant_id == tenant_id, Deal.deleted_at.is_(None))
            )
        ).scalar_one_or_none()
        if not deal:
            raise NotFoundException("Deal")
        old_stage_name = deal.stage
        deal.pipeline_id = stage.pipeline_id
        deal.stage_id = stage.id
        deal.stage = stage.name
        deal.stage_order = stage_order
        if stage.is_won and not deal.completed_at:
            deal.completed_at = datetime.now(timezone.utc)
            from app.workers.queue import enqueue

            await enqueue("send_review_request", deal_id=str(deal.id), tenant_id=str(tenant_id), _defer_by=7200)
            await enqueue("generate_social_post", deal_id=str(deal.id), tenant_id=str(tenant_id))
            await enqueue(
                "trigger_automation_for_event",
                tenant_id=str(tenant_id),
                event="job_completed",
                entity_id=str(deal.id),
            )
        db.add(
            DealActivity(
                id=uuid.uuid4(),
                tenant_id=tenant_id,
                deal_id=deal.id,
                user_id=user_id,
                type="stage_changed",
                body=f"Moved from {old_stage_name} to {stage.name}",
                extra_metadata={"from": old_stage_name, "to": stage.name, "stage_id": str(stage.id)},
            )
        )
        await _record_activity(
            db,
            tenant_id,
            "deal",
            deal.id,
            "stage_changed",
            f"Moved from {old_stage_name} to {stage.name}",
            user_id,
            {"from": old_stage_name, "to": stage.name},
        )
        await log_action(
            db,
            action="deal.stage_changed",
            resource="deal",
            resource_id=deal.id,
            tenant_id=tenant_id,
            user_id=user_id,
            metadata={"from": old_stage_name, "to": stage.name},
        )
        from app.workers.queue import enqueue

        await enqueue(
            "trigger_automation_for_event",
            tenant_id=str(tenant_id),
            event="deal_stage_changed",
            entity_id=str(deal.id),
        )
    else:
        raise ValidationException("card_type must be lead or deal")

    await db.commit()


async def move_deal_by_stage(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    deal_id: uuid.UUID,
    *,
    stage_id: uuid.UUID | None = None,
    stage_name: str | None = None,
    stage_order: int = 0,
    user_id: uuid.UUID | None = None,
) -> Deal:
    if stage_id:
        await move_board_card(db, tenant_id, "deal", deal_id, stage_id, stage_order, user_id)
        from app.modules.crm.service import get_deal

        return await get_deal(db, tenant_id, deal_id)
    if stage_name:
        pipeline = await ensure_default_pipeline(db, tenant_id)
        match = next((s for s in pipeline.stages if s.name == stage_name), None)
        if not match:
            raise NotFoundException("Stage")
        await move_board_card(db, tenant_id, "deal", deal_id, match.id, stage_order, user_id)
        from app.modules.crm.service import get_deal

        return await get_deal(db, tenant_id, deal_id)
    raise ValidationException("stage_id or stage required")
