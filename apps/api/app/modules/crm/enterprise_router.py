"""CRM enterprise API routes (pipelines, board, tags, bulk, dashboard)."""
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import CurrentTenantContext, require_permission
from app.modules.crm import enterprise_service, pipeline_service
from app.modules.crm.enterprise_schemas import (
    ActivityCreate,
    ActivityResponse,
    AssignmentCreate,
    AttachmentCreate,
    AttachmentResponse,
    BoardMoveRequest,
    BoardResponse,
    BulkUpdateRequest,
    CustomFieldDefCreate,
    CustomFieldDefResponse,
    CustomFieldValueSet,
    DashboardResponse,
    DuplicateCandidateResponse,
    MergeRequest,
    PipelineCreate,
    PipelineResponse,
    PipelineUpdate,
    SavedFilterCreate,
    SavedFilterResponse,
    ScoreRuleCreate,
    ScoreRuleResponse,
    StageCreate,
    StageReorderItem,
    StageResponse,
    StageUpdate,
    TagAssignRequest,
    TagCreate,
    TagResponse,
)
from app.modules.crm.pipeline_models import CrmImportJob
router = APIRouter(prefix="/crm", tags=["CRM Enterprise"])


# ── Pipelines ─────────────────────────────────────────────────────────────────

@router.get("/pipelines", response_model=list[PipelineResponse])
async def list_pipelines(
    ctx: CurrentTenantContext,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_permission("crm.read")),
):
    _, tenant, _ = ctx
    return await pipeline_service.list_pipelines(db, tenant.id)


@router.post("/pipelines", response_model=PipelineResponse, status_code=201)
async def create_pipeline(
    data: PipelineCreate,
    ctx: CurrentTenantContext,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_permission("crm.write")),
):
    user, tenant, _ = ctx
    return await pipeline_service.create_pipeline(db, tenant.id, data, actor_user_id=user.id)


@router.patch("/pipelines/{pipeline_id}", response_model=PipelineResponse)
async def update_pipeline(
    pipeline_id: UUID,
    data: PipelineUpdate,
    ctx: CurrentTenantContext,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_permission("crm.write")),
):
    user, tenant, _ = ctx
    return await pipeline_service.update_pipeline(db, tenant.id, pipeline_id, data, actor_user_id=user.id)


@router.delete("/pipelines/{pipeline_id}", status_code=204)
async def delete_pipeline(
    pipeline_id: UUID,
    ctx: CurrentTenantContext,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_permission("crm.delete")),
):
    _, tenant, _ = ctx
    await pipeline_service.delete_pipeline(db, tenant.id, pipeline_id)


@router.post("/pipelines/{pipeline_id}/stages", response_model=StageResponse, status_code=201)
async def create_stage(
    pipeline_id: UUID,
    data: StageCreate,
    ctx: CurrentTenantContext,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_permission("crm.write")),
):
    _, tenant, _ = ctx
    return await pipeline_service.create_stage(db, tenant.id, pipeline_id, data)


@router.patch("/stages/{stage_id}", response_model=StageResponse)
async def update_stage(
    stage_id: UUID,
    data: StageUpdate,
    ctx: CurrentTenantContext,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_permission("crm.write")),
):
    _, tenant, _ = ctx
    return await pipeline_service.update_stage(db, tenant.id, stage_id, data)


class StageReorderBody(BaseModel):
    items: list[StageReorderItem]


@router.post("/pipelines/{pipeline_id}/stages/reorder", response_model=list[StageResponse])
async def reorder_stages(
    pipeline_id: UUID,
    body: StageReorderBody,
    ctx: CurrentTenantContext,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_permission("crm.write")),
):
    _, tenant, _ = ctx
    return await pipeline_service.reorder_stages(
        db, tenant.id, pipeline_id, [(i.stage_id, i.position) for i in body.items]
    )


# ── Unified board ─────────────────────────────────────────────────────────────

@router.get("/board", response_model=BoardResponse)
async def get_board(
    ctx: CurrentTenantContext,
    db: AsyncSession = Depends(get_db),
    pipeline_id: UUID | None = None,
    _: None = Depends(require_permission("crm.read")),
):
    _, tenant, _ = ctx
    return await pipeline_service.get_board(db, tenant.id, pipeline_id)


@router.post("/board/move", status_code=204)
async def move_board_card(
    data: BoardMoveRequest,
    ctx: CurrentTenantContext,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_permission("crm.write")),
):
    user, tenant, _ = ctx
    await pipeline_service.move_board_card(
        db, tenant.id, data.card_type, data.card_id, data.stage_id, data.stage_order, user.id
    )


# ── Activities ────────────────────────────────────────────────────────────────

@router.get("/activities", response_model=list[ActivityResponse])
async def list_activities(
    ctx: CurrentTenantContext,
    db: AsyncSession = Depends(get_db),
    entity_type: str = Query(...),
    entity_id: UUID = Query(...),
    _: None = Depends(require_permission("crm.read")),
):
    _, tenant, _ = ctx
    return await enterprise_service.list_activities(db, tenant.id, entity_type, entity_id)


@router.post("/activities", response_model=ActivityResponse, status_code=201)
async def create_activity(
    data: ActivityCreate,
    ctx: CurrentTenantContext,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_permission("crm.write")),
):
    user, tenant, _ = ctx
    return await enterprise_service.create_activity(db, tenant.id, data, user.id)


# ── Tags ──────────────────────────────────────────────────────────────────────

@router.get("/tags", response_model=list[TagResponse])
async def list_tags(
    ctx: CurrentTenantContext,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_permission("crm.read")),
):
    _, tenant, _ = ctx
    return await enterprise_service.list_tags(db, tenant.id)


@router.post("/tags", response_model=TagResponse, status_code=201)
async def create_tag(
    data: TagCreate,
    ctx: CurrentTenantContext,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_permission("crm.write")),
):
    _, tenant, _ = ctx
    return await enterprise_service.create_tag(db, tenant.id, data)


@router.post("/tags/assign", status_code=204)
async def assign_tags(
    data: TagAssignRequest,
    ctx: CurrentTenantContext,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_permission("crm.write")),
):
    _, tenant, _ = ctx
    await enterprise_service.assign_tags(db, tenant.id, data)


@router.get("/tags/entity", response_model=list[TagResponse])
async def entity_tags(
    ctx: CurrentTenantContext,
    db: AsyncSession = Depends(get_db),
    entity_type: str = Query(...),
    entity_id: UUID = Query(...),
    _: None = Depends(require_permission("crm.read")),
):
    _, tenant, _ = ctx
    return await enterprise_service.get_entity_tags(db, tenant.id, entity_type, entity_id)


# ── Custom fields ─────────────────────────────────────────────────────────────

@router.get("/custom-fields", response_model=list[CustomFieldDefResponse])
async def list_custom_fields(
    ctx: CurrentTenantContext,
    db: AsyncSession = Depends(get_db),
    entity_type: str | None = None,
    _: None = Depends(require_permission("crm.read")),
):
    _, tenant, _ = ctx
    return await enterprise_service.list_field_definitions(db, tenant.id, entity_type)


@router.post("/custom-fields", response_model=CustomFieldDefResponse, status_code=201)
async def create_custom_field(
    data: CustomFieldDefCreate,
    ctx: CurrentTenantContext,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_permission("crm.settings")),
):
    _, tenant, _ = ctx
    return await enterprise_service.create_field_definition(db, tenant.id, data)


@router.put("/custom-fields/values", status_code=204)
async def set_custom_field_value(
    data: CustomFieldValueSet,
    ctx: CurrentTenantContext,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_permission("crm.write")),
):
    _, tenant, _ = ctx
    await enterprise_service.set_field_value(db, tenant.id, data)


# ── Saved filters ─────────────────────────────────────────────────────────────

@router.get("/filters", response_model=list[SavedFilterResponse])
async def list_filters(
    ctx: CurrentTenantContext,
    db: AsyncSession = Depends(get_db),
    entity_type: str | None = None,
    _: None = Depends(require_permission("crm.read")),
):
    _, tenant, _ = ctx
    return await enterprise_service.list_saved_filters(db, tenant.id, entity_type)


@router.post("/filters", response_model=SavedFilterResponse, status_code=201)
async def create_filter(
    data: SavedFilterCreate,
    ctx: CurrentTenantContext,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_permission("crm.write")),
):
    user, tenant, _ = ctx
    return await enterprise_service.create_saved_filter(db, tenant.id, data, user.id)


@router.delete("/filters/{filter_id}", status_code=204)
async def delete_filter(
    filter_id: UUID,
    ctx: CurrentTenantContext,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_permission("crm.write")),
):
    _, tenant, _ = ctx
    await enterprise_service.delete_saved_filter(db, tenant.id, filter_id)


# ── Score rules ───────────────────────────────────────────────────────────────

@router.get("/score-rules", response_model=list[ScoreRuleResponse])
async def list_score_rules(
    ctx: CurrentTenantContext,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_permission("crm.read")),
):
    _, tenant, _ = ctx
    return await enterprise_service.list_score_rules(db, tenant.id)


@router.post("/score-rules", response_model=ScoreRuleResponse, status_code=201)
async def create_score_rule(
    data: ScoreRuleCreate,
    ctx: CurrentTenantContext,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_permission("crm.write")),
):
    _, tenant, _ = ctx
    return await enterprise_service.create_score_rule(db, tenant.id, data)


@router.post("/leads/{lead_id}/apply-scores")
async def apply_lead_scores(
    lead_id: UUID,
    ctx: CurrentTenantContext,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_permission("leads.score")),
):
    _, tenant, _ = ctx
    lead = await enterprise_service.apply_score_rules(db, tenant.id, lead_id)
    return {"id": str(lead.id), "score": lead.score, "score_label": lead.score_label}


@router.post("/leads/{lead_id}/enrich")
async def enrich_lead(
    lead_id: UUID,
    ctx: CurrentTenantContext,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_permission("ai.lead_score")),
):
    _, tenant, _ = ctx
    return await enterprise_service.enrich_lead_ai(db, tenant.id, lead_id)


# ── Bulk & merge ──────────────────────────────────────────────────────────────

@router.post("/bulk")
async def bulk_update(
    data: BulkUpdateRequest,
    ctx: CurrentTenantContext,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_permission("crm.bulk")),
):
    _, tenant, _ = ctx
    count = await enterprise_service.bulk_update(db, tenant.id, data)
    return {"updated": count}


@router.post("/duplicates/scan", response_model=list[DuplicateCandidateResponse])
async def scan_duplicates(
    ctx: CurrentTenantContext,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_permission("crm.read")),
):
    _, tenant, _ = ctx
    return await enterprise_service.scan_duplicate_customers(db, tenant.id)


@router.post("/merge")
async def merge_entities(
    data: MergeRequest,
    ctx: CurrentTenantContext,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_permission("crm.merge")),
):
    user, tenant, _ = ctx
    primary_id = await enterprise_service.merge_entities(
        db, tenant.id, data.entity_type, data.primary_id, data.duplicate_id, user.id
    )
    return {"primary_id": str(primary_id)}


# ── Dashboard ─────────────────────────────────────────────────────────────────

@router.get("/dashboard", response_model=DashboardResponse)
async def crm_dashboard(
    ctx: CurrentTenantContext,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_permission("crm.read")),
):
    _, tenant, _ = ctx
    return await enterprise_service.get_dashboard(db, tenant.id)


# ── Attachments ───────────────────────────────────────────────────────────────

@router.get("/attachments", response_model=list[AttachmentResponse])
async def list_attachments(
    ctx: CurrentTenantContext,
    db: AsyncSession = Depends(get_db),
    entity_type: str = Query(...),
    entity_id: UUID = Query(...),
    _: None = Depends(require_permission("crm.read")),
):
    _, tenant, _ = ctx
    return await enterprise_service.list_attachments(db, tenant.id, entity_type, entity_id)


@router.post("/attachments", response_model=AttachmentResponse, status_code=201)
async def create_attachment(
    data: AttachmentCreate,
    ctx: CurrentTenantContext,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_permission("crm.write")),
):
    user, tenant, _ = ctx
    return await enterprise_service.create_attachment(db, tenant.id, data, user.id)


# ── Assignments ───────────────────────────────────────────────────────────────

@router.post("/assignments", status_code=201)
async def create_assignment(
    data: AssignmentCreate,
    ctx: CurrentTenantContext,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_permission("crm.assign")),
):
    _, tenant, _ = ctx
    await enterprise_service.create_assignment(db, tenant.id, data)


# ── Customer profile (bookings read-only) ─────────────────────────────────────

@router.get("/customers/{customer_id}/bookings")
async def customer_bookings(
    customer_id: UUID,
    ctx: CurrentTenantContext,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_permission("crm.read")),
):
    _, tenant, _ = ctx
    return await enterprise_service.list_customer_bookings(db, tenant.id, customer_id)


# ── Import / export ───────────────────────────────────────────────────────────

@router.get("/export/leads")
async def export_leads(
    ctx: CurrentTenantContext,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_permission("customers.export")),
):
    _, tenant, _ = ctx
    from fastapi.responses import PlainTextResponse

    csv_data = await enterprise_service.export_leads_csv(db, tenant.id)
    return PlainTextResponse(csv_data, media_type="text/csv")


class ImportLeadsBody(BaseModel):
    csv: str


@router.post("/import/leads")
async def import_leads(
    body: ImportLeadsBody,
    ctx: CurrentTenantContext,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_permission("crm.import")),
):
    user, tenant, _ = ctx
    job = await enterprise_service.import_leads_csv(db, tenant.id, body.csv, user.id)
    return {"job_id": str(job.id), "status": job.status, "row_count": job.row_count}
