"""Link extractor — discovers crawlable URLs inside a page.

RULE 4 (mandatory):
    Only extract <a href="..."> links that:
        - belong to the same root domain
        - contain business or directory patterns:
            /tradesmen/, /listing/, ?page=, /contact
"""
from __future__ import annotations

import re
from urllib.parse import urljoin, urlparse

# ── Compiled patterns ─────────────────────────────────────────────────────────

_HREF_RE = re.compile(r'href\s*=\s*["\']([^"\'#]+)["\']', re.IGNORECASE)

# Business / directory path patterns per spec
_DIRECTORY_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"/tradesmen", re.IGNORECASE),
    re.compile(r"/listing", re.IGNORECASE),
    re.compile(r"\?page=", re.IGNORECASE),
    re.compile(r"/contact", re.IGNORECASE),
    # Extended common business-directory patterns
    re.compile(r"/category", re.IGNORECASE),
    re.compile(r"/directory", re.IGNORECASE),
    re.compile(r"/profile", re.IGNORECASE),
    re.compile(r"/business", re.IGNORECASE),
    re.compile(r"/search", re.IGNORECASE),
    re.compile(r"/results", re.IGNORECASE),
    re.compile(r"/trade", re.IGNORECASE),
    re.compile(r"/service", re.IGNORECASE),
    re.compile(r"/contractor", re.IGNORECASE),
    re.compile(r"/supplier", re.IGNORECASE),
    re.compile(r"/find", re.IGNORECASE),
    re.compile(r"/near", re.IGNORECASE),
    re.compile(r"/local", re.IGNORECASE),
    re.compile(r"/page/", re.IGNORECASE),
    re.compile(r"[?&]p=\d+", re.IGNORECASE),
)


def _is_directory_pattern(href: str) -> bool:
    """Return True if the href matches at least one business/directory pattern."""
    for pattern in _DIRECTORY_PATTERNS:
        if pattern.search(href):
            return True
    return False


def _same_root_domain(base_netloc: str, target_netloc: str) -> bool:
    """Return True when both netlocs share the same root domain (per Rule 4)."""
    if not target_netloc:
        return False
    # Strip www prefix for comparison
    def _root(netloc: str) -> str:
        netloc = netloc.lower()
        if netloc.startswith("www."):
            netloc = netloc[4:]
        # Strip port if present
        return netloc.split(":")[0]

    return _root(base_netloc) == _root(target_netloc)


def extract_links(html: str, base_url: str) -> list[str]:
    """Extract valid crawlable links from HTML.

    Rules:
        - Same root domain only (Rule 4).
        - Link path must match a business/directory pattern (Rule 4).
        - Absolute URLs are returned (relative hrefs are resolved).
        - Duplicate URLs are dropped.
    """
    if not html or not base_url:
        return []

    base_parsed = urlparse(base_url)
    base_netloc = base_parsed.netloc

    seen: set[str] = set()
    results: list[str] = []

    for match in _HREF_RE.finditer(html):
        href = match.group(1).strip()
        if not href or href.startswith(("javascript:", "mailto:", "tel:", "#")):
            continue

        absolute = urljoin(base_url, href)
        parsed = urlparse(absolute)

        # Must be http(s)
        if parsed.scheme not in ("http", "https"):
            continue

        # Same root domain
        if not _same_root_domain(base_netloc, parsed.netloc):
            continue

        # Business / directory pattern
        path_and_query = parsed.path + ("?" + parsed.query if parsed.query else "")
        if not _is_directory_pattern(path_and_query):
            continue

        # Deduplicate
        if absolute in seen:
            continue
        seen.add(absolute)
        results.append(absolute)

    return results
