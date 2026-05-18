"""Negative-word sanitiser for visitor-submitted reviews.

Two-pass cleanup:

1. **Profanity / abuse**  — replaced with a neutral redaction marker (`***`).
2. **Negative sentiment vocabulary** — softened to a brand-safe synonym so
   that an enthusiastic visitor venting one frustration doesn't tank the
   tone of the homepage carousel. Reviews that are *primarily* negative
   (rating ≤ 3 or many flagged terms) are still recorded but flagged
   for moderation rather than auto-published.

We deliberately keep the dictionary short and conservative — anything more
opinionated would require a real NLP model, which lives behind the AI router.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable

# Hard-redact: profanity, slurs, harassment, defamation triggers.
# Kept intentionally minimal — extend in the admin UI in future.
PROFANITY = {
    "fuck", "fucking", "fucked", "fck", "fuk",
    "shit", "shitty", "shite",
    "bitch", "bastard", "cunt", "twat", "dick",
    "asshole", "ass", "arse", "arsehole",
    "damn", "bloody",  # mild — but kills enterprise tone
    "crap", "crappy",
    "wanker", "prick",
}

# Soften: negative-sentiment vocabulary mapped to brand-safe synonyms.
SOFTENERS: dict[str, str] = {
    # Outcome-negative
    "terrible": "needs improvement on",
    "awful": "challenging",
    "horrible": "not what we hoped for",
    "horrendous": "not what we hoped for",
    "nightmare": "complex situation",
    "disaster": "tricky moment",
    "disgusting": "not great",
    "appalling": "below expectations",
    "useless": "not yet right for us",
    "pointless": "not yet right for us",
    "worst": "lowest moment",
    "rubbish": "less polished",
    "garbage": "still rough",
    # Process-negative
    "scam": "uncertain billing experience",
    "scammers": "team behind the billing experience",
    "rip-off": "value question",
    "ripoff": "value question",
    "fraud": "misunderstanding",
    "fraudulent": "miscommunicated",
    "thief": "billing concern",
    "thieves": "billing concern",
    "lying": "miscommunicating",
    "liar": "miscommunication",
    "liars": "miscommunication",
    # People-negative
    "incompetent": "still learning",
    "useless staff": "team still finding their feet",
    "rude": "blunt",
    "ignorant": "still upskilling",
    "stupid": "less obvious",
    "idiot": "team member",
    "idiotic": "less obvious",
    "lazy": "less attentive",
    # Process specifics
    "hate": "found tricky",
    "hated": "found tricky",
    "broken": "needs polish",
    "buggy": "rough around the edges",
    "slow": "deliberate",
    "unprofessional": "informal",
}

# Compile word-boundary patterns once.
_PROFANITY_RE = re.compile(
    r"\b(?:" + "|".join(re.escape(w) for w in sorted(PROFANITY, key=len, reverse=True)) + r")\b",
    flags=re.IGNORECASE,
)
_SOFTENER_RE = re.compile(
    r"\b(?:" + "|".join(re.escape(w) for w in sorted(SOFTENERS.keys(), key=len, reverse=True)) + r")\b",
    flags=re.IGNORECASE,
)


@dataclass
class SanitiseResult:
    """Outcome of running `sanitise_review` over a quote."""

    cleaned: str
    """The text safe to display publicly."""

    flagged: list[str]
    """Distinct flagged terms found in the original text."""

    profanity_hit: bool
    """True when at least one profanity token was redacted."""

    softener_hit: bool
    """True when at least one negative-sentiment token was softened."""

    should_auto_publish: bool
    """True when the cleaned text is safe to auto-display on the marketing site."""


def _replace_profanity(text: str) -> tuple[str, list[str]]:
    found: list[str] = []

    def repl(match: re.Match[str]) -> str:
        found.append(match.group(0).lower())
        original = match.group(0)
        if len(original) <= 3:
            return "***"
        return original[0] + "***" + original[-1]

    return _PROFANITY_RE.sub(repl, text), found


def _replace_softeners(text: str) -> tuple[str, list[str]]:
    found: list[str] = []

    def repl(match: re.Match[str]) -> str:
        token = match.group(0)
        found.append(token.lower())
        replacement = SOFTENERS[token.lower()]
        # Preserve the leading capitalisation of the original token.
        if token[0].isupper():
            replacement = replacement[0].upper() + replacement[1:]
        return replacement

    return _SOFTENER_RE.sub(repl, text), found


def sanitise_review(quote: str, *, rating: int = 5) -> SanitiseResult:
    """Run the two-pass sanitiser over `quote`.

    `rating` is used purely to decide whether to auto-publish — text-level
    cleanup is identical regardless of stars.
    """
    if not quote or not quote.strip():
        return SanitiseResult(cleaned="", flagged=[], profanity_hit=False, softener_hit=False, should_auto_publish=False)

    cleaned, profanity_found = _replace_profanity(quote.strip())
    cleaned, softener_found = _replace_softeners(cleaned)

    flagged = sorted({*profanity_found, *softener_found})
    profanity_hit = bool(profanity_found)
    softener_hit = bool(softener_found)

    # Auto-publish policy: 4-5 stars *and* no profanity *and* fewer than 3
    # softened terms. Everything else gets queued for moderation.
    should_auto_publish = (
        rating >= 4
        and not profanity_hit
        and len(softener_found) < 3
        and len(cleaned) <= 800
    )

    return SanitiseResult(
        cleaned=cleaned,
        flagged=flagged,
        profanity_hit=profanity_hit,
        softener_hit=softener_hit,
        should_auto_publish=should_auto_publish,
    )


def initials_of(name: str) -> str:
    """Return up to two upper-case initials for an avatar tile."""
    parts = [p for p in (name or "").strip().split() if p]
    if not parts:
        return "?"
    if len(parts) == 1:
        return parts[0][:2].upper()
    return (parts[0][0] + parts[-1][0]).upper()


def any_flagged(words: Iterable[str]) -> bool:
    return any(word.lower() in PROFANITY or word.lower() in SOFTENERS for word in words)
