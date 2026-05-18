"""Fetcher — HTTP layer for the CustomerFlow Crawler.

RULE 2 (mandatory):
    Every request MUST follow:
        max_retries = 3
        sleep_between_retries = exponential backoff (1s, 3s, 7s)
        timeout = 15 seconds
        user-agent = "CustomerFlowBot/1.0"

RULE 6 — robots.txt compliance when possible.
"""
from __future__ import annotations

import asyncio
import logging
import urllib.robotparser
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

_BACKOFF_SECONDS: tuple[int, ...] = (1, 3, 7)
_TIMEOUT: float = 15.0
_USER_AGENT: str = "CustomerFlowBot/1.0"
_HEADERS: dict[str, str] = {"User-Agent": _USER_AGENT}

# In-memory robots cache to avoid re-fetching on every request.
_robots_cache: dict[str, urllib.robotparser.RobotFileParser] = {}


async def _load_robots(base_url: str) -> urllib.robotparser.RobotFileParser | None:
    """Fetch and parse robots.txt for base_url (best-effort)."""
    parsed = urlparse(base_url)
    origin = f"{parsed.scheme}://{parsed.netloc}"
    if origin in _robots_cache:
        return _robots_cache[origin]
    robots_url = f"{origin}/robots.txt"
    try:
        import httpx

        async with httpx.AsyncClient(timeout=5.0, follow_redirects=True) as client:
            resp = await client.get(robots_url, headers=_HEADERS)
            if resp.status_code == 200:
                rp = urllib.robotparser.RobotFileParser()
                rp.parse(resp.text.splitlines())
                _robots_cache[origin] = rp
                return rp
    except Exception as exc:  # noqa: BLE001
        logger.debug("robots.txt unavailable for %s: %s", origin, exc)
    return None


def _robots_allows(rp: urllib.robotparser.RobotFileParser | None, url: str) -> bool:
    """Return True when robots.txt allows crawling the URL (or when unknown)."""
    if rp is None:
        return True
    return rp.can_fetch(_USER_AGENT, url)


async def fetch_page(url: str) -> tuple[int, str]:
    """Fetch a single URL and return (status_code, html_content).

    Applies the mandatory retry/backoff/timeout/UA rules.
    Checks robots.txt before fetching (Rule 6).
    Returns (0, '') on terminal failure.
    """
    import httpx

    # Rule 6 — robots.txt compliance when possible
    rp = await _load_robots(url)
    if not _robots_allows(rp, url):
        logger.info("fetch_page: robots.txt disallows %s — skipping", url)
        return 0, ""

    last_exc: Exception | None = None
    for attempt in range(3):
        try:
            async with httpx.AsyncClient(
                timeout=_TIMEOUT,
                follow_redirects=True,
            ) as client:
                resp = await client.get(url, headers=_HEADERS)
                return resp.status_code, resp.text
        except Exception as exc:  # noqa: BLE001
            last_exc = exc
            logger.warning(
                "fetch_page attempt %d/3 failed for %s: %s",
                attempt + 1, url, exc,
            )
            if attempt < 2:
                await asyncio.sleep(_BACKOFF_SECONDS[attempt])

    logger.error("fetch_page exhausted retries for %s: %s", url, last_exc)
    return 0, ""
