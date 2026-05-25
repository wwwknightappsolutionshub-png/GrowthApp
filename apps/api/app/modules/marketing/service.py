"""Business logic for the marketing CMS, public reviews and landing templates."""
from __future__ import annotations

import html
import logging
import uuid
from datetime import datetime, timezone
from typing import Iterable

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters import get_email_adapter
from app.adapters.email.base import EmailMessage
from app.core.config import settings
from app.core.exceptions import NotFoundException
from app.modules.auth.models import User
from app.modules.marketing.models import (
    AdaptiveLandingPage,
    LandingPageTemplate,
    MarketingReview,
    MarketingSection,
)
from app.modules.marketing.sanitiser import sanitise_review

log = logging.getLogger(__name__)

# ── Marketing sections ──────────────────────────────────────────────────────


async def list_sections(db: AsyncSession, *, only_published: bool = True) -> list[MarketingSection]:
    stmt = select(MarketingSection).order_by(MarketingSection.sort_order, MarketingSection.key)
    if only_published:
        stmt = stmt.where(MarketingSection.is_published.is_(True))
    return list((await db.execute(stmt)).scalars().all())


async def ensure_marketing_seeded(db: AsyncSession, *, force: bool = False) -> dict[str, int]:
    """Ensure default marketing CMS rows exist (idempotent unless `force=True`)."""
    from app.modules.marketing.seed import seed_marketing_data

    return await seed_marketing_data(db, replace=force)


async def get_section(db: AsyncSession, key: str) -> MarketingSection:
    section = (
        await db.execute(select(MarketingSection).where(MarketingSection.key == key))
    ).scalar_one_or_none()
    if not section:
        raise NotFoundException(f"Marketing section '{key}'")
    return section


async def upsert_section(
    db: AsyncSession,
    *,
    key: str,
    data: dict,
    title: str | None = None,
    description: str | None = None,
    is_published: bool = True,
    sort_order: int = 0,
    user_id: uuid.UUID | None = None,
) -> MarketingSection:
    existing = (
        await db.execute(select(MarketingSection).where(MarketingSection.key == key))
    ).scalar_one_or_none()
    if existing:
        existing.data = data
        if title is not None:
            existing.title = title
        if description is not None:
            existing.description = description
        existing.is_published = is_published
        existing.sort_order = sort_order
        existing.updated_by_user_id = user_id
        db.add(existing)
        await db.commit()
        await db.refresh(existing)
        return existing

    section = MarketingSection(
        id=uuid.uuid4(),
        key=key,
        title=title,
        description=description,
        data=data,
        is_published=is_published,
        sort_order=sort_order,
        updated_by_user_id=user_id,
    )
    db.add(section)
    await db.commit()
    await db.refresh(section)
    return section


async def patch_section(
    db: AsyncSession,
    key: str,
    *,
    title: str | None = None,
    description: str | None = None,
    data: dict | None = None,
    is_published: bool | None = None,
    sort_order: int | None = None,
    user_id: uuid.UUID | None = None,
) -> MarketingSection:
    section = await get_section(db, key)
    if title is not None:
        section.title = title
    if description is not None:
        section.description = description
    if data is not None:
        section.data = data
    if is_published is not None:
        section.is_published = is_published
    if sort_order is not None:
        section.sort_order = sort_order
    section.updated_by_user_id = user_id
    db.add(section)
    await db.commit()
    await db.refresh(section)
    return section


async def delete_section(db: AsyncSession, key: str) -> None:
    section = await get_section(db, key)
    await db.delete(section)
    await db.commit()


async def reorder_sections(
    db: AsyncSession,
    keys: list[str],
    *,
    user_id: uuid.UUID | None = None,
) -> None:
    """Assign `sort_order` from the given key order (10, 20, …). All keys must exist."""
    seen: list[str] = []
    for k in keys:
        if k not in seen:
            seen.append(k)
    for i, key in enumerate(seen):
        res = await db.execute(
            update(MarketingSection)
            .where(MarketingSection.key == key)
            .values(sort_order=(i + 1) * 10, updated_by_user_id=user_id)
        )
        if res.rowcount == 0:
            raise NotFoundException(f"Marketing section '{key}'")
    await db.commit()


async def section_bundle(db: AsyncSession) -> dict[str, dict]:
    """Bundle every published section as `{key: data}` for the marketing site."""
    sections = await list_sections(db, only_published=True)
    return {s.key: s.data for s in sections}


# ── Adaptive landing pages ──────────────────────────────────────────────────


async def list_adaptive_pages(
    db: AsyncSession,
    *,
    only_published: bool = True,
) -> list[AdaptiveLandingPage]:
    stmt = select(AdaptiveLandingPage).order_by(AdaptiveLandingPage.label)
    if only_published:
        stmt = stmt.where(AdaptiveLandingPage.is_published.is_(True))
    return list((await db.execute(stmt)).scalars().all())


async def get_adaptive_page(db: AsyncSession, niche_id: str) -> AdaptiveLandingPage:
    page = (
        await db.execute(
            select(AdaptiveLandingPage).where(AdaptiveLandingPage.niche_id == niche_id)
        )
    ).scalar_one_or_none()
    if not page:
        raise NotFoundException(f"Adaptive landing page '{niche_id}'")
    return page


async def upsert_adaptive_page(
    db: AsyncSession,
    *,
    niche_id: str,
    label: str,
    data: dict,
    is_published: bool = True,
    user_id: uuid.UUID | None = None,
) -> AdaptiveLandingPage:
    existing = (
        await db.execute(
            select(AdaptiveLandingPage).where(AdaptiveLandingPage.niche_id == niche_id)
        )
    ).scalar_one_or_none()
    if existing:
        existing.label = label
        existing.data = data
        existing.is_published = is_published
        existing.updated_by_user_id = user_id
        db.add(existing)
        await db.commit()
        await db.refresh(existing)
        return existing

    page = AdaptiveLandingPage(
        id=uuid.uuid4(),
        niche_id=niche_id,
        label=label,
        data=data,
        is_published=is_published,
        updated_by_user_id=user_id,
    )
    db.add(page)
    await db.commit()
    await db.refresh(page)
    return page


async def patch_adaptive_page(
    db: AsyncSession,
    niche_id: str,
    *,
    label: str | None = None,
    data: dict | None = None,
    is_published: bool | None = None,
    user_id: uuid.UUID | None = None,
) -> AdaptiveLandingPage:
    page = await get_adaptive_page(db, niche_id)
    if label is not None:
        page.label = label
    if data is not None:
        page.data = data
    if is_published is not None:
        page.is_published = is_published
    page.updated_by_user_id = user_id
    db.add(page)
    await db.commit()
    await db.refresh(page)
    return page


async def delete_adaptive_page(db: AsyncSession, niche_id: str) -> None:
    page = await get_adaptive_page(db, niche_id)
    await db.delete(page)
    await db.commit()


# ── Public reviews ──────────────────────────────────────────────────────────


def _to_public_dict(review: MarketingReview) -> dict:
    return {
        "id": review.id,
        "author_name": review.author_name,
        "author_role": review.author_role,
        "author_location": review.author_location,
        "rating": review.rating,
        "quote": review.quote,
        "metric": review.metric,
        "is_featured": review.is_featured,
        "created_at": review.created_at,
    }


async def _notify_superadmins_of_review(db: AsyncSession, review: MarketingReview) -> None:
    """Best-effort email alert so superadmins can approve and push reviews externally."""
    rows = await db.execute(
        select(User.email, User.full_name)
        .where(User.is_superadmin.is_(True), User.deleted_at.is_(None))
        .order_by(User.created_at.asc())
    )
    recipients = [(email, name) for email, name in rows.all() if email]
    if not recipients:
        return

    admin_url = f"{settings.FRONTEND_URL.rstrip('/')}/admin/reviews"
    gmb_status = "ready to queue" if review.status == "approved" else "needs approval first"
    safe_author = html.escape(review.author_name)
    safe_quote = html.escape(review.quote)
    safe_status = html.escape(review.status)
    safe_company = html.escape(review.author_company or "Not supplied")
    safe_email = html.escape(review.author_email or "Not supplied")

    html_body = f"""
    <div style="font-family:Arial,sans-serif;line-height:1.5;color:#0f172a">
      <h2>New CustomerFlow AI review submitted</h2>
      <p>A visitor review has been saved to the superadmin review queue.</p>
      <ul>
        <li><strong>Author:</strong> {safe_author}</li>
        <li><strong>Email:</strong> {safe_email}</li>
        <li><strong>Company:</strong> {safe_company}</li>
        <li><strong>Rating:</strong> {review.rating}/5</li>
        <li><strong>Status:</strong> {safe_status}</li>
        <li><strong>GMB:</strong> {gmb_status}</li>
      </ul>
      <blockquote style="border-left:4px solid #0f766e;margin:16px 0;padding:8px 12px;background:#f8fafc">
        {safe_quote}
      </blockquote>
      <p><a href="{admin_url}">Open superadmin reviews</a></p>
    </div>
    """
    text_body = (
        "New CustomerFlow AI review submitted\n\n"
        f"Author: {review.author_name}\n"
        f"Email: {review.author_email or 'Not supplied'}\n"
        f"Company: {review.author_company or 'Not supplied'}\n"
        f"Rating: {review.rating}/5\n"
        f"Status: {review.status}\n"
        f"GMB: {gmb_status}\n\n"
        f"{review.quote}\n\n"
        f"Open: {admin_url}\n"
    )

    try:
        adapter = get_email_adapter()
    except Exception as exc:  # noqa: BLE001
        log.warning("Failed to initialise email adapter for review %s: %s", review.id, exc)
        return

    for email, name in recipients:
        try:
            await adapter.send(
                EmailMessage(
                    to=email,
                    to_name=name or "",
                    subject=f"New review submitted: {review.rating}/5 from {review.author_name}",
                    html_body=html_body,
                    text_body=text_body,
                    reply_to=review.author_email,
                )
            )
        except Exception as exc:  # noqa: BLE001
            log.warning("Failed to notify superadmin %s about review %s: %s", email, review.id, exc)


async def submit_public_review(
    db: AsyncSession,
    *,
    author_name: str,
    author_role: str | None,
    author_location: str | None,
    author_email: str | None,
    author_company: str | None,
    rating: int,
    quote: str,
    metric: str | None,
    capture_source: str,
    ip_address: str | None = None,
    user_agent: str | None = None,
    referrer_url: str | None = None,
) -> MarketingReview:
    result = sanitise_review(quote, rating=rating)
    status = "approved" if result.should_auto_publish else "pending"
    is_carousel = result.should_auto_publish

    review = MarketingReview(
        id=uuid.uuid4(),
        author_name=author_name.strip(),
        author_role=(author_role or "").strip() or None,
        author_location=(author_location or "").strip() or None,
        author_email=(author_email or "").strip() or None,
        author_company=(author_company or "").strip() or None,
        rating=rating,
        quote=result.cleaned,
        quote_raw=quote.strip(),
        metric=(metric or "").strip() or None,
        status=status,
        is_featured=False,
        is_carousel=is_carousel,
        sanitised=result.profanity_hit or result.softener_hit,
        capture_source=capture_source,
        ip_address=ip_address,
        user_agent=user_agent,
        referrer_url=referrer_url,
    )
    db.add(review)
    await db.commit()
    await db.refresh(review)
    try:
        await _notify_superadmins_of_review(db, review)
    except Exception as exc:  # noqa: BLE001
        log.warning("Review notification failed for %s: %s", review.id, exc)
    return review


async def list_public_reviews(
    db: AsyncSession,
    *,
    only_carousel: bool = True,
    limit: int = 16,
) -> list[MarketingReview]:
    stmt = (
        select(MarketingReview)
        .where(MarketingReview.status == "approved")
        .order_by(MarketingReview.is_featured.desc(), MarketingReview.created_at.desc())
        .limit(limit)
    )
    if only_carousel:
        stmt = stmt.where(MarketingReview.is_carousel.is_(True))
    return list((await db.execute(stmt)).scalars().all())


async def list_all_reviews_for_admin(
    db: AsyncSession,
    *,
    status: str | None = None,
    limit: int = 200,
) -> list[MarketingReview]:
    stmt = select(MarketingReview).order_by(MarketingReview.created_at.desc()).limit(limit)
    if status:
        stmt = stmt.where(MarketingReview.status == status)
    return list((await db.execute(stmt)).scalars().all())


async def moderate_review(
    db: AsyncSession,
    review_id: uuid.UUID,
    *,
    status: str | None = None,
    is_featured: bool | None = None,
    is_carousel: bool | None = None,
    quote: str | None = None,
    author_role: str | None = None,
    author_location: str | None = None,
    metric: str | None = None,
) -> MarketingReview:
    review = (
        await db.execute(select(MarketingReview).where(MarketingReview.id == review_id))
    ).scalar_one_or_none()
    if not review:
        raise NotFoundException("Review")

    if status is not None:
        review.status = status
    if is_featured is not None:
        review.is_featured = is_featured
    if is_carousel is not None:
        review.is_carousel = is_carousel
    if quote is not None:
        review.quote = quote.strip()
    if author_role is not None:
        review.author_role = (author_role or "").strip() or None
    if author_location is not None:
        review.author_location = (author_location or "").strip() or None
    if metric is not None:
        review.metric = (metric or "").strip() or None

    db.add(review)
    await db.commit()
    await db.refresh(review)
    return review


async def push_review_external(
    db: AsyncSession,
    review_id: uuid.UUID,
    *,
    channel: str,
    target_url: str | None = None,
) -> MarketingReview:
    """Queue a review for external publishing.

    The actual API push (GMB Business Profile API, Trustpilot Business API) is
    a real integration that requires partner credentials. For now we update
    the audit fields synchronously so the operator UI can track status and
    surface a "Copy to clipboard" pre-formatted block.
    """
    review = (
        await db.execute(select(MarketingReview).where(MarketingReview.id == review_id))
    ).scalar_one_or_none()
    if not review:
        raise NotFoundException("Review")

    now = datetime.now(timezone.utc)
    if channel == "gmb":
        review.gmb_status = "queued" if not target_url else "pushed"
        review.gmb_pushed_at = now
        if target_url:
            review.gmb_url = target_url
    elif channel == "trustpilot":
        review.trustpilot_status = "queued" if not target_url else "pushed"
        review.trustpilot_pushed_at = now
        if target_url:
            review.trustpilot_url = target_url
    else:
        raise NotFoundException("Channel")

    db.add(review)
    await db.commit()
    await db.refresh(review)
    return review


# ── Landing-page templates ──────────────────────────────────────────────────


async def list_templates(
    db: AsyncSession,
    *,
    niche: str | None = None,
) -> list[LandingPageTemplate]:
    stmt = (
        select(LandingPageTemplate)
        .where(LandingPageTemplate.is_published.is_(True))
        .order_by(LandingPageTemplate.niche, LandingPageTemplate.sort_order, LandingPageTemplate.name)
    )
    if niche:
        stmt = stmt.where(LandingPageTemplate.niche == niche)
    return list((await db.execute(stmt)).scalars().all())


async def get_template_by_slug(db: AsyncSession, slug: str) -> LandingPageTemplate:
    tmpl = (
        await db.execute(select(LandingPageTemplate).where(LandingPageTemplate.slug == slug))
    ).scalar_one_or_none()
    if not tmpl:
        raise NotFoundException(f"Template '{slug}'")
    return tmpl


async def apply_template_to_tenant(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
    template_slug: str,
    page_title: str,
    page_slug: str | None = None,
):
    """Clone a template into a brand-new `landing_pages` row."""
    from app.modules.landing_pages.models import LandingPage
    from app.modules.landing_pages.service import _slugify as _slugify_slug

    tmpl = await get_template_by_slug(db, template_slug)
    final_slug = _slugify_slug(page_slug or page_title)

    # Ensure uniqueness per tenant.
    existing = (
        await db.execute(
            select(LandingPage).where(
                LandingPage.tenant_id == tenant_id, LandingPage.slug == final_slug
            )
        )
    ).scalar_one_or_none()
    if existing:
        # Append a numeric suffix until free.
        i = 2
        while True:
            candidate = f"{final_slug}-{i}"
            taken = (
                await db.execute(
                    select(LandingPage).where(
                        LandingPage.tenant_id == tenant_id, LandingPage.slug == candidate
                    )
                )
            ).scalar_one_or_none()
            if not taken:
                final_slug = candidate
                break
            i += 1

    page = LandingPage(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        slug=final_slug,
        title=page_title,
        meta_description=tmpl.description,
        theme=dict(tmpl.theme or {}),
        sections=[dict(s) for s in (tmpl.sections or [])],
        is_published=False,
        created_by_user_id=user_id,
    )
    db.add(page)
    await db.commit()
    await db.refresh(page)
    return page
