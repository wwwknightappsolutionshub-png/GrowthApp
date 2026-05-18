"""Super Admin — Email Template Manager.

Endpoints:
  GET    /api/admin/email-templates/        list all templates
  GET    /api/admin/email-templates/{name}  get a single template's HTML
  PUT    /api/admin/email-templates/{name}  update a template's HTML
  POST   /api/admin/email-templates/{name}/preview  render preview with dummy vars
"""
from __future__ import annotations

import os
import re
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from app.core.dependencies import SuperAdmin

TEMPLATES_DIR = Path(__file__).parent.parent.parent / "templates" / "emails"

router = APIRouter(prefix="/api/admin/email-templates", tags=["Admin — Email Templates"])

# Human-readable descriptions for each template
TEMPLATE_META: dict[str, dict] = {
    "base":                  {"label": "Base Layout",          "description": "Master template extended by all others. Edit header/footer/branding here.", "category": "system"},
    "welcome":               {"label": "Welcome",              "description": "Sent immediately when a new user registers.", "category": "lifecycle"},
    "onboarding_reminder":   {"label": "Onboarding Reminder",  "description": "Sent on Day 3 and Day 7 to nudge new users through setup.", "category": "lifecycle"},
    "trial_expiry":          {"label": "Trial Expiry Warning",  "description": "Sent on Day 12 and Day 13 when the trial is about to end.", "category": "lifecycle"},
    "subscription_upsell":   {"label": "Subscription Upsell",  "description": "Sent on Day 10 if the user hasn't subscribed yet.", "category": "lifecycle"},
    "magic_link":            {"label": "Magic Sign-in Link",   "description": "Passwordless login link email.", "category": "auth"},
    "password_reset":        {"label": "Password Reset",       "description": "Password reset request email.", "category": "auth"},
    "booking_confirmation":  {"label": "Booking Confirmation", "description": "Sent to the customer when a booking is confirmed.", "category": "transactional"},
    "booking_reminder":      {"label": "Booking Reminder",     "description": "Sent to the customer before their appointment.", "category": "transactional"},
    "invoice_sent":          {"label": "Invoice Sent",         "description": "Sent when an invoice is issued to a customer.", "category": "transactional"},
    "invoice_paid":          {"label": "Invoice Paid",         "description": "Sent when a customer's payment is received.", "category": "transactional"},
    "invoice_overdue":       {"label": "Invoice Overdue",      "description": "Sent when an invoice becomes overdue.", "category": "transactional"},
    "quote_sent":            {"label": "Quote Sent",           "description": "Sent when a quote is sent to a customer.", "category": "transactional"},
    "quote_accepted":        {"label": "Quote Accepted",       "description": "Sent when a customer accepts a quote.", "category": "transactional"},
    "quote_declined":        {"label": "Quote Declined",       "description": "Sent when a customer declines a quote.", "category": "transactional"},
    "review_request":        {"label": "Review Request",       "description": "Sent after a job is completed to request a Google review.", "category": "transactional"},
}

DUMMY_VARS: dict[str, str] = {
    "first_name": "Jane",
    "last_name": "Smith",
    "email": "jane@example.com",
    "business_name": "Jane's Salon",
    "dashboard_url": "#",
    "login_url": "#",
    "magic_link_url": "#",
    "reset_url": "#",
    "trial_ends_at": "25 May 2026",
    "days_remaining": "2",
    "plan_name": "Growth",
    "plan_price": "£49/month",
    "booking_date": "28 May 2026 at 10:00",
    "service_name": "Cut & Colour",
    "invoice_number": "INV-0042",
    "invoice_total": "£120.00",
    "due_date": "1 June 2026",
    "quote_number": "QUO-0017",
    "quote_total": "£350.00",
    "review_link": "#",
    "unsubscribe_url": "#",
}


def _path(name: str) -> Path:
    safe = re.sub(r"[^a-z0-9_-]", "", name.lower())
    p = TEMPLATES_DIR / f"{safe}.html"
    if not p.exists():
        raise HTTPException(404, f"Template '{safe}' not found")
    return p


@router.get("")
async def list_templates(_: SuperAdmin):
    results = []
    for path in sorted(TEMPLATES_DIR.glob("*.html")):
        name = path.stem
        stat = path.stat()
        meta = TEMPLATE_META.get(name, {"label": name.replace("_", " ").title(), "description": "", "category": "other"})
        results.append({
            "name": name,
            "label": meta["label"],
            "description": meta["description"],
            "category": meta["category"],
            "size_bytes": stat.st_size,
            "updated_at": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
        })
    return results


@router.get("/{name}")
async def get_template(name: str, _: SuperAdmin):
    p = _path(name)
    meta = TEMPLATE_META.get(name, {"label": name.replace("_", " ").title(), "description": "", "category": "other"})
    stat = p.stat()
    return {
        "name": name,
        "label": meta["label"],
        "description": meta["description"],
        "category": meta["category"],
        "html": p.read_text(encoding="utf-8"),
        "size_bytes": stat.st_size,
        "updated_at": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
    }


class TemplateUpdate(BaseModel):
    html: str


@router.put("/{name}")
async def update_template(name: str, body: TemplateUpdate, _: SuperAdmin):
    p = _path(name)
    if not body.html.strip():
        raise HTTPException(422, "Template HTML cannot be empty")
    p.write_text(body.html, encoding="utf-8")
    stat = p.stat()
    return {
        "name": name,
        "updated_at": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
        "message": "Template saved",
    }


@router.post("/{name}/reset")
async def reset_template(name: str, _: SuperAdmin):
    """Restore from the .html.bak backup if it exists, else 404."""
    p = _path(name)
    bak = p.with_suffix(".html.bak")
    if not bak.exists():
        raise HTTPException(404, "No backup found for this template")
    p.write_text(bak.read_text(encoding="utf-8"), encoding="utf-8")
    return {"name": name, "message": "Template restored from backup"}


@router.post("/{name}/preview", response_class=HTMLResponse)
async def preview_template(name: str, _: SuperAdmin):
    """Render the template with dummy variables and return raw HTML for iframe preview."""
    from app.templates.renderer import render_email
    try:
        html = render_email(f"emails/{name}.html", DUMMY_VARS)
        return HTMLResponse(content=html)
    except Exception as exc:
        raise HTTPException(500, f"Render error: {exc}") from exc
