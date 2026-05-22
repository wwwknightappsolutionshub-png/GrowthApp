"""Google Business public review URL for Review & Comments QR (C)."""
from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequestException, NotFoundException
from app.modules.integrations.service import get_connection
from app.modules.tenants.models import Tenant


async def get_public_google_review_url(db: AsyncSession, tenant: Tenant) -> dict:
    """
    Return the tenant's public Google review link.
    Requires Google Business Profile connected on the tenant account.
    """
    conn = await get_connection(db, tenant.id)
    if not conn or not conn.google_location_name:
        raise BadRequestException(
            "Google Business Profile is not connected. The business must connect GMB in CustomerFlow settings."
        )

    url = (tenant.google_review_url or "").strip()
    if not url:
        meta = conn.connection_metadata or {}
        url = (meta.get("new_review_uri") or meta.get("review_url") or "").strip()

    if not url:
        meta = conn.connection_metadata or {}
        loc = conn.google_location_name
        if loc:
            place_id = meta_place_id(meta, loc)
            if place_id:
                url = f"https://search.google.com/local/writereview?placeid={place_id}"
            elif conn.location_title:
                from urllib.parse import quote_plus

                url = f"https://www.google.com/maps/search/?api=1&query={quote_plus(conn.location_title)}"

    if not url:
        raise NotFoundException("Google review URL")

    return {
        "review_url": url,
        "location_title": conn.location_title,
        "connected": True,
    }


def meta_place_id(metadata: dict, location_name: str) -> str | None:
    for loc in metadata.get("locations") or []:
        if loc.get("name") == location_name:
            return loc.get("placeId") or loc.get("place_id")
    return metadata.get("placeId") or metadata.get("place_id")
