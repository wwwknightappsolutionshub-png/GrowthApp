"""Business site bootstrap, publish, and QR for tenant subdomains."""
from __future__ import annotations

import base64
import logging
import uuid
from datetime import datetime, timezone
from io import BytesIO

import segno
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import BadRequestException, NotFoundException
from app.modules.admin.tool_config import classifyBusiness_py
from app.modules.landing_pages.models import LandingPage
from app.modules.tenants.models import Tenant

logger = logging.getLogger(__name__)

# Map tool_config category → marketing template niche + default template slug
CATEGORY_SITE_TEMPLATE: dict[str, tuple[str, str]] = {
    "tradesman": ("trades", "trades-emergency-callout"),
    "salon_beauty": ("beauty", "beauty-salon-bookings"),
    "healthcare": ("healthcare", "healthcare-private-clinic"),
    "restaurant_food": ("hospitality", "hospitality-restaurant-reservations"),
    "retail": ("generic", "generic-saas-launch"),
    "fitness_wellness": ("beauty", "beauty-spa-membership"),
    "professional_services": ("generic", "generic-saas-launch"),
    "general": ("generic", "generic-saas-launch"),
}


def business_site_public_url(tenant_slug: str) -> str:
    domain = (settings.BUSINESS_SITE_BASE_DOMAIN or "customerflowai.online").strip().lstrip(".")
    return f"https://{tenant_slug}.{domain}"


def qr_png_bytes(url: str) -> bytes:
    buf = BytesIO()
    segno.make(url).save(buf, kind="png", scale=6, border=2)
    return buf.getvalue()


def _qr_png_base64(url: str) -> str:
    return base64.b64encode(qr_png_bytes(url)).decode("ascii")


async def get_site_status(db: AsyncSession, tenant: Tenant) -> dict:
    from app.modules.membership_rewards.landing import memberships_public_url

    page = await _get_primary_page(db, tenant)
    public_url = business_site_public_url(tenant.slug)
    qr_b64 = _qr_png_base64(public_url) if tenant.business_site_published else None
    memberships_url = None
    try:
        from app.modules.membership_rewards.models import MrTenantSettings

        mr_settings = await db.get(MrTenantSettings, tenant.id)
        if mr_settings and mr_settings.landing_published:
            memberships_url = memberships_public_url(tenant.slug)
    except Exception:  # noqa: BLE001
        pass
    return {
        "tenant_slug": tenant.slug,
        "public_url": public_url,
        "memberships_url": memberships_url,
        "is_published": tenant.business_site_published,
        "published_at": tenant.business_site_published_at.isoformat()
        if tenant.business_site_published_at
        else None,
        "primary_page_id": str(tenant.primary_landing_page_id) if tenant.primary_landing_page_id else None,
        "primary_page_slug": page.slug if page else None,
        "primary_page_title": page.title if page else None,
        "page_is_published": page.is_published if page else False,
        "qr_png_base64": qr_b64,
        "edit_url": f"/dashboard/landing-pages/{page.id}" if page else None,
    }


async def bootstrap_business_site(
    db: AsyncSession,
    tenant: Tenant,
    user_id: uuid.UUID,
    *,
    template_slug: str | None = None,
) -> LandingPage:
    """Create enterprise landing page from category template (slug ``home``)."""
    from app.modules.marketing.service import apply_template_to_tenant, list_templates

    if tenant.primary_landing_page_id:
        existing = await _get_primary_page(db, tenant)
        if existing:
            return existing

    category = classifyBusiness_py(tenant.business_type)
    niche, default_slug = CATEGORY_SITE_TEMPLATE.get(category, CATEGORY_SITE_TEMPLATE["general"])
    slug = template_slug or default_slug

    templates = await list_templates(db, niche=niche)
    if not any(t.slug == slug for t in templates):
        fallback = templates[0].slug if templates else default_slug
        slug = fallback

    page = await apply_template_to_tenant(
        db,
        tenant_id=tenant.id,
        user_id=user_id,
        template_slug=slug,
        page_title=f"{tenant.name} — Get in touch",
        page_slug="home",
    )

    theme = dict(page.theme or {})
    theme["primary_color"] = tenant.primary_color or theme.get("primary_color") or "#166534"
    theme["business_name"] = tenant.name
    page.theme = theme
    page.meta_description = (
        page.meta_description
        or f"Contact {tenant.name} for professional {tenant.business_type} services in {tenant.city or 'your area'}."
    )[:400]

    tenant.primary_landing_page_id = page.id
    db.add(page)
    db.add(tenant)
    await db.commit()
    await db.refresh(page)
    return page


async def publish_business_site(
    db: AsyncSession,
    tenant: Tenant,
    *,
    owner_email: str | None = None,
) -> dict:
    page = await _get_primary_page(db, tenant)
    if not page:
        raise BadRequestException("Create your business page first")

    page.is_published = True
    page.published_at = datetime.now(timezone.utc)
    page.slug = "home"
    db.add(page)

    tenant.business_site_published = True
    tenant.business_site_published_at = datetime.now(timezone.utc)
    tenant.primary_landing_page_id = page.id
    db.add(tenant)
    await db.commit()

    public_url = business_site_public_url(tenant.slug)
    qr_b64 = _qr_png_base64(public_url)

    email = owner_email or tenant.email
    if email:
        await _email_site_published(email, tenant.name, public_url, qr_b64)

    await db.refresh(tenant)
    return await get_site_status(db, tenant)


async def get_public_site_payload(db: AsyncSession, tenant_slug: str) -> dict:
    tenant = (
        await db.execute(
            select(Tenant).where(Tenant.slug == tenant_slug, Tenant.is_active.is_(True))
        )
    ).scalar_one_or_none()
    if not tenant or not tenant.business_site_published:
        raise NotFoundException("Site")

    page = await _get_primary_page(db, tenant)
    if not page or not page.is_published:
        raise NotFoundException("Site")

    return {
        "tenant_slug": tenant.slug,
        "business_name": tenant.name,
        "business_type": tenant.business_type,
        "phone": tenant.phone,
        "email": tenant.email,
        "city": tenant.city,
        "postcode": tenant.postcode,
        "primary_color": tenant.primary_color,
        "title": page.title,
        "meta_description": page.meta_description,
        "theme": page.theme or {},
        "sections": page.sections or [],
    }


async def _get_primary_page(db: AsyncSession, tenant: Tenant) -> LandingPage | None:
    if not tenant.primary_landing_page_id:
        return None
    return (
        await db.execute(
            select(LandingPage).where(
                LandingPage.id == tenant.primary_landing_page_id,
                LandingPage.tenant_id == tenant.id,
            )
        )
    ).scalar_one_or_none()


async def _email_site_published(
    email: str,
    business_name: str,
    public_url: str,
    qr_png_base64: str,
) -> None:
    from app.templates.renderer import render_business_site_published
    from app.workers.queue import enqueue

    html = render_business_site_published(
        business_name=business_name,
        public_url=public_url,
        qr_data_url=f"data:image/png;base64,{qr_png_base64}",
    )
    try:
        await enqueue(
            "send_email_task",
            to=email,
            subject=f"Your business page is live — {business_name}",
            html=html,
            tenant_id=None,
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("business site publish email enqueue failed: %s", exc)
