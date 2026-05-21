"""Public booking widget and self-service."""
from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.booking.enterprise.settings import get_or_create_settings
from app.modules.booking.enterprise.services_catalog import list_services
from app.modules.booking.enterprise_schemas import PublicWidgetConfigResponse
from app.modules.booking.models import Booking
from app.modules.tenants.models import Tenant


async def get_widget_config(db: AsyncSession, tenant: Tenant) -> PublicWidgetConfigResponse:
    settings = await get_or_create_settings(db, tenant.id)
    services = await list_services(db, tenant.id, active_only=True)
    from app.modules.booking.enterprise_schemas import BookingServiceResponse

    return PublicWidgetConfigResponse(
        tenant_slug=tenant.slug,
        tenant_name=tenant.name,
        timezone=settings.timezone,
        services=[BookingServiceResponse.model_validate(s) for s in services],
        widget_primary_color=settings.widget_primary_color,
        google_pixel_id=settings.google_pixel_id,
        meta_pixel_id=settings.meta_pixel_id,
        intake_questions=settings.intake_questions or [],
        deposit_enabled=settings.deposit_enabled,
        default_deposit_pence=settings.default_deposit_pence,
    )


async def get_public_ical(db: AsyncSession, tenant_slug: str) -> str:
    from app.modules.booking.enterprise.calendar_sync import build_ical_feed

    tenant = (
        await db.execute(select(Tenant).where(Tenant.slug == tenant_slug, Tenant.is_active == True))  # noqa: E712
    ).scalar_one_or_none()
    if not tenant:
        return build_ical_feed([], "Bookings")

    bookings = (
        await db.execute(
            select(Booking).where(
                Booking.tenant_id == tenant.id,
                Booking.status.in_(("confirmed", "pending")),
            )
        )
    ).scalars().all()
    return build_ical_feed(list(bookings), tenant.name)
