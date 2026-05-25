"""
Business-category tool configuration.

SuperAdmin can enable/disable which dashboard modules (identified by their
frontend href) are visible to each business category.  When no DB row exists
for a category the frontend falls back to its hardcoded defaults.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException
from pydantic import BaseModel
from sqlalchemy import DateTime, ForeignKey, String, func, select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.db_types import UUIDType, JSONBType

# AI Social and Marketer Tools hrefs — added in Step 5
AI_SOCIAL_HREFS: list[str] = [
    "/dashboard/ai-social/brand-identity",
    "/dashboard/ai-social/samples",
    "/dashboard/ai-social/preferences",
    "/dashboard/ai-social/drafts",
    "/dashboard/ai-social/approval",
    "/dashboard/ai-social/calendar",
]
MARKETER_HREFS: list[str] = [
    "/dashboard/marketer/funnel",
    "/dashboard/marketer/audience",
    "/dashboard/marketer/competitor",
    "/dashboard/marketer/quota",
]

# ── All known tool hrefs (canonical list mirrored from the frontend) ─────────
ALL_TOOL_HREFS: list[str] = [
    "/dashboard",
    "/dashboard/assistant",
    "/dashboard/leads",
    "/dashboard/crm",
    "/dashboard/tasks",
    "/dashboard/bookings",
    "/dashboard/quotes",
    "/dashboard/invoices",
    "/dashboard/accounts",
    "/dashboard/money",
    "/dashboard/messages",
    "/dashboard/whatsapp",
    "/dashboard/auto-replies",
    "/dashboard/outreach",
    "/dashboard/site-builder",
    "/dashboard/ads",
    "/dashboard/seo",
    "/dashboard/automations",
    "/dashboard/reviews",
    "/dashboard/membership-rewards",
    "/dashboard/notifications",
    "/dashboard/settings",
    *AI_SOCIAL_HREFS,
    *MARKETER_HREFS,
]
FREELANCER_TOOL_HREFS: list[str] = [
    "/dashboard/clients",
    *ALL_TOOL_HREFS,
]

# Tool labels (for the admin UI)
TOOL_LABELS: dict[str, str] = {
    "/dashboard":           "Dashboard",
    "/dashboard/clients":   "Clients",
    "/dashboard/assistant": "AI Assistant",
    "/dashboard/leads":     "Leads",
    "/dashboard/crm":       "CRM",
    "/dashboard/tasks":     "Tasks",
    "/dashboard/bookings":  "Bookings",
    "/dashboard/quotes":    "Quotes",
    "/dashboard/invoices":  "Invoices",
    "/dashboard/accounts":  "Accounts",
    "/dashboard/money":     "Accounts",
    "/dashboard/messages":  "Messages",
    "/dashboard/whatsapp":  "WhatsApp",
    "/dashboard/auto-replies": "AI Replies",
    "/dashboard/outreach":  "Outreach",
    "/dashboard/site-builder": "Business Page",
    "/dashboard/ads":       "Ads",
    "/dashboard/seo":       "SEO",
    "/dashboard/automations": "Automations",
    "/dashboard/reviews":   "Reviews",
    "/dashboard/membership-rewards": "Membership & Rewards",
    "/dashboard/notifications": "Notifications",
    "/dashboard/settings":  "Settings",
    # AI Social
    "/dashboard/ai-social/brand-identity": "Brand Identity",
    "/dashboard/ai-social/samples":        "Upload Samples",
    "/dashboard/ai-social/preferences":    "Posting Preferences",
    "/dashboard/ai-social/drafts":         "Draft Review",
    "/dashboard/ai-social/approval":       "Approval Flow",
    "/dashboard/ai-social/calendar":       "Scheduling Calendar",
    # Marketer
    "/dashboard/marketer/funnel":      "Funnel Builder",
    "/dashboard/marketer/audience":    "Audience Research",
    "/dashboard/marketer/competitor":  "Competitor Intelligence",
    "/dashboard/marketer/quota":       "Monthly Quota",
}

# Default enabled-tool sets per category (mirrors Sidebar.tsx CATEGORY_DEFAULTS).
# Each list is curated to show only the tools relevant to that business type.
CATEGORY_DEFAULTS: dict[str, list[str]] = {
    # Tradespeople: job/quote/invoice flow + local growth tools
    "tradesman": [
        "/dashboard", "/dashboard/leads", "/dashboard/crm",
        "/dashboard/tasks", "/dashboard/bookings", "/dashboard/quotes",
        "/dashboard/invoices", "/dashboard/money",
        "/dashboard/messages", "/dashboard/whatsapp", "/dashboard/auto-replies",
        "/dashboard/reviews", "/dashboard/membership-rewards",
        "/dashboard/site-builder", "", "/dashboard/outreach", "/dashboard/automations",
        *AI_SOCIAL_HREFS, *MARKETER_HREFS,
        "/dashboard/notifications",
        "/dashboard/settings",
    ],
    # Salons/beauty: appointments, loyalty, social proof
    "salon_beauty": [
        "/dashboard", "/dashboard/leads", "/dashboard/crm",
        "/dashboard/tasks", "/dashboard/bookings", "/dashboard/invoices", "/dashboard/money",
        "/dashboard/messages", "/dashboard/whatsapp", "/dashboard/auto-replies",
        "/dashboard/outreach", "/dashboard/reviews", "/dashboard/membership-rewards",
        "", "/dashboard/automations",
        *AI_SOCIAL_HREFS, *MARKETER_HREFS,
        "/dashboard/notifications",
        "/dashboard/settings",
    ],
    # Healthcare: appointments, compliance-light messaging, reputation
    "healthcare": [
        "/dashboard", "/dashboard/leads", "/dashboard/crm",
        "/dashboard/tasks", "/dashboard/bookings", "/dashboard/invoices", "/dashboard/money",
        "/dashboard/messages", "/dashboard/auto-replies",
        "/dashboard/reviews", "/dashboard/membership-rewards",
        "", "/dashboard/automations",
        *AI_SOCIAL_HREFS, *MARKETER_HREFS,
        "/dashboard/notifications",
        "/dashboard/settings",
    ],
    # Restaurants/food: bookings, messaging, reviews, local ads
    "restaurant_food": [
        "/dashboard", "/dashboard/leads", "/dashboard/crm",
        "/dashboard/tasks", "/dashboard/bookings", "/dashboard/money",
        "/dashboard/messages", "/dashboard/whatsapp", "/dashboard/auto-replies",
        "/dashboard/outreach", "/dashboard/reviews", "/dashboard/membership-rewards",
        "/dashboard/site-builder", "", "/dashboard/ads", "/dashboard/seo",
        "/dashboard/automations",
        *AI_SOCIAL_HREFS, *MARKETER_HREFS,
        "/dashboard/notifications",
        "/dashboard/settings",
    ],
    # Retail: CRM, messaging, loyalty, ads
    "retail": [
        "/dashboard", "/dashboard/leads", "/dashboard/crm",
        "/dashboard/tasks", "/dashboard/money",
        "/dashboard/messages", "/dashboard/whatsapp", "/dashboard/auto-replies",
        "/dashboard/outreach", "/dashboard/reviews", "/dashboard/membership-rewards",
        "/dashboard/site-builder", "", "/dashboard/ads", "/dashboard/seo",
        "/dashboard/automations",
        *AI_SOCIAL_HREFS, *MARKETER_HREFS,
        "/dashboard/notifications",
        "/dashboard/settings",
    ],
    # Fitness/wellness: memberships via bookings, outreach, reviews
    "fitness_wellness": [
        "/dashboard", "/dashboard/leads", "/dashboard/crm",
        "/dashboard/tasks", "/dashboard/bookings", "/dashboard/invoices", "/dashboard/money",
        "/dashboard/messages", "/dashboard/whatsapp", "/dashboard/auto-replies",
        "/dashboard/outreach", "/dashboard/reviews", "/dashboard/membership-rewards",
        "", "/dashboard/automations",
        *AI_SOCIAL_HREFS, *MARKETER_HREFS,
        "/dashboard/notifications",
        "/dashboard/settings",
    ],
    # Professional services: full pipeline, quotes, proposals, all growth tools
    "professional_services": ALL_TOOL_HREFS,
    # General fallback: full access
    "general": ALL_TOOL_HREFS,
}

KNOWN_CATEGORIES = list(CATEGORY_DEFAULTS.keys())

# ── Business-type classifier (mirrors Sidebar.tsx BIZ_PATTERNS) ──────────────
import re as _re

_BIZ_PATTERNS: list[tuple[str, "_re.Pattern[str]"]] = [
    ("tradesman",            _re.compile(
        r"plumb|electri|carpent|builder|roofer|painter|glazier|locksmith|hvac|plaster"
        r"|trades|handyman|gas|heating|boiler|joiner|tiler|flooring|landscap|garden"
        r"|cleaner|cleaning|window.?clean|pressure.?wash|pest.?control|drain|sewage"
        r"|remov|skip.?hire|scaffolding|fencing|paving|bricklay|plasterer|decorator",
        _re.I,
    )),
    ("salon_beauty",         _re.compile(
        r"salon|beauty|hair|nail|spa|barber|makeup|aesthet|lash|brow|wax|tanning"
        r"|tattoo|piercing|cosmetic|skin.?care|eyelash|eyebrow|massage|holistic",
        _re.I,
    )),
    ("healthcare",           _re.compile(
        r"clinic|doctor|gp|dentist|physio|health|medic|therap|chiro|optom|nurse"
        r"|pharma|dental|hospital|osteopath|podiat|audiolog|psychology|counsell"
        r"|acupunctur|vet|veterinar|midwife|care.?home|care.?worker",
        _re.I,
    )),
    ("restaurant_food",      _re.compile(
        r"restaurant|café|cafe|food|takeaway|catering|baker|bistro|pub|hospit"
        r"|diner|kitchen|pizza|burger|sushi|curry|chinese|indian|thai|kebab|chippy|fish.?chip"
        r"|sandwich|deli|coffee|tea.?room|canteen|meal.?prep",
        _re.I,
    )),
    ("retail",               _re.compile(
        r"shop|retail|boutique|store|fashion|clothing|jewel|florist|gift|market"
        r"|newsagent|off.?licence|pet.?shop|toy|book.?shop|music.?shop|art.?supplies"
        r"|hardware|diy|garden.?centre|antique",
        _re.I,
    )),
    ("fitness_wellness",     _re.compile(
        r"gym|fitness|yoga|pilates|personal.?train|sport|wellness|coach|crossfit"
        r"|martial|dance|swim|tennis|golf|boxing|running|cycling|bootcamp|nutrition",
        _re.I,
    )),
    ("professional_services", _re.compile(
        r"account|solicitor|architect|consult|lawyer|finance|advisor|agent|pr |design"
        r"|market|recruit|insurance|mortgage|estate.?agent|letting|surveyor|it.?support"
        r"|web.?develop|software|media|photograp|videograph|translat|event|wedding",
        _re.I,
    )),
]


def classifyBusiness_py(business_type: str) -> str:
    for cat, pattern in _BIZ_PATTERNS:
        if pattern.search(business_type):
            return cat
    return "general"


# ── ORM model ─────────────────────────────────────────────────────────────────

class BusinessCategoryConfig(Base):
    __tablename__ = "business_category_configs"

    # category slug is the primary key (e.g. "tradesman")
    category: Mapped[str] = mapped_column(String(60), primary_key=True)
    enabled_tools: Mapped[list] = mapped_column(JSONBType, default=list)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    updated_by: Mapped[uuid.UUID | None] = mapped_column(
        UUIDType, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )


# ── Pydantic schemas ──────────────────────────────────────────────────────────

class CategoryToolConfigResponse(BaseModel):
    model_config = {"from_attributes": True}
    category: str
    enabled_tools: list[str]
    is_customised: bool
    updated_at: datetime | None = None


class CategoryToolConfigUpdate(BaseModel):
    enabled_tools: list[str]


# ── Service helpers ───────────────────────────────────────────────────────────

async def get_all_configs(db: AsyncSession) -> list[dict[str, Any]]:
    """Return merged config for every known category (DB overrides defaults)."""
    rows = {
        r.category: r
        for r in (await db.execute(select(BusinessCategoryConfig))).scalars()
    }
    result = []
    for cat in KNOWN_CATEGORIES:
        row = rows.get(cat)
        result.append({
            "category": cat,
            "enabled_tools": row.enabled_tools if row else CATEGORY_DEFAULTS[cat],
            "is_customised": row is not None,
            "updated_at": row.updated_at if row else None,
        })
    return result


async def get_config_for_category(db: AsyncSession, category: str) -> list[str]:
    """Return the effective enabled-tool list for a single category."""
    row = (await db.execute(
        select(BusinessCategoryConfig).where(
            BusinessCategoryConfig.category == category
        )
    )).scalar_one_or_none()
    if row:
        return list(row.enabled_tools)
    return CATEGORY_DEFAULTS.get(category, ALL_TOOL_HREFS)


async def upsert_config(
    db: AsyncSession,
    category: str,
    enabled_tools: list[str],
    updated_by: uuid.UUID | None = None,
) -> dict[str, Any]:
    """Create or replace the tool config for a category."""
    if category not in KNOWN_CATEGORIES:
        raise HTTPException(status_code=404, detail=f"Unknown category: {category!r}")
    # Validate all hrefs
    unknown = [h for h in enabled_tools if h not in ALL_TOOL_HREFS]
    if unknown:
        raise HTTPException(status_code=422, detail=f"Unknown tool hrefs: {unknown}")

    row = (await db.execute(
        select(BusinessCategoryConfig).where(
            BusinessCategoryConfig.category == category
        )
    )).scalar_one_or_none()

    if row:
        row.enabled_tools = enabled_tools
        row.updated_at = datetime.now(timezone.utc)
        row.updated_by = updated_by
    else:
        row = BusinessCategoryConfig(
            category=category,
            enabled_tools=enabled_tools,
            updated_by=updated_by,
        )
        db.add(row)

    await db.commit()
    await db.refresh(row)
    return {
        "category": row.category,
        "enabled_tools": row.enabled_tools,
        "is_customised": True,
        "updated_at": row.updated_at,
    }


async def reset_config(db: AsyncSession, category: str) -> dict[str, Any]:
    """Delete any custom config, reverting to hardcoded defaults."""
    if category not in KNOWN_CATEGORIES:
        raise HTTPException(status_code=404, detail=f"Unknown category: {category!r}")
    await db.execute(
        delete(BusinessCategoryConfig).where(
            BusinessCategoryConfig.category == category
        )
    )
    await db.commit()
    return {
        "category": category,
        "enabled_tools": CATEGORY_DEFAULTS[category],
        "is_customised": False,
        "updated_at": None,
    }
