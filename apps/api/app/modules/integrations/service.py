"""Google Business Profile integration service."""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from jose import JWTError, jwt
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import BadRequestException, NotFoundException
from app.modules.integrations.models import GoogleBusinessReview, TenantGoogleConnection
from app.modules.integrations.token_crypto import decrypt_secret, encrypt_secret
from app.services.google_business.client import (
    GoogleBusinessClient,
    GoogleBusinessError,
    build_authorization_url,
    exchange_code_for_tokens,
    refresh_access_token,
    token_expires_at,
)

logger = logging.getLogger(__name__)

_STATE_ALG = "HS256"
_STATE_TTL_SEC = 600


def _google_configured() -> bool:
    return bool(
        settings.GOOGLE_CLIENT_ID
        and settings.GOOGLE_CLIENT_SECRET
        and settings.GOOGLE_REDIRECT_URI
        and settings.INTEGRATIONS_TOKEN_ENCRYPTION_KEY
    )


def create_oauth_state(*, tenant_id: uuid.UUID, user_id: uuid.UUID) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(tenant_id),
        "uid": str(user_id),
        "typ": "google_oauth",
        "iat": int(now.timestamp()),
        "exp": int(now.timestamp()) + _STATE_TTL_SEC,
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=_STATE_ALG)


def parse_oauth_state(state: str) -> tuple[uuid.UUID, uuid.UUID]:
    try:
        payload = jwt.decode(state, settings.JWT_SECRET, algorithms=[_STATE_ALG])
        if payload.get("typ") != "google_oauth":
            raise BadRequestException("Invalid OAuth state")
        return uuid.UUID(payload["sub"]), uuid.UUID(payload["uid"])
    except (JWTError, ValueError) as exc:
        raise BadRequestException("Invalid or expired OAuth state") from exc


def connect_authorization_url(*, tenant_id: uuid.UUID, user_id: uuid.UUID) -> str:
    if not _google_configured():
        raise BadRequestException("Google Business integration is not configured on this server")
    state = create_oauth_state(tenant_id=tenant_id, user_id=user_id)
    return build_authorization_url(state=state)


async def get_connection(db: AsyncSession, tenant_id: uuid.UUID) -> TenantGoogleConnection | None:
    return (
        await db.execute(
            select(TenantGoogleConnection).where(TenantGoogleConnection.tenant_id == tenant_id)
        )
    ).scalar_one_or_none()


async def connection_status(db: AsyncSession, tenant_id: uuid.UUID) -> dict[str, Any]:
    row = await get_connection(db, tenant_id)
    if not row:
        return {
            "connected": False,
            "configured": _google_configured(),
            "location_title": None,
            "google_location_name": None,
            "last_sync_at": None,
        }
    return {
        "connected": bool(row.google_location_name),
        "configured": _google_configured(),
        "location_title": row.location_title,
        "google_location_name": row.google_location_name,
        "google_account_name": row.google_account_name,
        "last_sync_at": row.last_sync_at.isoformat() if row.last_sync_at else None,
        "available_locations": row.connection_metadata.get("locations") or [],
    }


async def _save_tokens(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    *,
    token_payload: dict[str, Any],
    account_name: str,
    location: dict[str, Any] | None,
    all_locations: list[dict[str, Any]],
) -> TenantGoogleConnection:
    access = token_payload.get("access_token")
    if not access:
        raise BadRequestException("Google did not return an access token")

    refresh = token_payload.get("refresh_token")
    expires = token_expires_at(token_payload.get("expires_in"))

    location_name = (location or {}).get("name")
    location_title = (location or {}).get("title") or (location or {}).get("locationName")

    existing = await get_connection(db, tenant_id)
    if existing:
        row = existing
    else:
        row = TenantGoogleConnection(id=uuid.uuid4(), tenant_id=tenant_id, google_account_name=account_name)
        db.add(row)

    row.google_account_name = account_name
    row.google_location_name = location_name
    row.location_title = location_title
    row.access_token_encrypted = encrypt_secret(access)
    if refresh:
        row.refresh_token_encrypted = encrypt_secret(refresh)
    row.token_expires_at = expires
    row.connection_metadata = {
        "locations": [
            {"name": loc.get("name"), "title": loc.get("title") or loc.get("locationName")}
            for loc in all_locations
        ]
    }
    await db.commit()
    await db.refresh(row)
    return row


async def complete_oauth_callback(
    db: AsyncSession,
    *,
    code: str,
    tenant_id: uuid.UUID,
) -> TenantGoogleConnection:
    token_payload = await exchange_code_for_tokens(code)
    access = token_payload.get("access_token")
    if not access:
        raise BadRequestException("Google authorization failed")

    client = GoogleBusinessClient(access)
    accounts = await client.list_accounts()
    if not accounts:
        raise BadRequestException("No Google Business accounts found for this Google user")

    account = accounts[0]
    account_name = account.get("name") or ""
    if not account_name:
        raise BadRequestException("Google account response missing name")

    locations = await client.list_locations(account_name)
    if not locations:
        raise BadRequestException("No business locations found on this Google account")

    primary = locations[0]
    return await _save_tokens(
        db,
        tenant_id,
        token_payload=token_payload,
        account_name=account_name,
        location=primary,
        all_locations=locations,
    )


async def select_location(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    *,
    location_name: str,
) -> TenantGoogleConnection:
    row = await get_connection(db, tenant_id)
    if not row:
        raise NotFoundException("Google connection")

    meta_locs = row.connection_metadata.get("locations") or []
    match = next((loc for loc in meta_locs if loc.get("name") == location_name), None)
    if not match and row.google_account_name:
        client = await _client_for_connection(db, row)
        locations = await client.list_locations(row.google_account_name)
        match = next((loc for loc in locations if loc.get("name") == location_name), None)
        if match:
            row.connection_metadata = {
                "locations": [
                    {"name": loc.get("name"), "title": loc.get("title") or loc.get("locationName")}
                    for loc in locations
                ]
            }

    if not match:
        raise BadRequestException("Unknown location")

    row.google_location_name = location_name
    row.location_title = match.get("title") or location_name
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return row


async def disconnect_google(db: AsyncSession, tenant_id: uuid.UUID) -> None:
    row = await get_connection(db, tenant_id)
    if not row:
        return
    await db.execute(delete(GoogleBusinessReview).where(GoogleBusinessReview.tenant_id == tenant_id))
    await db.delete(row)
    await db.commit()


async def _client_for_connection(
    db: AsyncSession,
    row: TenantGoogleConnection,
) -> GoogleBusinessClient:
    access = decrypt_secret(row.access_token_encrypted)
    if row.token_expires_at and row.token_expires_at <= datetime.now(timezone.utc):
        if row.refresh_token_encrypted:
            refreshed = await refresh_access_token(decrypt_secret(row.refresh_token_encrypted))
            access = refreshed.get("access_token") or access
            row.access_token_encrypted = encrypt_secret(access)
            if refreshed.get("refresh_token"):
                row.refresh_token_encrypted = encrypt_secret(refreshed["refresh_token"])
            row.token_expires_at = token_expires_at(refreshed.get("expires_in"))
            db.add(row)
            await db.commit()
    return GoogleBusinessClient(access)


def _parse_star(review: dict[str, Any]) -> str | None:
    rating = review.get("starRating") or review.get("star_rating")
    return str(rating) if rating else None


def _parse_review_time(review: dict[str, Any]) -> datetime | None:
    raw = review.get("createTime") or review.get("updateTime")
    if not raw:
        return None
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return None


async def sync_google_reviews(db: AsyncSession, tenant_id: uuid.UUID) -> dict[str, Any]:
    row = await get_connection(db, tenant_id)
    if not row or not row.google_location_name:
        raise BadRequestException("Google Business is not connected")

    client = await _client_for_connection(db, row)
    try:
        reviews = await client.list_reviews(row.google_location_name)
    except GoogleBusinessError as exc:
        logger.error("Google review sync failed tenant=%s: %s", tenant_id, exc)
        raise BadRequestException("Could not fetch reviews from Google") from exc

    synced = 0
    for review in reviews:
        name = review.get("name")
        if not name:
            continue
        reviewer = (review.get("reviewer") or {}).get("displayName")
        comment = review.get("comment")
        reply = (review.get("reviewReply") or {}).get("comment")
        star = _parse_star(review)
        created = _parse_review_time(review)

        existing = (
            await db.execute(
                select(GoogleBusinessReview).where(
                    GoogleBusinessReview.tenant_id == tenant_id,
                    GoogleBusinessReview.google_review_name == name,
                )
            )
        ).scalar_one_or_none()

        if existing:
            existing.reviewer_display_name = reviewer
            existing.star_rating = star
            existing.comment = comment
            existing.reply_comment = reply
            existing.review_created_at = created
            existing.raw_data = review
            existing.synced_at = datetime.now(timezone.utc)
            db.add(existing)
        else:
            db.add(
                GoogleBusinessReview(
                    id=uuid.uuid4(),
                    tenant_id=tenant_id,
                    google_review_name=name,
                    reviewer_display_name=reviewer,
                    star_rating=star,
                    comment=comment,
                    reply_comment=reply,
                    review_created_at=created,
                    raw_data=review,
                )
            )
            synced += 1

    row.last_sync_at = datetime.now(timezone.utc)
    db.add(row)
    await db.commit()
    return {"synced": synced, "total_fetched": len(reviews)}


async def list_google_reviews(db: AsyncSession, tenant_id: uuid.UUID) -> list[GoogleBusinessReview]:
    rows = (
        await db.execute(
            select(GoogleBusinessReview)
            .where(GoogleBusinessReview.tenant_id == tenant_id)
            .order_by(GoogleBusinessReview.review_created_at.desc().nullslast())
        )
    ).scalars().all()
    return list(rows)


async def reply_to_google_review(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    *,
    review_id: uuid.UUID,
    comment: str,
) -> GoogleBusinessReview:
    row = await get_connection(db, tenant_id)
    if not row or not row.google_location_name:
        raise BadRequestException("Google Business is not connected")

    review = (
        await db.execute(
            select(GoogleBusinessReview).where(
                GoogleBusinessReview.id == review_id,
                GoogleBusinessReview.tenant_id == tenant_id,
            )
        )
    ).scalar_one_or_none()
    if not review:
        raise NotFoundException("Google review")

    text = comment.strip()
    if not text:
        raise BadRequestException("Reply cannot be empty")

    client = await _client_for_connection(db, row)
    try:
        await client.reply_to_review(review.google_review_name, text)
    except GoogleBusinessError as exc:
        raise BadRequestException("Google rejected this reply") from exc

    review.reply_comment = text
    review.reply_updated_at = datetime.now(timezone.utc)
    db.add(review)
    await db.commit()
    await db.refresh(review)
    return review
