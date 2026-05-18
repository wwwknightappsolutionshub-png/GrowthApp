"""Parser — initial URL generation from source.url_pattern.

RULE 1 (mandatory):
    url_pattern may contain: {page}, {query}, {category}, etc.
    Generate sequential pages until depth reached.
"""
from __future__ import annotations

import re
from urllib.parse import urlencode, urlparse, urlunparse, parse_qs, urljoin

# Placeholder detection
_PLACEHOLDER_RE = re.compile(r"\{(\w+)\}")


def _has_placeholder(url_pattern: str, name: str) -> bool:
    return f"{{{name}}}" in url_pattern


def generate_initial_urls(url_pattern: str, depth: int) -> list[str]:
    """Generate the initial list of target URLs from url_pattern.

    Supports named placeholders (Rule 1):
        {page}      — replaced with sequential integers 1…depth
        {query}     — left as empty string when not supplied (crawl-time)
        {category}  — left as empty string when not supplied (crawl-time)
        any other   — replaced with empty string

    When the pattern contains no {page} placeholder, the pattern itself is
    returned as a single seed URL (depth-1 seed list). The crawler will then
    discover additional pages via link extraction.

    Args:
        url_pattern: raw source URL pattern from ai_scraper_sources.
        depth:       number of paginated URLs to generate.

    Returns:
        Ordered list of unique initial URLs.
    """
    if not url_pattern:
        return []

    depth = max(1, depth)

    placeholders = set(_PLACEHOLDER_RE.findall(url_pattern))

    if "page" in placeholders:
        urls: list[str] = []
        seen: set[str] = set()
        for page in range(1, depth + 1):
            url = url_pattern
            # Substitute {page}
            url = url.replace("{page}", str(page))
            # Substitute remaining known patterns with defaults
            url = url.replace("{query}", "")
            url = url.replace("{category}", "")
            # Substitute any remaining unknown placeholders with empty string
            url = _PLACEHOLDER_RE.sub("", url)
            url = url.strip()
            if url and url not in seen:
                seen.add(url)
                urls.append(url)
        return urls

    # No {page} placeholder — return pattern as-is after substituting others
    url = url_pattern
    url = url.replace("{query}", "")
    url = url.replace("{category}", "")
    url = _PLACEHOLDER_RE.sub("", url)
    url = url.strip()
    return [url] if url else []


# Aggression level → page depth mapping (Rule 5)
DEPTH_MAP: dict[str, int] = {
    "low":    1,
    "medium": 2,
    "high":   3,
    "extreme": 9999,   # unlimited — crawler enforces actual cap elsewhere
}

# Aggression level → max crawl pages (Rule 3)
PAGE_CAP_MAP: dict[str, int] = {
    "low":    2,
    "medium": 6,
    "high":   15,
    "extreme": 9999,
}
