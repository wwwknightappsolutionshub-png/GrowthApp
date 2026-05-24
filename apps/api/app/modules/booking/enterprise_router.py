"""Enterprise booking endpoints — extends /bookings without breaking existing routes."""
from __future__ import annotations

from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import CurrentTenantContext
from app.modules.booking import service as booking_service
from app.modules.booking.enterprise import (
    analytics,
    automation,
    calendar_sync,
    marketing,
    payments,
    services_catalog,
    settings as settings_svc,
    slots,
    staff_ops,
)
from app.modules.booking.enterprise_schemas import (
    AbandonedSessionCreate,
    BookingAnalyticsResponse,
    BookingPackageCreate,
    BookingPaymentIntentRequest,
    BookingPaymentIntentResponse,
    BookingPromoCreate,
    BookingRefundRequest,
    BookingResourceCreate,
    BookingResourceResponse,
    BookingServiceCreate,
    BookingServiceResponse,
    BookingServiceUpdate,
    BookingFormSchemaResponse,
    BookingFormTemplateUpdate,
    BookingSettingsResponse,
    BookingSettingsUpdate,
    ClientReminderRequest,
    FeedbackRequestBody,
    CalendarConnectionCreate,
    CalendarSyncResponse,
    SlotGenerateRequest,
    StaffBlackoutCreate,
    StaffCreate,
    StaffResponse,
    StaffShiftCreate,
    StaffUpdate,
    AvailabilitySlotResponse,
)
from app.modules.booking.models import Booking
from app.modules.booking.schemas import BookingResponse, BookingTimelineResponse

router = APIRouter(tags=["Bookings Enterprise"])


# ── Settings ──────────────────────────────────────────────────────────────────

@router.get("/settings", response_model=BookingSettingsResponse)
async def get_booking_settings(ctx: CurrentTenantContext, db: AsyncSession = Depends(get_db)):
    _, tenant, _ = ctx
    return await settings_svc.get_or_create_settings(db, tenant.id)


@router.patch("/settings", response_model=BookingSettingsResponse)
async def patch_booking_settings(
    body: BookingSettingsUpdate,
    ctx: CurrentTenantContext,
    db: AsyncSession = Depends(get_db),
):
    user, tenant, _ = ctx
    return await settings_svc.update_settings(db, tenant.id, body, user_id=user.id)


@router.post("/{booking_id}/remind")
async def send_booking_client_reminder(
    booking_id: UUID,
    body: ClientReminderRequest,
    ctx: CurrentTenantContext,
    db: AsyncSession = Depends(get_db),
):
    _, tenant, _ = ctx
    return await automation.send_immediate_client_reminder(
        db, tenant.id, booking_id, channel=body.channel
    )


@router.get("/link")
async def get_booking_link(ctx: CurrentTenantContext):
    _, tenant, _ = ctx
    return {"url": marketing.booking_link_for_tenant(tenant.slug), "slug": tenant.slug}


def _booking_links_payload(tenant, *, memberships_url: str | None = None) -> dict:
    from app.modules.booking.feedback import refer_url_for_slug

    base_book = marketing.booking_link_for_tenant(tenant.slug)
    payload = {
        "slug": tenant.slug,
        "booking_url": base_book,
        "referral_url": refer_url_for_slug(tenant.slug),
        "rate_url": f"{base_book.rstrip('/')}/rate",
        "review_label": "Review & Comments (Google)",
        "refer_label": "Refer & Win",
        "booking_label": "Book appointment",
        "slug_archived": "-deleted-" in (tenant.slug or ""),
    }
    if memberships_url:
        payload["memberships_url"] = memberships_url
        payload["memberships_label"] = "Membership & Rewards"
    return payload


async def _memberships_url_for_tenant(db: AsyncSession, tenant_id) -> str | None:
    from app.modules.membership_rewards.landing import memberships_public_url
    from app.modules.membership_rewards.models import MrTenantSettings
    from app.modules.tenants.models import Tenant

    settings = await db.get(MrTenantSettings, tenant_id)
    if not settings or not settings.landing_published:
        return None
    tenant = await db.get(Tenant, tenant_id)
    if not tenant:
        return None
    return memberships_public_url(tenant.slug)


@router.get("/links")
async def get_booking_qr_links(ctx: CurrentTenantContext, db: AsyncSession = Depends(get_db)):
    """Distinct public URLs for booking, referral, rate-us, and memberships QR codes."""
    _, tenant, _ = ctx
    memberships_url = await _memberships_url_for_tenant(db, tenant.id)
    return _booking_links_payload(tenant, memberships_url=memberships_url)


@router.post("/links/restore-slug")
async def restore_tenant_booking_slug(ctx: CurrentTenantContext, db: AsyncSession = Depends(get_db)):
    """Restore clean slug and re-enable public booking (sets ``is_active``)."""
    from app.core.exceptions import BadRequestException
    from app.modules.admin.deletion import ARCHIVED_SLUG_MARKER, restore_archived_tenant_slug

    _, tenant, _ = ctx
    slug_archived = ARCHIVED_SLUG_MARKER in tenant.slug
    if not slug_archived and tenant.is_active:
        raise BadRequestException("Booking URL slug is already active (no archived suffix).")

    tenant.is_active = True
    if slug_archived:
        await restore_archived_tenant_slug(db, tenant)
    else:
        db.add(tenant)
        await db.commit()
    await db.refresh(tenant)
    memberships_url = await _memberships_url_for_tenant(db, tenant.id)
    return _booking_links_payload(tenant, memberships_url=memberships_url)


@router.get("/form")
async def get_tenant_booking_form(ctx: CurrentTenantContext, db: AsyncSession = Depends(get_db)):
    from app.modules.admin.tool_config import classifyBusiness_py
    from app.modules.booking.form_builder import resolve_tenant_booking_form

    _, tenant, _ = ctx
    settings = await settings_svc.get_or_create_settings(db, tenant.id)
    category = classifyBusiness_py(tenant.business_type or "general")
    override = getattr(settings, "booking_form_override", None) or {}
    resolved = await resolve_tenant_booking_form(db, tenant)
    return {
        "category": category,
        "schema": resolved,
        "is_tenant_override": bool(override.get("fields")),
    }


@router.put("/form")
async def update_tenant_booking_form(
    request: Request,
    ctx: CurrentTenantContext,
    db: AsyncSession = Depends(get_db),
):
    from app.core.exceptions import BadRequestException
    from app.modules.admin.tool_config import classifyBusiness_py
    from app.modules.booking.form_builder import extract_schema_payload, update_tenant_form_override

    user, tenant, _ = ctx
    raw = await request.json()
    if not isinstance(raw, dict):
        raise BadRequestException("Invalid JSON body")
    try:
        schema_in = extract_schema_payload(raw)
    except ValueError as exc:
        raise BadRequestException(str(exc)) from exc
    try:
        schema = await update_tenant_form_override(
            db, tenant.id, schema_in, user_id=user.id
        )
    except ValueError as exc:
        raise BadRequestException(str(exc)) from exc
    settings = await settings_svc.get_or_create_settings(db, tenant.id)
    override = getattr(settings, "booking_form_override", None) or {}
    return {
        "category": classifyBusiness_py(tenant.business_type or "general"),
        "schema": schema,
        "is_tenant_override": bool(override.get("fields")),
    }


@router.post("/{booking_id}/request-feedback")
async def request_booking_feedback(
    booking_id: UUID,
    body: FeedbackRequestBody,
    ctx: CurrentTenantContext,
    db: AsyncSession = Depends(get_db),
):
    from app.modules.booking.feedback import request_service_feedback

    user, tenant, _ = ctx
    return await request_service_feedback(
        db, tenant.id, booking_id, channels=body.channels, actor_user_id=user.id
    )


# ── Services & resources ──────────────────────────────────────────────────────

@router.get("/services", response_model=list[BookingServiceResponse])
async def list_booking_services(ctx: CurrentTenantContext, db: AsyncSession = Depends(get_db)):
    _, tenant, _ = ctx
    return await services_catalog.list_services(db, tenant.id, active_only=False)


@router.post("/services", response_model=BookingServiceResponse, status_code=201)
async def create_booking_service(
    body: BookingServiceCreate, ctx: CurrentTenantContext, db: AsyncSession = Depends(get_db)
):
    _, tenant, _ = ctx
    return await services_catalog.create_service(db, tenant.id, body)


@router.patch("/services/{service_id}", response_model=BookingServiceResponse)
async def update_booking_service(
    service_id: UUID,
    body: BookingServiceUpdate,
    ctx: CurrentTenantContext,
    db: AsyncSession = Depends(get_db),
):
    _, tenant, _ = ctx
    return await services_catalog.update_service(db, tenant.id, service_id, body)


@router.get("/resources", response_model=list[BookingResourceResponse])
async def list_booking_resources(ctx: CurrentTenantContext, db: AsyncSession = Depends(get_db)):
    _, tenant, _ = ctx
    return await services_catalog.list_resources(db, tenant.id)


@router.post("/resources", response_model=BookingResourceResponse, status_code=201)
async def create_booking_resource(
    body: BookingResourceCreate, ctx: CurrentTenantContext, db: AsyncSession = Depends(get_db)
):
    _, tenant, _ = ctx
    return await services_catalog.create_resource(db, tenant.id, body)


# ── Staff ─────────────────────────────────────────────────────────────────────

@router.get("/staff", response_model=list[StaffResponse])
async def list_booking_staff(ctx: CurrentTenantContext, db: AsyncSession = Depends(get_db)):
    _, tenant, _ = ctx
    return await staff_ops.list_staff(db, tenant.id)


@router.post("/staff", response_model=StaffResponse, status_code=201)
async def create_booking_staff(
    body: StaffCreate, ctx: CurrentTenantContext, db: AsyncSession = Depends(get_db)
):
    user, tenant, _ = ctx
    return await staff_ops.create_staff(db, tenant.id, body, user_id=user.id)


@router.patch("/staff/{staff_id}", response_model=StaffResponse)
async def update_booking_staff(
    staff_id: UUID, body: StaffUpdate, ctx: CurrentTenantContext, db: AsyncSession = Depends(get_db)
):
    _, tenant, _ = ctx
    return await staff_ops.update_staff(db, tenant.id, staff_id, body)


@router.delete("/staff/{staff_id}", status_code=204)
async def delete_booking_staff(
    staff_id: UUID, ctx: CurrentTenantContext, db: AsyncSession = Depends(get_db)
):
    user, tenant, _ = ctx
    await staff_ops.delete_staff(db, tenant.id, staff_id, user_id=user.id)


@router.post("/staff/shifts", status_code=201)
async def create_staff_shift(
    body: StaffShiftCreate, ctx: CurrentTenantContext, db: AsyncSession = Depends(get_db)
):
    _, tenant, _ = ctx
    return await staff_ops.create_shift(db, tenant.id, body)


@router.get("/staff/shifts")
async def list_staff_shifts(
    ctx: CurrentTenantContext,
    db: AsyncSession = Depends(get_db),
    staff_id: UUID | None = None,
):
    _, tenant, _ = ctx
    return await staff_ops.list_shifts(db, tenant.id, staff_id)


@router.post("/staff/blackouts", status_code=201)
async def create_staff_blackout(
    body: StaffBlackoutCreate, ctx: CurrentTenantContext, db: AsyncSession = Depends(get_db)
):
    _, tenant, _ = ctx
    return await staff_ops.create_blackout(db, tenant.id, body)


@router.get("/staff/blackouts")
async def list_staff_blackouts(ctx: CurrentTenantContext, db: AsyncSession = Depends(get_db)):
    _, tenant, _ = ctx
    return await staff_ops.list_blackouts(db, tenant.id)


# ── Slots ─────────────────────────────────────────────────────────────────────

@router.get("/slots", response_model=list[AvailabilitySlotResponse])
async def list_availability_slots(
    ctx: CurrentTenantContext,
    db: AsyncSession = Depends(get_db),
    from_date: date | None = None,
    staff_id: UUID | None = None,
    only_available: bool = False,
):
    _, tenant, _ = ctx
    return await slots.list_slots(
        db, tenant.id, from_date=from_date, staff_id=staff_id, only_available=only_available
    )


@router.post("/slots/generate")
async def generate_availability_slots(
    body: SlotGenerateRequest, ctx: CurrentTenantContext, db: AsyncSession = Depends(get_db)
):
    _, tenant, _ = ctx
    created = await slots.generate_slots(db, tenant.id, body)
    return {"created": created}


# ── Payments ──────────────────────────────────────────────────────────────────

@router.post("/payments/intent", response_model=BookingPaymentIntentResponse)
async def create_payment_intent(
    body: BookingPaymentIntentRequest, ctx: CurrentTenantContext, db: AsyncSession = Depends(get_db)
):
    _, tenant, _ = ctx
    result = await payments.create_booking_payment_intent(db, tenant.id, body)
    return BookingPaymentIntentResponse(**result)


@router.post("/{booking_id}/refund", response_model=BookingResponse)
async def refund_booking(
    booking_id: UUID,
    body: BookingRefundRequest,
    ctx: CurrentTenantContext,
    db: AsyncSession = Depends(get_db),
):
    _, tenant, _ = ctx
    return await payments.refund_booking(db, tenant.id, booking_id, body)


# ── Packages & promos ─────────────────────────────────────────────────────────

@router.get("/packages")
async def list_packages(ctx: CurrentTenantContext, db: AsyncSession = Depends(get_db)):
    _, tenant, _ = ctx
    return await marketing.list_packages(db, tenant.id)


@router.post("/packages", status_code=201)
async def create_package(
    body: BookingPackageCreate, ctx: CurrentTenantContext, db: AsyncSession = Depends(get_db)
):
    _, tenant, _ = ctx
    return await marketing.create_package(db, tenant.id, body)


@router.post("/promo-codes", status_code=201)
async def create_promo(body: BookingPromoCreate, ctx: CurrentTenantContext, db: AsyncSession = Depends(get_db)):
    _, tenant, _ = ctx
    return await marketing.create_promo(db, tenant.id, body)


@router.post("/abandoned-sessions", status_code=201)
async def record_abandoned(
    body: AbandonedSessionCreate, ctx: CurrentTenantContext, db: AsyncSession = Depends(get_db)
):
    _, tenant, _ = ctx
    return await marketing.record_abandoned(db, tenant.id, body)


# ── Analytics & AI ────────────────────────────────────────────────────────────

@router.get("/analytics", response_model=BookingAnalyticsResponse)
async def booking_analytics(
    ctx: CurrentTenantContext,
    db: AsyncSession = Depends(get_db),
    days: int = Query(30, ge=7, le=365),
):
    _, tenant, _ = ctx
    return await analytics.get_booking_analytics(db, tenant.id, days=days)


@router.get("/{booking_id}/recommendations")
async def booking_recommendations(
    booking_id: UUID, ctx: CurrentTenantContext, db: AsyncSession = Depends(get_db)
):
    _, tenant, _ = ctx
    return await automation.ai_booking_recommendations(db, tenant.id, booking_id)


@router.get("/{booking_id}/timeline", response_model=BookingTimelineResponse)
async def booking_timeline(
    booking_id: UUID, ctx: CurrentTenantContext, db: AsyncSession = Depends(get_db)
):
    _, tenant, _ = ctx
    return await booking_service.get_booking_timeline(db, tenant.id, booking_id)


# ── Calendar ──────────────────────────────────────────────────────────────────

@router.post("/calendar/connections", status_code=201)
async def create_calendar_connection(
    body: CalendarConnectionCreate, ctx: CurrentTenantContext, db: AsyncSession = Depends(get_db)
):
    _, tenant, _ = ctx
    return await calendar_sync.create_connection(db, tenant.id, body)


@router.get("/calendar/connections")
async def list_calendar_connections(ctx: CurrentTenantContext, db: AsyncSession = Depends(get_db)):
    _, tenant, _ = ctx
    return await calendar_sync.list_connections(db, tenant.id)


@router.post("/calendar/connections/{connection_id}/sync", response_model=CalendarSyncResponse)
async def sync_calendar_connection(
    connection_id: UUID, ctx: CurrentTenantContext, db: AsyncSession = Depends(get_db)
):
    _, tenant, _ = ctx
    return await calendar_sync.sync_calendar(db, tenant.id, connection_id)


@router.get("/export/ical")
async def export_tenant_ical(ctx: CurrentTenantContext, db: AsyncSession = Depends(get_db)):
    from fastapi.responses import PlainTextResponse
    from sqlalchemy import select

    _, tenant, _ = ctx
    bookings = (
        await db.execute(
            select(Booking).where(
                Booking.tenant_id == tenant.id,
                Booking.status.in_(("confirmed", "pending")),
            )
        )
    ).scalars().all()
    content = calendar_sync.build_ical_feed(list(bookings), tenant.name)
    return PlainTextResponse(content, media_type="text/calendar")
