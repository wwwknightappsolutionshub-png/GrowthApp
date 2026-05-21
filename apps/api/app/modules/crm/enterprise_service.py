"""CRM enterprise: tags, activities, filters, bulk, merge, dashboard, scoring."""
from __future__ import annotations

import csv
import io
import uuid
from datetime import datetime, timezone

from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import log_action
from app.core.exceptions import NotFoundException, ValidationException
from app.modules.booking.models import Booking
from app.modules.crm.enterprise_schemas import (
    ActivityCreate,
    ActivityResponse,
    AssignmentCreate,
    AttachmentCreate,
    AttachmentResponse,
    BulkUpdateRequest,
    CustomFieldDefCreate,
    CustomFieldDefResponse,
    CustomFieldValueSet,
    DashboardResponse,
    DuplicateCandidateResponse,
    SavedFilterCreate,
    SavedFilterResponse,
    ScoreRuleCreate,
    ScoreRuleResponse,
    TagAssignRequest,
    TagCreate,
    TagResponse,
)
from app.modules.crm.models import Customer, Deal
from app.modules.crm.pipeline_models import (
    CrmActivity,
    CrmAssignment,
    CrmAttachment,
    CrmCustomFieldDefinition,
    CrmCustomFieldValue,
    CrmDuplicateCandidate,
    CrmImportJob,
    CrmSavedFilter,
    CrmScoreRule,
    CrmTag,
    CrmTagAssignment,
)
from app.modules.crm.pipeline_service import ensure_default_pipeline
from app.modules.leads.models import Lead


async def list_activities(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    entity_type: str,
    entity_id: uuid.UUID,
    limit: int = 50,
) -> list[ActivityResponse]:
    rows = (
        await db.execute(
            select(CrmActivity)
            .where(
                CrmActivity.tenant_id == tenant_id,
                CrmActivity.entity_type == entity_type,
                CrmActivity.entity_id == entity_id,
            )
            .order_by(CrmActivity.created_at.desc())
            .limit(limit)
        )
    ).scalars().all()
    return [ActivityResponse.model_validate(r) for r in rows]


async def create_activity(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    data: ActivityCreate,
    user_id: uuid.UUID | None,
) -> ActivityResponse:
    row = CrmActivity(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        entity_type=data.entity_type,
        entity_id=data.entity_id,
        activity_type=data.activity_type,
        title=data.title,
        body=data.body,
        user_id=user_id,
        extra_metadata=data.metadata,
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return ActivityResponse.model_validate(row)


# ── Tags ──────────────────────────────────────────────────────────────────────

async def list_tags(db: AsyncSession, tenant_id: uuid.UUID) -> list[TagResponse]:
    rows = (await db.execute(select(CrmTag).where(CrmTag.tenant_id == tenant_id).order_by(CrmTag.name))).scalars().all()
    return [TagResponse.model_validate(r) for r in rows]


async def create_tag(db: AsyncSession, tenant_id: uuid.UUID, data: TagCreate) -> TagResponse:
    row = CrmTag(id=uuid.uuid4(), tenant_id=tenant_id, name=data.name, color=data.color)
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return TagResponse.model_validate(row)


async def assign_tags(db: AsyncSession, tenant_id: uuid.UUID, data: TagAssignRequest) -> None:
    await db.execute(
        delete(CrmTagAssignment).where(
            CrmTagAssignment.tenant_id == tenant_id,
            CrmTagAssignment.entity_type == data.entity_type,
            CrmTagAssignment.entity_id == data.entity_id,
        )
    )
    for tag_id in data.tag_ids:
        db.add(
            CrmTagAssignment(
                id=uuid.uuid4(),
                tenant_id=tenant_id,
                tag_id=tag_id,
                entity_type=data.entity_type,
                entity_id=data.entity_id,
            )
        )
    await db.commit()


async def get_entity_tags(db: AsyncSession, tenant_id: uuid.UUID, entity_type: str, entity_id: uuid.UUID) -> list[TagResponse]:
    rows = (
        await db.execute(
            select(CrmTag)
            .join(CrmTagAssignment, CrmTagAssignment.tag_id == CrmTag.id)
            .where(
                CrmTagAssignment.tenant_id == tenant_id,
                CrmTagAssignment.entity_type == entity_type,
                CrmTagAssignment.entity_id == entity_id,
            )
        )
    ).scalars().all()
    return [TagResponse.model_validate(r) for r in rows]


# ── Custom fields ───────────────────────────────────────────────────────────

async def list_field_definitions(
    db: AsyncSession, tenant_id: uuid.UUID, entity_type: str | None = None
) -> list[CustomFieldDefResponse]:
    q = select(CrmCustomFieldDefinition).where(CrmCustomFieldDefinition.tenant_id == tenant_id)
    if entity_type:
        q = q.where(CrmCustomFieldDefinition.entity_type == entity_type)
    rows = (await db.execute(q.order_by(CrmCustomFieldDefinition.position))).scalars().all()
    return [CustomFieldDefResponse.model_validate(r) for r in rows]


async def create_field_definition(
    db: AsyncSession, tenant_id: uuid.UUID, data: CustomFieldDefCreate
) -> CustomFieldDefResponse:
    row = CrmCustomFieldDefinition(id=uuid.uuid4(), tenant_id=tenant_id, **data.model_dump())
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return CustomFieldDefResponse.model_validate(row)


async def set_field_value(db: AsyncSession, tenant_id: uuid.UUID, data: CustomFieldValueSet) -> None:
    existing = (
        await db.execute(
            select(CrmCustomFieldValue).where(
                CrmCustomFieldValue.tenant_id == tenant_id,
                CrmCustomFieldValue.definition_id == data.definition_id,
                CrmCustomFieldValue.entity_id == data.entity_id,
            )
        )
    ).scalar_one_or_none()
    payload = {
        "value_text": data.value_text,
        "value_number": data.value_number,
        "value_bool": data.value_bool,
        "value_date": data.value_date,
        "value_json": data.value_json,
    }
    if existing:
        for k, v in payload.items():
            setattr(existing, k, v)
    else:
        db.add(
            CrmCustomFieldValue(
                id=uuid.uuid4(),
                tenant_id=tenant_id,
                definition_id=data.definition_id,
                entity_type=data.entity_type,
                entity_id=data.entity_id,
                **payload,
            )
        )
    await db.commit()


# ── Saved filters ───────────────────────────────────────────────────────────

async def list_saved_filters(db: AsyncSession, tenant_id: uuid.UUID, entity_type: str | None = None) -> list[SavedFilterResponse]:
    q = select(CrmSavedFilter).where(CrmSavedFilter.tenant_id == tenant_id)
    if entity_type:
        q = q.where(CrmSavedFilter.entity_type == entity_type)
    rows = (await db.execute(q.order_by(CrmSavedFilter.name))).scalars().all()
    return [SavedFilterResponse.model_validate(r) for r in rows]


async def create_saved_filter(
    db: AsyncSession, tenant_id: uuid.UUID, data: SavedFilterCreate, user_id: uuid.UUID | None
) -> SavedFilterResponse:
    row = CrmSavedFilter(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        user_id=user_id,
        **data.model_dump(),
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return SavedFilterResponse.model_validate(row)


async def delete_saved_filter(db: AsyncSession, tenant_id: uuid.UUID, filter_id: uuid.UUID) -> None:
    row = (
        await db.execute(
            select(CrmSavedFilter).where(CrmSavedFilter.id == filter_id, CrmSavedFilter.tenant_id == tenant_id)
        )
    ).scalar_one_or_none()
    if not row:
        raise NotFoundException("Filter")
    await db.delete(row)
    await db.commit()


# ── Score rules ─────────────────────────────────────────────────────────────

async def list_score_rules(db: AsyncSession, tenant_id: uuid.UUID) -> list[ScoreRuleResponse]:
    rows = (
        await db.execute(
            select(CrmScoreRule)
            .where(CrmScoreRule.tenant_id == tenant_id)
            .order_by(CrmScoreRule.priority, CrmScoreRule.created_at)
        )
    ).scalars().all()
    return [ScoreRuleResponse.model_validate(r) for r in rows]


async def create_score_rule(db: AsyncSession, tenant_id: uuid.UUID, data: ScoreRuleCreate) -> ScoreRuleResponse:
    row = CrmScoreRule(id=uuid.uuid4(), tenant_id=tenant_id, **data.model_dump())
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return ScoreRuleResponse.model_validate(row)


def _match_condition(lead: Lead, conditions: dict) -> bool:
    """Simple rule: {field, op, value} or {all: [...]}."""
    if "all" in conditions:
        return all(_match_condition(lead, c) for c in conditions.get("all", []))
    field = conditions.get("field")
    op = conditions.get("op")
    value = conditions.get("value")
    if not field:
        return False
    actual = getattr(lead, field, None) if hasattr(lead, field) else lead.extra_data.get(field)
    if op == "eq":
        return actual == value
    if op == "contains" and actual:
        return str(value).lower() in str(actual).lower()
    if op == "exists":
        return actual is not None and actual != ""
    return False


async def apply_score_rules(db: AsyncSession, tenant_id: uuid.UUID, lead_id: uuid.UUID) -> Lead:
    lead = (
        await db.execute(select(Lead).where(Lead.id == lead_id, Lead.tenant_id == tenant_id))
    ).scalar_one_or_none()
    if not lead:
        raise NotFoundException("Lead")
    rules = (
        await db.execute(
            select(CrmScoreRule)
            .where(CrmScoreRule.tenant_id == tenant_id, CrmScoreRule.is_active == True)  # noqa: E712
            .order_by(CrmScoreRule.priority)
        )
    ).scalars().all()
    total = 0
    for rule in rules:
        if _match_condition(lead, rule.conditions):
            total += rule.points
    lead.score = max(0, min(100, total))
    if lead.score >= 70:
        lead.score_label = "hot"
    elif lead.score >= 40:
        lead.score_label = "warm"
    else:
        lead.score_label = "cold"
    lead.scored_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(lead)
    return lead


# ── Bulk ────────────────────────────────────────────────────────────────────

async def bulk_update(db: AsyncSession, tenant_id: uuid.UUID, data: BulkUpdateRequest) -> int:
    updated = 0
    allowed = {"assigned_user_id", "stage_id", "pipeline_id", "status", "stage_order"}
    updates = {k: v for k, v in data.updates.items() if k in allowed}
    if not updates:
        raise ValidationException("No valid fields in updates")

    def _coerce(field: str, value):
        if field.endswith("_id") and value is not None and value != "":
            return value if isinstance(value, uuid.UUID) else uuid.UUID(str(value))
        return value

    if data.entity_type == "lead":
        for lid in data.ids:
            lead = (
                await db.execute(select(Lead).where(Lead.id == lid, Lead.tenant_id == tenant_id))
            ).scalar_one_or_none()
            if lead:
                for k, v in updates.items():
                    setattr(lead, k, _coerce(k, v))
                updated += 1
    elif data.entity_type == "deal":
        for did in data.ids:
            deal = (
                await db.execute(select(Deal).where(Deal.id == did, Deal.tenant_id == tenant_id))
            ).scalar_one_or_none()
            if deal:
                for k, v in updates.items():
                    if k == "stage_id" and v:
                        from app.modules.crm.pipeline_service import _get_stage_row

                        stage = await _get_stage_row(db, tenant_id, uuid.UUID(v))
                        deal.stage_id = stage.id
                        deal.stage = stage.name
                        deal.pipeline_id = stage.pipeline_id
                    elif k.endswith("_id") and v:
                        setattr(deal, k, uuid.UUID(v))
                    else:
                        setattr(deal, k, v)
                updated += 1
    elif data.entity_type == "customer":
        for cid in data.ids:
            cust = (
                await db.execute(select(Customer).where(Customer.id == cid, Customer.tenant_id == tenant_id))
            ).scalar_one_or_none()
            if cust:
                for k, v in updates.items():
                    if k in ("assigned_user_id",):
                        setattr(cust, k, uuid.UUID(v) if v else None)
                updated += 1
    else:
        raise ValidationException("Unsupported entity_type")
    await db.commit()
    return updated


# ── Duplicates & merge ──────────────────────────────────────────────────────

async def scan_duplicate_customers(db: AsyncSession, tenant_id: uuid.UUID) -> list[DuplicateCandidateResponse]:
    customers = (
        await db.execute(
            select(Customer).where(Customer.tenant_id == tenant_id, Customer.deleted_at.is_(None))
        )
    ).scalars().all()
    seen: list[DuplicateCandidateResponse] = []
    for i, a in enumerate(customers):
        for b in customers[i + 1 :]:
            score = 0.0
            if a.email and b.email and a.email.lower() == b.email.lower():
                score = 95.0
            elif a.phone and b.phone and a.phone == b.phone:
                score = 85.0
            if score >= 80:
                cand = CrmDuplicateCandidate(
                    id=uuid.uuid4(),
                    tenant_id=tenant_id,
                    entity_type="customer",
                    primary_id=a.id,
                    duplicate_id=b.id,
                    match_score=score,
                    status="pending",
                )
                db.add(cand)
                seen.append(DuplicateCandidateResponse.model_validate(cand))
    await db.commit()
    return seen


async def merge_entities(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    entity_type: str,
    primary_id: uuid.UUID,
    duplicate_id: uuid.UUID,
    user_id: uuid.UUID | None,
) -> uuid.UUID:
    if entity_type == "customer":
        primary = (
            await db.execute(select(Customer).where(Customer.id == primary_id, Customer.tenant_id == tenant_id))
        ).scalar_one_or_none()
        dup = (
            await db.execute(select(Customer).where(Customer.id == duplicate_id, Customer.tenant_id == tenant_id))
        ).scalar_one_or_none()
        if not primary or not dup:
            raise NotFoundException("Customer")
        await db.execute(
            update(Deal).where(Deal.customer_id == duplicate_id).values(customer_id=primary_id)
        )
        dup.deleted_at = datetime.now(timezone.utc)
        await log_action(
            db,
            action="customer.merged",
            resource="customer",
            resource_id=primary_id,
            tenant_id=tenant_id,
            user_id=user_id,
            metadata={"merged_id": str(duplicate_id)},
        )
        await db.commit()
        return primary_id
    if entity_type == "lead":
        raise ValidationException("Lead merge not yet supported — convert to customer first")
    raise ValidationException("Unsupported entity_type for merge")


# ── Dashboard ───────────────────────────────────────────────────────────────

async def get_dashboard(db: AsyncSession, tenant_id: uuid.UUID) -> DashboardResponse:
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    new_leads_today = (
        await db.execute(
            select(func.count()).select_from(Lead).where(
                Lead.tenant_id == tenant_id,
                Lead.deleted_at.is_(None),
                Lead.created_at >= today_start,
            )
        )
    ).scalar_one()

    month_start = today_start.replace(day=1)
    deals_won = (
        await db.execute(
            select(func.count()).select_from(Deal).where(
                Deal.tenant_id == tenant_id,
                Deal.deleted_at.is_(None),
                Deal.stage == "Completed",
                Deal.completed_at.isnot(None),
                Deal.completed_at >= month_start,
            )
        )
    ).scalar_one()

    total_value = (
        await db.execute(
            select(func.coalesce(func.sum(Deal.value_pence), 0)).where(
                Deal.tenant_id == tenant_id, Deal.deleted_at.is_(None), Deal.stage != "Lost"
            )
        )
    ).scalar_one()

    leads_by_source: dict[str, int] = {}
    for source, cnt in (
        await db.execute(
            select(Lead.source, func.count())
            .where(Lead.tenant_id == tenant_id, Lead.deleted_at.is_(None))
            .group_by(Lead.source)
        )
    ).all():
        leads_by_source[source or "unknown"] = cnt

    leads_by_stage: dict[str, int] = {}
    pipeline = await ensure_default_pipeline(db, tenant_id)
    stage_names = {s.id: s.name for s in pipeline.stages}
    for stage_id, cnt in (
        await db.execute(
            select(Lead.stage_id, func.count())
            .where(Lead.tenant_id == tenant_id, Lead.deleted_at.is_(None))
            .group_by(Lead.stage_id)
        )
    ).all():
        leads_by_stage[stage_names.get(stage_id, "Unassigned")] = cnt

    deals_by_stage: dict[str, int] = {}
    for stage, cnt in (
        await db.execute(
            select(Deal.stage, func.count())
            .where(Deal.tenant_id == tenant_id, Deal.deleted_at.is_(None))
            .group_by(Deal.stage)
        )
    ).all():
        deals_by_stage[stage or "unknown"] = cnt

    return DashboardResponse(
        new_leads_today=new_leads_today,
        deals_won_this_month=deals_won,
        total_pipeline_value_pence=int(total_value or 0),
        leads_by_source=leads_by_source,
        leads_by_stage=leads_by_stage,
        deals_by_stage=deals_by_stage,
    )


# ── Attachments ─────────────────────────────────────────────────────────────

async def create_attachment(
    db: AsyncSession, tenant_id: uuid.UUID, data: AttachmentCreate, user_id: uuid.UUID | None
) -> AttachmentResponse:
    row = CrmAttachment(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        uploaded_by_user_id=user_id,
        **data.model_dump(),
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return AttachmentResponse.model_validate(row)


async def list_attachments(
    db: AsyncSession, tenant_id: uuid.UUID, entity_type: str, entity_id: uuid.UUID
) -> list[AttachmentResponse]:
    rows = (
        await db.execute(
            select(CrmAttachment)
            .where(
                CrmAttachment.tenant_id == tenant_id,
                CrmAttachment.entity_type == entity_type,
                CrmAttachment.entity_id == entity_id,
            )
            .order_by(CrmAttachment.created_at.desc())
        )
    ).scalars().all()
    return [AttachmentResponse.model_validate(r) for r in rows]


# ── Assignments ─────────────────────────────────────────────────────────────

async def create_assignment(db: AsyncSession, tenant_id: uuid.UUID, data: AssignmentCreate) -> None:
    db.add(
        CrmAssignment(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            entity_type=data.entity_type,
            entity_id=data.entity_id,
            user_id=data.user_id,
            role=data.role,
        )
    )
    if data.entity_type == "lead":
        lead = (await db.execute(select(Lead).where(Lead.id == data.entity_id))).scalar_one_or_none()
        if lead:
            lead.assigned_user_id = data.user_id
    elif data.entity_type == "deal":
        deal = (await db.execute(select(Deal).where(Deal.id == data.entity_id))).scalar_one_or_none()
        if deal:
            deal.assigned_user_id = data.user_id
    elif data.entity_type == "customer":
        cust = (await db.execute(select(Customer).where(Customer.id == data.entity_id))).scalar_one_or_none()
        if cust:
            cust.assigned_user_id = data.user_id
    await db.commit()


# ── Customer profile (bookings read-only) ───────────────────────────────────

async def list_customer_bookings(db: AsyncSession, tenant_id: uuid.UUID, customer_id: uuid.UUID, limit: int = 20):
    rows = (
        await db.execute(
            select(Booking)
            .where(Booking.tenant_id == tenant_id, Booking.customer_id == customer_id)
            .order_by(Booking.booking_date.desc())
            .limit(limit)
        )
    ).scalars().all()
    return [
        {
            "id": str(b.id),
            "booking_date": b.booking_date.isoformat() if b.booking_date else None,
            "status": b.status,
            "service_type": b.service_type,
            "value_pence": getattr(b, "total_pence", None) or getattr(b, "prepaid_pence", 0),
        }
        for b in rows
    ]


# ── CSV export / import ─────────────────────────────────────────────────────

async def export_leads_csv(db: AsyncSession, tenant_id: uuid.UUID) -> str:
    leads = (
        await db.execute(
            select(Lead).where(Lead.tenant_id == tenant_id, Lead.deleted_at.is_(None)).order_by(Lead.created_at.desc())
        )
    ).scalars().all()
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["first_name", "last_name", "email", "phone", "source", "status", "score"])
    for lead in leads:
        w.writerow([lead.first_name, lead.last_name or "", lead.email or "", lead.phone or "", lead.source, lead.status, lead.score or ""])
    return buf.getvalue()


async def import_leads_csv(
    db: AsyncSession, tenant_id: uuid.UUID, csv_text: str, user_id: uuid.UUID | None
) -> CrmImportJob:
    pipeline = await ensure_default_pipeline(db, tenant_id)
    first_stage = sorted(pipeline.stages, key=lambda s: s.position)[0]
    job = CrmImportJob(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        user_id=user_id,
        job_type="import",
        entity_type="lead",
        status="running",
    )
    db.add(job)
    reader = csv.DictReader(io.StringIO(csv_text))
    count = 0
    for row in reader:
        db.add(
            Lead(
                id=uuid.uuid4(),
                tenant_id=tenant_id,
                first_name=row.get("first_name") or "Unknown",
                last_name=row.get("last_name") or None,
                email=row.get("email") or None,
                phone=row.get("phone") or None,
                source=row.get("source") or "csv_import",
                pipeline_id=pipeline.id,
                stage_id=first_stage.id,
            )
        )
        count += 1
    job.status = "done"
    job.row_count = count
    job.completed_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(job)
    return job


async def enrich_lead_ai(db: AsyncSession, tenant_id: uuid.UUID, lead_id: uuid.UUID) -> dict:
    """Summarize lead using existing AI router."""
    lead = (
        await db.execute(select(Lead).where(Lead.id == lead_id, Lead.tenant_id == tenant_id))
    ).scalar_one_or_none()
    if not lead:
        raise NotFoundException("Lead")
    from app.services.ai.router import get_ai_router
    from app.services.ai.types import AIMessage

    router = get_ai_router()
    prompt = (
        f"Summarize this UK service business lead in 2-3 sentences for a CRM rep.\n"
        f"Name: {lead.first_name} {lead.last_name or ''}\n"
        f"Email: {lead.email}\nPhone: {lead.phone}\n"
        f"Message: {lead.message}\nService: {lead.service_needed}\nSource: {lead.source}"
    )
    result = await router.chat(
        [AIMessage(role="user", content=prompt)],
        tenant_id=tenant_id,
        purpose="crm_lead_enrich",
        temperature=0.4,
    )
    summary = result.content or ""
    lead.extra_data = {**(lead.extra_data or {}), "ai_summary": summary}
    db.add(
        CrmActivity(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            entity_type="lead",
            entity_id=lead.id,
            activity_type="ai_enrichment",
            body=summary,
            extra_metadata={},
        )
    )
    await db.commit()
    return {"summary": summary}
