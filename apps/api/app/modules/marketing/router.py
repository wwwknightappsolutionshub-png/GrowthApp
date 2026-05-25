"""HTTP routes for the marketing CMS, public review pipeline and landing
templates.

Three distinct surfaces live here:

- `/admin/marketing/...`         super-admin CRUD over sections, reviews,
  template catalogue.
- `/marketing/landing-templates` authenticated tenant access to apply a
  template to their own workspace.
- `/public/marketing/...`        unauthenticated reads for the marketing site
  + visitor review submission.
"""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import CurrentTenantContext, CurrentUser, SuperAdmin
from app.core.middleware import limiter
from app.modules.marketing import service
from app.modules.marketing.schemas import (
    AdaptiveLandingPageResponse,
    AdaptiveLandingPageUpdate,
    AdaptiveLandingPageUpsert,
    AdminReviewResponse,
    ApplyTemplateRequest,
    LandingPageTemplateDetail,
    LandingPageTemplateSummary,
    MarketingSectionCreate,
    MarketingSectionResponse,
    MarketingSectionReorderRequest,
    MarketingSectionUpdate,
    PublicMarketingBundle,
    PublicReviewResponse,
    PublicReviewSubmit,
    ReviewModerationAction,
    ReviewPushRequest,
)

# ──────────────────────────────────────────────────────────────────────────────
# Admin router (super-admin only) — /admin/marketing/*
# ──────────────────────────────────────────────────────────────────────────────

admin_router = APIRouter(prefix="/admin/marketing", tags=["Admin · Marketing"])


@admin_router.get("/sections", response_model=list[MarketingSectionResponse])
async def admin_list_sections(_: SuperAdmin, db: AsyncSession = Depends(get_db)):
    sections = await service.list_sections(db, only_published=False)
    if not sections:
        await service.ensure_marketing_seeded(db)
        sections = await service.list_sections(db, only_published=False)
    return sections


@admin_router.post("/seed", status_code=status.HTTP_200_OK)
async def admin_seed_marketing(_: SuperAdmin, db: AsyncSession = Depends(get_db)):
    """Idempotently seed default marketing CMS content (sections, reviews, templates)."""
    counts = await service.ensure_marketing_seeded(db, force=True)
    return {"ok": True, "created": counts}


@admin_router.get("/sections/{key}", response_model=MarketingSectionResponse)
async def admin_get_section(key: str, _: SuperAdmin, db: AsyncSession = Depends(get_db)):
    return await service.get_section(db, key)


@admin_router.post(
    "/sections", response_model=MarketingSectionResponse, status_code=status.HTTP_201_CREATED
)
async def admin_create_section(
    body: MarketingSectionCreate,
    admin: SuperAdmin,
    db: AsyncSession = Depends(get_db),
):
    return await service.upsert_section(
        db,
        key=body.key,
        title=body.title,
        description=body.description,
        data=body.data,
        is_published=body.is_published if body.is_published is not None else True,
        sort_order=body.sort_order or 0,
        user_id=admin.id,
    )


@admin_router.post("/sections/reorder", response_model=list[MarketingSectionResponse])
async def admin_reorder_sections(
    body: MarketingSectionReorderRequest,
    admin: SuperAdmin,
    db: AsyncSession = Depends(get_db),
):
    await service.reorder_sections(db, body.keys, user_id=admin.id)
    return await service.list_sections(db, only_published=False)


@admin_router.patch("/sections/{key}", response_model=MarketingSectionResponse)
async def admin_patch_section(
    key: str,
    body: MarketingSectionUpdate,
    admin: SuperAdmin,
    db: AsyncSession = Depends(get_db),
):
    return await service.patch_section(
        db,
        key,
        title=body.title,
        description=body.description,
        data=body.data,
        is_published=body.is_published,
        sort_order=body.sort_order,
        user_id=admin.id,
    )


@admin_router.delete("/sections/{key}", status_code=status.HTTP_204_NO_CONTENT)
async def admin_delete_section(key: str, _: SuperAdmin, db: AsyncSession = Depends(get_db)):
    await service.delete_section(db, key)
    return None


# Adaptive landing pages ----------------------------------------------------


@admin_router.get("/adaptive-pages", response_model=list[AdaptiveLandingPageResponse])
async def admin_list_adaptive_pages(_: SuperAdmin, db: AsyncSession = Depends(get_db)):
    return await service.list_adaptive_pages(db, only_published=False)


@admin_router.get("/adaptive-pages/{niche_id}", response_model=AdaptiveLandingPageResponse)
async def admin_get_adaptive_page(
    niche_id: str, _: SuperAdmin, db: AsyncSession = Depends(get_db)
):
    return await service.get_adaptive_page(db, niche_id)


@admin_router.post(
    "/adaptive-pages",
    response_model=AdaptiveLandingPageResponse,
    status_code=status.HTTP_201_CREATED,
)
async def admin_upsert_adaptive_page(
    body: AdaptiveLandingPageUpsert,
    admin: SuperAdmin,
    db: AsyncSession = Depends(get_db),
):
    return await service.upsert_adaptive_page(
        db,
        niche_id=body.niche_id,
        label=body.label,
        data=body.data,
        is_published=body.is_published,
        user_id=admin.id,
    )


@admin_router.patch("/adaptive-pages/{niche_id}", response_model=AdaptiveLandingPageResponse)
async def admin_patch_adaptive_page(
    niche_id: str,
    body: AdaptiveLandingPageUpdate,
    admin: SuperAdmin,
    db: AsyncSession = Depends(get_db),
):
    return await service.patch_adaptive_page(
        db,
        niche_id,
        label=body.label,
        data=body.data,
        is_published=body.is_published,
        user_id=admin.id,
    )


@admin_router.delete("/adaptive-pages/{niche_id}", status_code=status.HTTP_204_NO_CONTENT)
async def admin_delete_adaptive_page(
    niche_id: str, _: SuperAdmin, db: AsyncSession = Depends(get_db)
):
    await service.delete_adaptive_page(db, niche_id)
    return None


# Reviews moderation -------------------------------------------------------


@admin_router.get("/reviews", response_model=list[AdminReviewResponse])
async def admin_list_reviews(
    _: SuperAdmin,
    db: AsyncSession = Depends(get_db),
    status_filter: str | None = None,
):
    return await service.list_all_reviews_for_admin(db, status=status_filter)


@admin_router.patch("/reviews/{review_id}", response_model=AdminReviewResponse)
async def admin_moderate_review(
    review_id: uuid.UUID,
    body: ReviewModerationAction,
    _: SuperAdmin,
    db: AsyncSession = Depends(get_db),
):
    return await service.moderate_review(
        db,
        review_id,
        status=body.status,
        is_featured=body.is_featured,
        is_carousel=body.is_carousel,
        quote=body.quote,
        author_role=body.author_role,
        author_location=body.author_location,
        metric=body.metric,
    )


@admin_router.post("/reviews/{review_id}/push", response_model=AdminReviewResponse)
async def admin_push_review(
    review_id: uuid.UUID,
    body: ReviewPushRequest,
    _: SuperAdmin,
    db: AsyncSession = Depends(get_db),
):
    return await service.push_review_external(
        db, review_id, channel=body.channel, target_url=body.target_url
    )


# Landing-page templates ---------------------------------------------------


@admin_router.get("/landing-templates", response_model=list[LandingPageTemplateSummary])
async def admin_list_landing_templates(
    _: SuperAdmin, db: AsyncSession = Depends(get_db), niche: str | None = None
):
    return await service.list_templates(db, niche=niche)


@admin_router.get("/landing-templates/{slug}", response_model=LandingPageTemplateDetail)
async def admin_get_landing_template(
    slug: str, _: SuperAdmin, db: AsyncSession = Depends(get_db)
):
    return await service.get_template_by_slug(db, slug)


# ──────────────────────────────────────────────────────────────────────────────
# Authenticated tenant router — /marketing/*
# ──────────────────────────────────────────────────────────────────────────────

tenant_router = APIRouter(prefix="/marketing", tags=["Marketing"])


@tenant_router.get("/landing-templates", response_model=list[LandingPageTemplateSummary])
async def list_landing_templates(
    _: CurrentUser, db: AsyncSession = Depends(get_db), niche: str | None = None
):
    return await service.list_templates(db, niche=niche)


@tenant_router.get(
    "/landing-templates/{slug}", response_model=LandingPageTemplateDetail
)
async def get_landing_template(
    slug: str, _: CurrentUser, db: AsyncSession = Depends(get_db)
):
    return await service.get_template_by_slug(db, slug)


@tenant_router.post("/landing-templates/apply", status_code=status.HTTP_201_CREATED)
async def apply_landing_template(
    body: ApplyTemplateRequest,
    ctx: CurrentTenantContext,
    db: AsyncSession = Depends(get_db),
):
    user, tenant, _role = ctx
    page = await service.apply_template_to_tenant(
        db,
        tenant_id=tenant.id,
        user_id=user.id,
        template_slug=body.template_slug,
        page_title=body.page_title,
        page_slug=body.page_slug,
    )
    return {
        "id": str(page.id),
        "slug": page.slug,
        "title": page.title,
        "redirect_to": "/dashboard/site-builder",
    }


# ──────────────────────────────────────────────────────────────────────────────
# Public router — /public/marketing/*
# ──────────────────────────────────────────────────────────────────────────────

public_router = APIRouter(prefix="/public/marketing", tags=["Public · Marketing"])


@public_router.get("/bundle", response_model=PublicMarketingBundle)
async def public_bundle(db: AsyncSession = Depends(get_db)):
    """Single hit the public marketing site uses to render server-side.

    Returns every published section and the approved review carousel.
    """
    sections = await service.section_bundle(db)
    reviews = await service.list_public_reviews(db, only_carousel=True, limit=16)
    return {"sections": sections, "reviews": reviews}


@public_router.get("/adaptive-pages", response_model=list[AdaptiveLandingPageResponse])
async def public_adaptive_pages(db: AsyncSession = Depends(get_db)):
    return await service.list_adaptive_pages(db, only_published=True)


@public_router.get("/sections/{key}")
async def public_section(key: str, db: AsyncSession = Depends(get_db)):
    section = await service.get_section(db, key)
    if not section.is_published:
        from app.core.exceptions import NotFoundException
        raise NotFoundException(f"Marketing section '{key}'")
    return {"key": section.key, "data": section.data, "updated_at": section.updated_at}


@public_router.get("/reviews", response_model=list[PublicReviewResponse])
async def public_reviews(db: AsyncSession = Depends(get_db), limit: int = 16):
    return await service.list_public_reviews(db, only_carousel=True, limit=limit)


@public_router.post(
    "/reviews", response_model=PublicReviewResponse, status_code=status.HTTP_201_CREATED
)
@limiter.limit("4/minute")
async def submit_public_review(
    body: PublicReviewSubmit,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Visitor-submitted review. Sanitised in-flight and auto-displayed when safe."""
    review = await service.submit_public_review(
        db,
        author_name=body.author_name,
        author_role=body.author_role,
        author_location=body.author_location,
        author_email=body.author_email,
        author_company=body.author_company,
        rating=body.rating,
        quote=body.quote,
        metric=body.metric,
        capture_source=body.capture_source,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        referrer_url=request.headers.get("referer"),
    )
    return review


@public_router.get("/landing-templates", response_model=list[LandingPageTemplateSummary])
async def public_landing_templates(db: AsyncSession = Depends(get_db), niche: str | None = None):
    return await service.list_templates(db, niche=niche)
