"""Batcher — groups crawled page content for AI extraction.

RULE 7 (mandatory):
    Group content into batches (5–25 pages) formatted as:
    [
        { "url": "...", "raw_text": "..." },
        ...
    ]
"""
from __future__ import annotations

from typing import TypedDict

# Batch size bounds per spec (5–25 pages)
_BATCH_MIN: int = 5
_BATCH_MAX: int = 25
_BATCH_SIZE: int = 10   # default batch size — within the 5–25 band


class PageEntry(TypedDict):
    url: str
    raw_text: str


def batch_content(pages: list[PageEntry]) -> list[list[PageEntry]]:
    """Split a list of page entries into batches of 5–25 pages each.

    Each element in the returned list is a batch (list of PageEntry dicts)
    ready to be sent to the AI extraction engine.

    Batch sizing:
        - Default batch size is 10 (within the spec 5–25 band).
        - A trailing batch that would be fewer than 5 entries is merged into
          the previous batch (to avoid sending micro-batches), unless it is
          the only batch.

    Args:
        pages: list of {"url": ..., "raw_text": ...} dicts.

    Returns:
        List of batches; empty list when input is empty.
    """
    if not pages:
        return []

    batches: list[list[PageEntry]] = []
    for i in range(0, len(pages), _BATCH_SIZE):
        chunk = pages[i : i + _BATCH_SIZE]
        batches.append(chunk)

    # Merge a trailing micro-batch (< _BATCH_MIN) into the previous one
    if len(batches) > 1 and len(batches[-1]) < _BATCH_MIN:
        last = batches.pop()
        batches[-1].extend(last)

    return batches
