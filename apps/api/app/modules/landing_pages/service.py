"""AI landing-page generator + CRUD.

The generator asks the LLM to return a structured `sections` list following our
section catalogue, then validates each section through Pydantic before
persisting. If the model returns unknown section types, we skip them rather
than failing — graceful degradation > total failure.
"""
from __future__ import annotations

import json
import logging
import re
import uuid
from datetime import datetime, timezone

from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundException, ValidationException
from app.modules.landing_pages.models import LandingPage
from app.modules.landing_pages.schemas import (
    GenerateRequest,
    LandingPageCreate,
    LandingPageUpdate,
    Section,
)
from app.modules.tenants.models import Tenant
from app.services.ai.router import get_ai_router
from app.services.ai.types import AIRouterError

logger = logging.getLogger(__name__)


_GENERATOR_SYSTEM = (
    "You are an expert UK SMB conversion copywriter and landing-page designer. "
    "You produce production-ready landing-page JSON, NOT prose. "
    "Output ONLY a single JSON object with this shape:\n"
    '{"title": "Page title (<=60 chars)", '
    '"meta_description": "<=155 chars meta description", '
    '"sections": [ {"type": "hero|features|testimonials|trust_badges|faq|cta|lead_form|pricing|gallery|rich_text", "props": {...}} ]}'
    "\n\n"
    "Section type → props contract:\n"
    "  hero: {eyebrow?:str, headline:str (8-12 words), subheadline:str, primary_cta_text:str, secondary_cta_text?:str, image_brief:str}\n"
    "  features: {title:str, items:[{title:str (<=8 words), description:str (<=25 words), icon_hint?:str}] (3-6 items)}\n"
    "  testimonials: {title?:str, items:[{quote:str, author:str, role?:str, rating?:int}] (2-4 items)}\n"
    "  trust_badges: {title?:str, items:[{label:str}] (3-6 items)}\n"
    "  faq: {title?:str, items:[{question:str, answer:str}] (4-8 items)}\n"
    "  cta: {headline:str, subheadline?:str, primary_cta_text:str}\n"
    "  lead_form: {title:str, subheadline?:str, fields:[{name:str, label:str, type:'text|email|tel|textarea', required:bool}], submit_text:str}\n"
    "  pricing: {title:str, plans:[{name:str, price_text:str, features:list[str], cta_text:str, featured?:bool}]}\n"
    "  rich_text: {markdown:str}\n"
    "  gallery: {title?:str, image_briefs:list[str]}\n"
    "\n"
    "Rules: British English. No emoji. No invented statistics, prices, or "
    "testimonials with full personal names — use first-name + initial or job "
    "title only. Lead-form should request only first_name + phone OR email + "
    "service. Image briefs are 1-sentence prompts a designer/AI can use."
)


async def generate_page(
    db: AsyncSession,
    tenant: Tenant,
    user_id: uuid.UUID | None,
    req: GenerateRequest,
) -> tuple[LandingPage | None, dict]:
    """Run the LLM, validate, optionally persist. Returns (page_or_none, payload)."""

    user_prompt = (
        f"Business: {tenant.name} ({tenant.business_type})\n"
        f"Website: {tenant.website_url or '(none)'}\n"
        f"Location: {tenant.city or ''} {tenant.postcode}\n"
        f"Business summary: {req.business_summary}\n"
        f"Primary offer: {req.primary_offer}\n"
        f"Target audience: {req.target_audience or 'local customers'}\n"
        f"Tone: {req.tone}\n"
        f"Primary CTA text: {req.cta_text}\n"
        f"Sections to include (in order): {', '.join(req.include_sections)}"
    )

    router_svc = get_ai_router()
    try:
        response = await router_svc.chat(
            messages=[
                {"role": "system", "content": _GENERATOR_SYSTEM},
                {"role": "user", "content": user_prompt},
            ],
            tenant_id=tenant.id,
            user_id=user_id,
            purpose="landing_page_generator",
            max_tokens=2500,
            temperature=0.6,
        )
    except AIRouterError as exc:
        raise ValidationException(f"AI router unavailable: {exc}") from exc

    parsed = _parse_json(response.content or "")
    title = (parsed.get("title") or req.primary_offer)[:255]
    meta = (parsed.get("meta_description") or req.business_summary[:155])[:400]
    raw_sections = parsed.get("sections") or []

    sections: list[Section] = []
    for s in raw_sections:
        if not isinstance(s, dict):
            continue
        try:
            sections.append(Section.model_validate(s))
        except ValidationError as exc:
            logger.warning("Skipping invalid generated section: %s", exc)

    # Ensure we always have a lead-form section so the page actually converts.
    if not any(s.type == "lead_form" for s in sections):
        sections.append(
            Section(
                type="lead_form",
                props={
                    "title": "Get in touch",
                    "subheadline": "We typically reply within an hour.",
                    "fields": [
                        {"name": "first_name", "label": "Your name", "type": "text", "required": True},
                        {"name": "phone", "label": "Phone", "type": "tel", "required": True},
                        {"name": "email", "label": "Email", "type": "email", "required": False},
                        {"name": "message", "label": "What do you need help with?", "type": "textarea", "required": False},
                    ],
                    "submit_text": req.cta_text,
                },
            )
        )

    payload = {
        "title": title,
        "meta_description": meta,
        "sections": [s.model_dump(mode="json") for s in sections],
        "provider": response.provider,
        "model": response.model,
    }

    if not req.save:
        return None, {**payload, "page_id": None, "slug": req.slug or _slugify(title)}

    slug = req.slug or await _unique_slug(db, tenant.id, _slugify(title))

    page = LandingPage(
        id=uuid.uuid4(),
        tenant_id=tenant.id,
        slug=slug,
        title=title,
        meta_description=meta,
        sections=[s.model_dump(mode="json") for s in sections],
        theme={"primary_color": tenant.primary_color or "#2563EB"},
        ai_provider=response.provider,
        ai_model=response.model,
        ai_prompt=user_prompt,
        created_by_user_id=user_id,
    )
    db.add(page)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        # Slug collision — retry with a suffixed slug.
        page.slug = await _unique_slug(db, tenant.id, slug)
        db.add(page)
        await db.commit()
    await db.refresh(page)
    return page, {**payload, "page_id": page.id, "slug": page.slug}


async def create_page(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
    data: LandingPageCreate,
) -> LandingPage:
    page = LandingPage(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        slug=data.slug,
        title=data.title,
        meta_description=data.meta_description,
        cover_image_url=data.cover_image_url,
        theme=data.theme,
        sections=[s.model_dump(mode="json") for s in data.sections],
        created_by_user_id=user_id,
    )
    db.add(page)
    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise ValidationException("A landing page with this slug already exists") from exc
    await db.refresh(page)
    return page


async def update_page(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    page_id: uuid.UUID,
    data: LandingPageUpdate,
) -> LandingPage:
    page = await _get(db, tenant_id, page_id)
    if data.title is not None:
        page.title = data.title
    if data.meta_description is not None:
        page.meta_description = data.meta_description
    if data.cover_image_url is not None:
        page.cover_image_url = data.cover_image_url
    if data.theme is not None:
        page.theme = data.theme
    if data.sections is not None:
        page.sections = [s.model_dump(mode="json") for s in data.sections]
    if data.is_published is not None:
        page.is_published = data.is_published
        page.published_at = datetime.now(timezone.utc) if data.is_published else None
    db.add(page)
    await db.commit()
    await db.refresh(page)
    return page


async def delete_page(
    db: AsyncSession, tenant_id: uuid.UUID, page_id: uuid.UUID
) -> None:
    page = await _get(db, tenant_id, page_id)
    await db.delete(page)
    await db.commit()


async def list_pages(db: AsyncSession, tenant_id: uuid.UUID) -> list[LandingPage]:
    rows = (
        await db.execute(
            select(LandingPage)
            .where(LandingPage.tenant_id == tenant_id)
            .order_by(LandingPage.updated_at.desc())
        )
    ).scalars().all()
    return list(rows)


async def get_public_page(
    db: AsyncSession, tenant_slug: str, page_slug: str
) -> LandingPage:
    tenant = (
        await db.execute(
            select(Tenant).where(Tenant.slug == tenant_slug, Tenant.is_active.is_(True))
        )
    ).scalar_one_or_none()
    if not tenant:
        raise NotFoundException("Tenant")
    page = (
        await db.execute(
            select(LandingPage).where(
                LandingPage.tenant_id == tenant.id,
                LandingPage.slug == page_slug,
                LandingPage.is_published.is_(True),
            )
        )
    ).scalar_one_or_none()
    if not page:
        raise NotFoundException("LandingPage")
    return page


async def _get(db: AsyncSession, tenant_id: uuid.UUID, page_id: uuid.UUID) -> LandingPage:
    row = (
        await db.execute(
            select(LandingPage).where(
                LandingPage.id == page_id, LandingPage.tenant_id == tenant_id
            )
        )
    ).scalar_one_or_none()
    if not row:
        raise NotFoundException("LandingPage")
    return row


# ── Helpers ──────────────────────────────────────────────────────────────────

def _parse_json(raw: str) -> dict:
    raw = (raw or "").strip()
    if raw.startswith("```"):
        raw = raw.strip("`")
        if raw.lower().startswith("json"):
            raw = raw[4:]
    raw = raw.strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        start = raw.find("{")
        end = raw.rfind("}")
        if start != -1 and end != -1:
            try:
                return json.loads(raw[start : end + 1])
            except json.JSONDecodeError:
                pass
    return {}


def _slugify(text: str) -> str:
    text = (text or "").lower().strip()
    text = re.sub(r"[^a-z0-9]+", "-", text).strip("-")
    return (text[:80] or f"page-{uuid.uuid4().hex[:6]}")


async def _unique_slug(db: AsyncSession, tenant_id: uuid.UUID, base: str) -> str:
    """Return `base` if unused for this tenant, else suffix with -2, -3, …"""
    slug = base
    suffix = 2
    while True:
        existing = (
            await db.execute(
                select(LandingPage.id).where(
                    LandingPage.tenant_id == tenant_id, LandingPage.slug == slug
                )
            )
        ).scalar_one_or_none()
        if not existing:
            return slug
        slug = f"{base}-{suffix}"
        suffix += 1
        if suffix > 50:
            return f"{base}-{uuid.uuid4().hex[:6]}"
