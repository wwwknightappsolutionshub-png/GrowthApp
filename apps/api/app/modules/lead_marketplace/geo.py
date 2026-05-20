"""UK postcode helpers for lead matching."""
from __future__ import annotations

import re

_OUTWARD_RE = re.compile(
    r"^([A-Z]{1,2}\d{1,2}[A-Z]?)",
    re.IGNORECASE,
)


def normalize_postcode(raw: str | None) -> str:
    if not raw:
        return ""
    return re.sub(r"\s+", "", raw.strip()).upper()


def outward_code(postcode: str | None) -> str:
    """Return UK outward code (e.g. SW1A from SW1A1AA)."""
    norm = normalize_postcode(postcode)
    if not norm:
        return ""
    if len(norm) > 3 and norm[-3] != " ":
        # Inward is last 3 chars when no space
        body = norm[:-3] if len(norm) > 4 else norm
    else:
        body = norm.split()[0] if " " in norm else norm
    m = _OUTWARD_RE.match(body if body else norm)
    return (m.group(1) if m else body[:4]).upper()


def postcodes_match(tenant_pc: str | None, lead_pc: str | None) -> bool:
    """True when outward codes match, or either is missing (loose fallback)."""
    t = outward_code(tenant_pc)
    l = outward_code(lead_pc)
    if not t or not l:
        return True
    if t == l:
        return True
    # Same district area: first 2-3 chars (e.g. SW1 vs SW1A — still close)
    return t[:2] == l[:2] or t[:3] == l[:3]


def business_type_to_category_name(business_type: str) -> str:
    """Map tenant signup trade slug to marketplace/scraper category display name."""
    key = (business_type or "").strip().lower().replace(" ", "_")
    return _TRADE_LABELS.get(key, business_type.replace("_", " ").title() if business_type else "Other")


_TRADE_LABELS: dict[str, str] = {
    "plumber": "Plumber",
    "electrician": "Electrician",
    "cleaner": "Cleaner",
    "roofer": "Roofer",
    "painter": "Painter & Decorator",
    "builder": "Builder",
    "landscaper": "Landscaper",
    "handyman": "Handyman",
    "salon": "Salon & Beauty",
    "hvac": "HVAC",
    "locksmith": "Locksmith",
    "other": "Other trade",
}
