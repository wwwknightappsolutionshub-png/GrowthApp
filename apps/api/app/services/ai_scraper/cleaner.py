"""Cleaner — content normalisation for the CustomerFlow Crawler.

RULE 3 (mandatory):
    Normalize:
        - remove scripts, styles, ads
        - convert HTML to clean text paragraphs
        - lower-case duplicates
        - fix special characters
        - trim whitespace
        - deduplicate repeated blocks (common in directories)
"""
from __future__ import annotations

import re
import unicodedata
from html import unescape

# ── Compiled patterns ─────────────────────────────────────────────────────────

# Strip entire script / style / noscript / iframe / ad blocks including content
_BLOCK_STRIP_RE = re.compile(
    r"<(script|style|noscript|iframe|object|embed|form)[^>]*?>.*?</\1>",
    re.DOTALL | re.IGNORECASE,
)

# Strip ad-like blocks by class/id hints
_AD_ATTR_RE = re.compile(
    r'<[^>]+(class|id)\s*=\s*["\'][^"\']*(?:ad[_\-\s]|advert|banner|cookie|popup|newsletter|subscribe)[^"\']*["\'][^>]*>.*?</[^>]+>',
    re.DOTALL | re.IGNORECASE,
)

# Strip all remaining HTML tags (keep content)
_TAG_RE = re.compile(r"<[^>]+>", re.DOTALL)

# Collapse runs of whitespace (including \r\n) into single space
_SPACE_RE = re.compile(r"[ \t]+")

# Collapse multiple blank lines into one paragraph break
_PARA_RE = re.compile(r"\n{3,}")

# Non-printable control characters (except \n, \t)
_CTRL_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")

# Minimum meaningful paragraph length (skip nav/footer noise)
_MIN_BLOCK_LEN: int = 30


def _strip_html_blocks(html: str) -> str:
    """Remove scripts, styles, ads and other non-content blocks."""
    text = _BLOCK_STRIP_RE.sub(" ", html)
    text = _AD_ATTR_RE.sub(" ", text)
    return text


def _to_paragraphs(text: str) -> list[str]:
    """Convert raw text into cleaned non-empty paragraphs."""
    text = _TAG_RE.sub(" ", text)
    text = unescape(text)
    text = _CTRL_RE.sub("", text)
    # Normalise unicode (fix accented characters, ligatures, etc.)
    text = unicodedata.normalize("NFKC", text)
    # Collapse horizontal whitespace
    text = _SPACE_RE.sub(" ", text)
    # Split on line breaks, strip each, drop empties and navigation noise
    paras: list[str] = []
    for line in text.splitlines():
        line = line.strip()
        if len(line) >= _MIN_BLOCK_LEN:
            paras.append(line)
    return paras


def _deduplicate(paras: list[str]) -> list[str]:
    """Remove duplicate and near-duplicate text blocks.

    Two blocks are considered duplicates when their lowercased form is
    identical (common in directory pages where the same snippet appears in
    multiple listings).
    """
    seen: set[str] = set()
    out: list[str] = []
    for p in paras:
        key = p.lower()
        if key not in seen:
            seen.add(key)
            out.append(p)
    return out


def clean_content(html: str) -> str:
    """Clean and normalise raw HTML into plain text.

    Steps (per Rule 3):
        1. Strip scripts, styles, ads.
        2. Convert HTML to text paragraphs.
        3. Fix special characters and encoding.
        4. Trim whitespace.
        5. Deduplicate repeated blocks.

    Returns a clean, paragraph-joined string ready for AI extraction.
    """
    if not html:
        return ""
    stripped = _strip_html_blocks(html)
    paras = _to_paragraphs(stripped)
    paras = _deduplicate(paras)
    result = _PARA_RE.sub("\n\n", "\n".join(paras))
    return result.strip()
