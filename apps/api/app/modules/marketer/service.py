"""Marketer Tools — AI logic for funnel builder, audience research, competitor scan.

Implements the exact backend logic from Step 3:

  Funnel Builder
    - Input: funnel_type
    - Output: steps_json (Landing → Lead Magnet → Nurture → Offer → Upsell)
    - Add ai_notes

  Audience Research
    - Input: industry
    - Output: demographics_json, pain_points_json, opportunities_json

  Competitor Scanner
    - Visit website
    - Extract: strengths, weaknesses, pricing, positioning gaps
"""
from __future__ import annotations

import logging
import re
import uuid
from typing import Any, Optional

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.marketer.models import (
    AudienceResearchReport,
    CompetitorIntelligenceReport,
    MarketerFunnelBlueprint,
)

logger = logging.getLogger(__name__)


# ── 1. FUNNEL BUILDER ─────────────────────────────────────────────────────


# Each step is the canonical 5-stage funnel:
#   Landing → Lead Magnet → Nurture → Offer → Upsell
# The funnel_type tailors copy, CTA, and channels per step.
_FUNNEL_TEMPLATES: dict[str, list[dict[str, Any]]] = {
    "lead_generation": [
        {
            "stage": "Landing",
            "goal": "Capture attention from cold traffic",
            "asset": "High-converting landing page",
            "headline": "Get more {service} customers this month",
            "cta": "Get Free Quote",
            "channel": "google_ads, meta_ads",
        },
        {
            "stage": "Lead Magnet",
            "goal": "Trade value for contact details",
            "asset": "Free checklist / guide / cost calculator",
            "headline": "Free: The {service} buyer's checklist",
            "cta": "Download Now",
            "channel": "landing_page_form",
        },
        {
            "stage": "Nurture",
            "goal": "Build trust and educate the lead",
            "asset": "5-email automated sequence",
            "headline": "Why most {service} quotes are wrong",
            "cta": "Read More",
            "channel": "email, sms",
        },
        {
            "stage": "Offer",
            "goal": "Convert nurtured lead to a paying customer",
            "asset": "Tripwire offer + booking calendar",
            "headline": "Book your {service} consultation — first 30 mins free",
            "cta": "Book Now",
            "channel": "booking_link",
        },
        {
            "stage": "Upsell",
            "goal": "Increase customer lifetime value",
            "asset": "Maintenance plan / premium tier",
            "headline": "Protect your investment with our care plan",
            "cta": "Upgrade",
            "channel": "email, in_app",
        },
    ],
    "ecommerce": [
        {
            "stage": "Landing",
            "goal": "Drive product discovery",
            "asset": "Product landing page",
            "headline": "Meet the {service} everyone's talking about",
            "cta": "Shop Now",
            "channel": "meta_ads, tiktok_ads",
        },
        {
            "stage": "Lead Magnet",
            "goal": "Capture email for first-time discount",
            "asset": "10% off first order popup",
            "headline": "Get 10% off your first order",
            "cta": "Claim Discount",
            "channel": "popup",
        },
        {
            "stage": "Nurture",
            "goal": "Show social proof + product education",
            "asset": "Welcome flow + UGC reviews",
            "headline": "See how customers use {service}",
            "cta": "Read Reviews",
            "channel": "email",
        },
        {
            "stage": "Offer",
            "goal": "Convert browser to buyer",
            "asset": "Cart abandonment + flash sale",
            "headline": "Your cart is waiting",
            "cta": "Complete Order",
            "channel": "email, sms",
        },
        {
            "stage": "Upsell",
            "goal": "Increase AOV",
            "asset": "Post-purchase upsell + subscribe & save",
            "headline": "Never run out — subscribe and save 15%",
            "cta": "Subscribe",
            "channel": "thank_you_page",
        },
    ],
    "high_ticket": [
        {
            "stage": "Landing",
            "goal": "Attract qualified prospects",
            "asset": "VSL (video sales letter) page",
            "headline": "The premium {service} solution for serious operators",
            "cta": "Watch The Video",
            "channel": "linkedin_ads, youtube_ads",
        },
        {
            "stage": "Lead Magnet",
            "goal": "Pre-qualify with an application",
            "asset": "Application form (5-7 questions)",
            "headline": "Apply to work with us",
            "cta": "Apply Now",
            "channel": "typeform",
        },
        {
            "stage": "Nurture",
            "goal": "Build authority before the sales call",
            "asset": "Case studies + 3-touch sequence",
            "headline": "How [client] grew with {service}",
            "cta": "Read Case Study",
            "channel": "email",
        },
        {
            "stage": "Offer",
            "goal": "Close on a discovery call",
            "asset": "1:1 strategy call",
            "headline": "Book your strategy call",
            "cta": "Schedule Call",
            "channel": "calendar_invite",
        },
        {
            "stage": "Upsell",
            "goal": "Expand engagement",
            "asset": "Done-for-you / retainer tier",
            "headline": "Ready to scale? Let us handle it for you",
            "cta": "Talk To Us",
            "channel": "account_manager",
        },
    ],
}

_FUNNEL_FALLBACK = _FUNNEL_TEMPLATES["lead_generation"]


async def build_funnel(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    funnel_type: Optional[str],
) -> MarketerFunnelBlueprint:
    """Generate a 5-stage funnel blueprint + persist it."""
    key = (funnel_type or "lead_generation").strip().lower().replace(" ", "_")
    template = _FUNNEL_TEMPLATES.get(key, _FUNNEL_FALLBACK)

    ai_notes = (
        f"Generated funnel for type='{key}' using the canonical "
        f"Landing → Lead Magnet → Nurture → Offer → Upsell framework. "
        f"Recommended channels: {', '.join({c for s in template for c in s['channel'].split(', ')})}. "
        f"Total stages: {len(template)}."
    )

    blueprint = MarketerFunnelBlueprint(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        funnel_type=key,
        steps_json=template,
        ai_notes=ai_notes,
    )
    db.add(blueprint)
    await db.flush()
    return blueprint


# ── 2. AUDIENCE RESEARCH ──────────────────────────────────────────────────


_INDUSTRY_KNOWLEDGE: dict[str, dict[str, Any]] = {
    "plumbing": {
        "demographics": {
            "primary_age": "30-65",
            "household_income": "£40k+",
            "homeowner_share": "78%",
            "decision_maker": "Homeowner / property manager",
            "geo": "Suburban + urban UK",
        },
        "pain_points": [
            "Burst pipes and emergency leaks at unsociable hours",
            "Difficulty finding a trustworthy local plumber",
            "Hidden fees and call-out charges",
            "Long wait times for non-emergency jobs",
            "Insurance paperwork after water damage",
        ],
        "opportunities": [
            "24/7 emergency response tier with transparent pricing",
            "Annual boiler & pipe maintenance plans",
            "Same-day quote tool via WhatsApp/web",
            "Insurance-partner referrals",
            "Eco-friendly retrofit (low-flow / heat-pump) upsell",
        ],
    },
    "electrical": {
        "demographics": {
            "primary_age": "28-60",
            "household_income": "£45k+",
            "homeowner_share": "72%",
            "decision_maker": "Homeowner / landlord",
            "geo": "All UK",
        },
        "pain_points": [
            "Outdated consumer units / fuse boards",
            "EV charger installation complexity",
            "Compliance certificates for landlords (EICR)",
            "Concern over rogue traders",
            "Lighting upgrades during renovations",
        ],
        "opportunities": [
            "EV charger install + grant assistance bundle",
            "EICR-as-a-service for landlords",
            "Smart-home consultation tier",
            "Annual safety check membership",
            "Solar + battery integration partnerships",
        ],
    },
    "cleaning": {
        "demographics": {
            "primary_age": "25-55",
            "household_income": "£35k+",
            "homeowner_share": "55%",
            "decision_maker": "Working professional / busy parent",
            "geo": "Urban + commuter towns",
        },
        "pain_points": [
            "Trust — letting strangers into the home",
            "Inconsistent quality between visits",
            "Last-minute cancellations",
            "Eco-conscious clients want green products",
            "Move-in / move-out deep-clean spikes",
        ],
        "opportunities": [
            "Subscription cleaning plans with same-team guarantee",
            "Eco-cleaning premium tier",
            "Move-out deep-clean partner with estate agents",
            "Office / retail commercial cleaning expansion",
            "Loyalty referral rewards",
        ],
    },
}


_GENERIC_REPORT: dict[str, Any] = {
    "demographics": {
        "primary_age": "25-55",
        "household_income": "£35k+",
        "decision_maker": "Owner / manager",
        "geo": "UK",
    },
    "pain_points": [
        "Difficulty finding a reliable local provider",
        "Lack of transparent pricing",
        "Slow response and poor communication",
        "Inconsistent quality between visits",
    ],
    "opportunities": [
        "Same-day booking with clear pricing",
        "Subscription / membership tier for recurring revenue",
        "Local SEO + Google review programme",
        "Referral incentives for existing customers",
    ],
}


async def generate_audience_research(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    industry: Optional[str],
) -> AudienceResearchReport:
    """Generate a structured audience research report and persist it."""
    key = (industry or "").strip().lower()
    data = _INDUSTRY_KNOWLEDGE.get(key, _GENERIC_REPORT)

    report = AudienceResearchReport(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        industry=key or "general",
        demographics_json=data["demographics"],
        pain_points_json=data["pain_points"],
        opportunities_json=data["opportunities"],
    )
    db.add(report)
    await db.flush()
    return report


# ── 3. COMPETITOR SCANNER ─────────────────────────────────────────────────


_PRICE_RE = re.compile(r"(?:£|\$|€)\s?\d{1,4}(?:[.,]\d{2})?\s?(?:/\s?(?:mo|month|yr|year))?", re.I)
_TAG_RE = re.compile(r"<[^>]+>")
_WHITESPACE_RE = re.compile(r"\s+")


async def scan_competitor(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    competitor_name: Optional[str],
    website: Optional[str],
) -> CompetitorIntelligenceReport:
    """Visit competitor website and extract strengths/weaknesses/pricing/gaps."""
    page_text = ""
    page_title = ""
    fetch_error: str | None = None

    if website:
        url = website if website.startswith("http") else f"https://{website}"
        try:
            async with httpx.AsyncClient(
                timeout=15.0,
                follow_redirects=True,
                headers={"User-Agent": "CustomerFlowBot/1.0 (+https://customerflow.ai)"},
            ) as client:
                resp = await client.get(url)
                html = resp.text or ""
                title_match = re.search(r"<title[^>]*>(.*?)</title>", html, re.I | re.S)
                if title_match:
                    page_title = _WHITESPACE_RE.sub(" ", title_match.group(1)).strip()
                page_text = _WHITESPACE_RE.sub(" ", _TAG_RE.sub(" ", html)).strip()
        except Exception as exc:
            fetch_error = str(exc)
            logger.warning("Competitor scan fetch failed for %s: %s", website, exc)

    strengths, weaknesses, gaps = _extract_signals(page_text)
    pricing = _extract_pricing(page_text)

    report = CompetitorIntelligenceReport(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        competitor_name=competitor_name or page_title or "Unknown",
        website=website,
        strengths_json=strengths,
        weaknesses_json=weaknesses,
        pricing_json={
            "samples": pricing,
            "positioning_gaps": gaps,
            "fetch_error": fetch_error,
            "page_title": page_title or None,
        },
    )
    db.add(report)
    await db.flush()
    return report


def _extract_signals(text: str) -> tuple[list[str], list[str], list[str]]:
    """Heuristic extraction of strengths, weaknesses, positioning gaps."""
    lowered = text.lower()
    strengths: list[str] = []
    weaknesses: list[str] = []
    gaps: list[str] = []

    strength_signals = {
        "24/7 availability": ["24/7", "24 hours", "always open"],
        "Free quotes": ["free quote", "free estimate", "no obligation"],
        "Strong social proof": ["reviews", "trustpilot", "5-star", "google rated"],
        "Accreditation": ["accredited", "certified", "gas safe", "niceic", "checkatrade"],
        "Same-day service": ["same day", "same-day", "today only"],
        "Money-back guarantee": ["money back", "guarantee", "satisfaction guaranteed"],
        "Wide service range": ["installation", "repair", "maintenance", "servicing"],
    }
    weakness_signals = {
        "No clear pricing": ["call for price", "contact us for pricing"],
        "Slow contact options": ["please call", "phone only", "no email form"],
        "Outdated design hints": ["copyright 201", "best viewed in"],
        "Limited service coverage": ["serving only", "local area only"],
    }
    gap_signals = {
        "No online booking": ["book online", "schedule online"],
        "No live chat": ["live chat", "chat with us"],
        "No mobile-friendly proof": ["responsive", "mobile-friendly"],
        "No transparent pricing": ["from £", "starting at"],
        "No subscription / membership": ["membership", "subscription"],
    }

    for label, needles in strength_signals.items():
        if any(n in lowered for n in needles):
            strengths.append(label)
    for label, needles in weakness_signals.items():
        if any(n in lowered for n in needles):
            weaknesses.append(label)
    # gaps = signals the competitor is MISSING
    for label, needles in gap_signals.items():
        if not any(n in lowered for n in needles):
            gaps.append(label)

    if not text:
        weaknesses.append("Website unreachable or empty")
        gaps.append("Site not accessible — easy SEO opportunity")

    return strengths, weaknesses, gaps


def _extract_pricing(text: str) -> list[str]:
    """Pull up to 10 unique price strings from the page text."""
    matches = _PRICE_RE.findall(text)
    samples = []
    for m in matches:
        s = m.strip()
        if s not in samples:
            samples.append(s)
        if len(samples) >= 10:
            break
    return samples
