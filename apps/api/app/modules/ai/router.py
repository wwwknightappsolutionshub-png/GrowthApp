"""AI feature endpoints: review reply, lead scoring trigger, ads, SEO, onboarding."""
from __future__ import annotations

import json
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import CurrentTenantContext
from app.modules.leads.models import Lead
from app.modules.reputation.models import Review
from app.services.ai.lead_scoring import score_lead
from app.services.ai.prompts import REVIEW_REPLY_SYSTEM
from app.services.ai.router import get_ai_router
from app.services.ai.types import AIRouterError

router = APIRouter(prefix="/ai", tags=["AI"])


class ReviewReplyRequest(BaseModel):
    review_id: UUID
    tone: str = Field(default="warm and professional", max_length=80)


class ReviewReplyResponse(BaseModel):
    reply: str
    provider: str
    model: str
    cost_pence: int


class ScoreLeadResponse(BaseModel):
    lead_id: UUID
    score: int | None
    score_label: str | None
    score_reason: str | None


@router.post("/review-reply", response_model=ReviewReplyResponse)
async def generate_review_reply(
    body: ReviewReplyRequest,
    ctx: CurrentTenantContext,
    db: AsyncSession = Depends(get_db),
):
    _, tenant, _ = ctx
    review = (
        await db.execute(
            select(Review).where(Review.id == body.review_id, Review.tenant_id == tenant.id)
        )
    ).scalar_one_or_none()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")

    tenant_row = tenant
    star_label = "five-star" if review.rating >= 5 else "four-star" if review.rating == 4 else "three-star" if review.rating == 3 else "two-star" if review.rating == 2 else "one-star"

    user_prompt = (
        f"Business name: {tenant_row.name}\n"
        f"Business type: {tenant_row.business_type}\n"
        f"Tone: {body.tone}\n"
        f"Review rating: {review.rating}/5 ({star_label})\n"
        f"Review text: {review.feedback or '(no written feedback — rating only)'}\n"
        "Write a reply suitable for posting publicly on Google or Trustpilot."
    )

    router_svc = get_ai_router()
    try:
        response = await router_svc.chat(
            messages=[
                {"role": "system", "content": REVIEW_REPLY_SYSTEM},
                {"role": "user", "content": user_prompt},
            ],
            tenant_id=tenant.id,
            purpose="review_reply",
            max_tokens=300,
            temperature=0.6,
        )
    except AIRouterError as exc:
        raise HTTPException(status_code=503, detail=f"AI router unavailable: {exc}")

    return ReviewReplyResponse(
        reply=response.content,
        provider=response.provider,
        model=response.model,
        cost_pence=response.cost_pence,
    )


@router.post("/lead-score/{lead_id}", response_model=ScoreLeadResponse)
async def score_lead_now(
    lead_id: UUID,
    ctx: CurrentTenantContext,
    db: AsyncSession = Depends(get_db),
):
    _, tenant, _ = ctx
    lead = (
        await db.execute(
            select(Lead).where(
                Lead.id == lead_id,
                Lead.tenant_id == tenant.id,
                Lead.deleted_at.is_(None),
            )
        )
    ).scalar_one_or_none()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    scored = await score_lead(db, lead, tenant=tenant)
    return ScoreLeadResponse(
        lead_id=scored.id,
        score=scored.score,
        score_label=scored.score_label,
        score_reason=scored.score_reason,
    )


# ── Ads generator ────────────────────────────────────────────────────────────

class AdsGenerateRequest(BaseModel):
    platform: Literal["google", "facebook", "instagram", "tiktok"] = "google"
    objective: Literal["leads", "sales", "awareness"] = "leads"
    audience: str = Field(min_length=1, max_length=400)
    offer: str = Field(min_length=1, max_length=400)
    tone: str = Field(default="professional and confident", max_length=80)
    variant_count: int = Field(default=3, ge=1, le=5)


class AdCopyVariant(BaseModel):
    headline: str
    description: str
    primary_text: str | None = None
    cta: str | None = None
    image_brief: str | None = None


class AdsGenerateResponse(BaseModel):
    platform: str
    variants: list[AdCopyVariant]
    provider: str
    model: str


_ADS_SYSTEM = (
    "You are a senior performance-marketing copywriter for UK SMBs. "
    "Output ONLY valid JSON in this schema: "
    '{"variants": [{"headline": "...", "description": "...", "primary_text": "...", "cta": "...", "image_brief": "..."}]} '
    "Headlines max 30 chars for Google, 40 for Meta. Descriptions max 90 chars for Google, 125 for Meta. "
    "image_brief is a one-sentence brief for a designer/AI image. No emoji unless platform=tiktok."
)


@router.post("/ads", response_model=AdsGenerateResponse)
async def generate_ads(
    body: AdsGenerateRequest,
    ctx: CurrentTenantContext,
    db: AsyncSession = Depends(get_db),
):
    _, tenant, _ = ctx
    user_prompt = (
        f"Business: {tenant.name} ({tenant.business_type})\n"
        f"Platform: {body.platform}\n"
        f"Objective: {body.objective}\n"
        f"Target audience: {body.audience}\n"
        f"Offer: {body.offer}\n"
        f"Tone: {body.tone}\n"
        f"Variants to produce: {body.variant_count}"
    )

    router_svc = get_ai_router()
    try:
        response = await router_svc.chat(
            messages=[
                {"role": "system", "content": _ADS_SYSTEM},
                {"role": "user", "content": user_prompt},
            ],
            tenant_id=tenant.id,
            purpose="ads_generator",
            max_tokens=800,
            temperature=0.7,
        )
    except AIRouterError as exc:
        raise HTTPException(status_code=503, detail=f"AI router unavailable: {exc}")

    variants = _parse_variants(response.content, body.variant_count)
    return AdsGenerateResponse(
        platform=body.platform,
        variants=variants,
        provider=response.provider,
        model=response.model,
    )


def _parse_variants(raw: str, expected: int) -> list[AdCopyVariant]:
    raw = (raw or "").strip()
    if raw.startswith("```"):
        raw = raw.strip("`")
        if raw.lower().startswith("json"):
            raw = raw[4:]
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        start = raw.find("{")
        end = raw.rfind("}")
        if start != -1 and end != -1:
            try:
                parsed = json.loads(raw[start : end + 1])
            except json.JSONDecodeError:
                parsed = {"variants": []}
        else:
            parsed = {"variants": []}

    variants_raw = parsed.get("variants") or parsed.get("ads") or []
    out: list[AdCopyVariant] = []
    for v in variants_raw[:expected]:
        if not isinstance(v, dict):
            continue
        out.append(AdCopyVariant(
            headline=str(v.get("headline", "")).strip(),
            description=str(v.get("description", "")).strip(),
            primary_text=str(v.get("primary_text") or "").strip() or None,
            cta=str(v.get("cta") or "").strip() or None,
            image_brief=str(v.get("image_brief") or "").strip() or None,
        ))
    return out


# ── SEO assistant ────────────────────────────────────────────────────────────

class SeoAuditRequest(BaseModel):
    page_title: str = Field(min_length=1, max_length=255)
    meta_description: str = Field(default="", max_length=400)
    page_url: str = Field(min_length=1, max_length=500)
    body_excerpt: str = Field(default="", max_length=3000)
    target_keywords: list[str] = Field(default_factory=list, max_length=10)
    local_area: str = Field(default="", max_length=80)


class SeoAuditResponse(BaseModel):
    score: int
    summary: str
    suggested_title: str
    suggested_description: str
    suggested_keywords: list[str]
    gbp_recommendations: list[str]
    issues: list[str]
    provider: str
    model: str


_SEO_SYSTEM = (
    "You are a senior local-SEO consultant for UK SMBs. Audit the supplied page and respond ONLY "
    "in JSON with: {score:int(0-100), summary:str, suggested_title:str (<=60 chars), "
    "suggested_description:str (<=155 chars), suggested_keywords:list[str], "
    "gbp_recommendations:list[str] (Google Business Profile tips), issues:list[str]}. "
    "Be specific and actionable. Focus on local SEO if local_area is supplied."
)


@router.post("/seo/audit", response_model=SeoAuditResponse)
async def seo_audit(
    body: SeoAuditRequest,
    ctx: CurrentTenantContext,
    db: AsyncSession = Depends(get_db),
):
    _, tenant, _ = ctx
    user_prompt = (
        f"Business: {tenant.name} ({tenant.business_type})\n"
        f"Page URL: {body.page_url}\n"
        f"Current title: {body.page_title}\n"
        f"Current meta description: {body.meta_description or '(none)'}\n"
        f"Target keywords: {', '.join(body.target_keywords) or '(none provided)'}\n"
        f"Local area: {body.local_area or 'not provided'}\n"
        f"Body excerpt:\n{body.body_excerpt[:2000]}\n"
    )

    router_svc = get_ai_router()
    try:
        response = await router_svc.chat(
            messages=[
                {"role": "system", "content": _SEO_SYSTEM},
                {"role": "user", "content": user_prompt},
            ],
            tenant_id=tenant.id,
            purpose="seo_audit",
            max_tokens=900,
            temperature=0.3,
        )
    except AIRouterError as exc:
        raise HTTPException(status_code=503, detail=f"AI router unavailable: {exc}")

    parsed = _parse_seo(response.content)
    return SeoAuditResponse(
        score=parsed.get("score", 50),
        summary=parsed.get("summary", ""),
        suggested_title=parsed.get("suggested_title", ""),
        suggested_description=parsed.get("suggested_description", ""),
        suggested_keywords=parsed.get("suggested_keywords", []) or [],
        gbp_recommendations=parsed.get("gbp_recommendations", []) or [],
        issues=parsed.get("issues", []) or [],
        provider=response.provider,
        model=response.model,
    )


def _parse_seo(raw: str) -> dict:
    raw = (raw or "").strip()
    if raw.startswith("```"):
        raw = raw.strip("`")
        if raw.lower().startswith("json"):
            raw = raw[4:]
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


# ── Onboarding tutor ─────────────────────────────────────────────────────────

class OnboardingAskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=600)
    current_screen: str | None = Field(default=None, max_length=80)


class OnboardingAskResponse(BaseModel):
    answer: str
    next_steps: list[str]
    provider: str
    model: str


_ONBOARDING_SYSTEM = (
    "You are CustomerFlow AI's onboarding tutor. You help brand-new UK SMB users set up the platform. "
    "Be concise and friendly. Always finish with a short numbered list of next steps the user can do "
    "right now in the app. The platform has these top-level areas: Dashboard, AI Assistant, Leads, "
    "Pipeline (CRM), Tasks, Bookings, Quotes, Invoices, Money, Messages, Automations, Reviews, Social, "
    "Settings (incl. API Keys, Permissions, Integrations). Reply in British English."
)


@router.post("/onboarding/ask", response_model=OnboardingAskResponse)
async def onboarding_ask(
    body: OnboardingAskRequest,
    ctx: CurrentTenantContext,
):
    user, tenant, _ = ctx
    user_prompt = (
        f"User: {user.full_name} (role: {ctx[2]})\n"
        f"Business: {tenant.name} ({tenant.business_type})\n"
        f"Current screen: {body.current_screen or 'unknown'}\n"
        f"Question: {body.question}\n\n"
        "Reply with: short answer first, then a JSON-free numbered list of next steps."
    )

    router_svc = get_ai_router()
    try:
        response = await router_svc.chat(
            messages=[
                {"role": "system", "content": _ONBOARDING_SYSTEM},
                {"role": "user", "content": user_prompt},
            ],
            tenant_id=tenant.id,
            user_id=user.id,
            purpose="onboarding_tutor",
            max_tokens=500,
            temperature=0.5,
        )
    except AIRouterError as exc:
        raise HTTPException(status_code=503, detail=f"AI router unavailable: {exc}")

    answer, next_steps = _split_answer_and_steps(response.content)
    return OnboardingAskResponse(
        answer=answer,
        next_steps=next_steps,
        provider=response.provider,
        model=response.model,
    )


def _split_answer_and_steps(raw: str) -> tuple[str, list[str]]:
    """Extract numbered next-step bullets from the model output."""
    lines = (raw or "").splitlines()
    answer_lines: list[str] = []
    next_steps: list[str] = []
    in_steps = False
    for line in lines:
        stripped = line.strip()
        if not stripped:
            if in_steps:
                continue
            answer_lines.append("")
            continue
        # Detect numbered lists like "1." or "1)" or markdown bullets.
        if (
            stripped[:2] in ("1.", "1)", "2.", "2)", "3.", "3)", "4.", "4)", "5.", "5)")
            or stripped.startswith(("- ", "* "))
        ):
            in_steps = True
            # Strip leading marker
            for prefix in ("- ", "* "):
                if stripped.startswith(prefix):
                    stripped = stripped[len(prefix):]
                    break
            else:
                # Numeric prefix like "1." or "1)"
                while stripped and (stripped[0].isdigit() or stripped[0] in ".): "):
                    stripped = stripped[1:]
            stripped = stripped.strip()
            if stripped:
                next_steps.append(stripped)
            continue
        if in_steps:
            # Append continuation to the last step.
            if next_steps:
                next_steps[-1] = next_steps[-1] + " " + stripped
            continue
        answer_lines.append(stripped)
    return "\n".join(l for l in answer_lines if l).strip(), next_steps
