"""Magic-link (passwordless) sign-in.

Flow:

  1. POST /auth/magic-link { email, next? }
     - We don't reveal whether the email exists. We always respond 200.
     - If the user exists, we mint a single-use token (raw + hash), persist the
       hash + expiry, and email the raw token to the user as a clickable link.
  2. GET /auth/magic-link/verify?token=...
     - Hash the supplied token, find the row, ensure not used/expired.
     - Stamp used_at and issue access + refresh cookies (same as login).
"""
from __future__ import annotations

import logging
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.email import get_email_adapter
from app.adapters.email.base import EmailMessage
from app.core.config import settings
from app.core.exceptions import UnauthorizedException
from app.core.security import hash_token
from app.modules.auth.models import MagicLinkToken, User

logger = logging.getLogger(__name__)

MAGIC_LINK_EXPIRE_MINUTES = 15


async def issue_magic_link(
    db: AsyncSession,
    *,
    email: str,
    next_path: str | None = None,
    ip: str | None = None,
    user_agent: str | None = None,
) -> None:
    """Mint a single-use sign-in link for the given email.

    Always returns silently — the caller MUST NOT reveal whether the email
    exists. If the user is found we email the link; otherwise we no-op.
    """
    email = email.lower().strip()
    user = (
        await db.execute(select(User).where(User.email == email, User.deleted_at.is_(None)))
    ).scalar_one_or_none()
    if not user:
        logger.info("magic-link: no user for email=%s (silent)", email)
        return

    raw = secrets.token_urlsafe(48)
    token_hash = hash_token(raw)
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=MAGIC_LINK_EXPIRE_MINUTES)

    db.add(
        MagicLinkToken(
            id=uuid.uuid4(),
            email=email,
            token_hash=token_hash,
            next_path=next_path,
            issued_to_ip=ip,
            issued_user_agent=user_agent,
            expires_at=expires_at,
        )
    )
    await db.commit()

    qs = urlencode({"token": raw, **({"next": next_path} if next_path else {})})
    url = f"{settings.FRONTEND_URL.rstrip('/')}/auth/magic-link/verify?{qs}"

    try:
        from app.templates.renderer import render_magic_link
        await get_email_adapter().send(EmailMessage(
            to=user.email,
            to_name=user.full_name,
            subject="Your CustomerFlow AI sign-in link",
            html_body=render_magic_link(
                full_name=user.full_name,
                email=user.email,
                magic_url=url,
                expires_in_minutes=MAGIC_LINK_EXPIRE_MINUTES,
            ),
        ))
    except Exception as exc:
        # Persist the link even if email failed — admin can recover from the DB
        # if necessary. Don't leak the failure back to the caller.
        logger.warning("magic-link email failed for %s: %s", user.email, exc)


async def consume_magic_link(
    db: AsyncSession,
    *,
    raw_token: str,
    ip: str | None = None,
) -> tuple[User, dict]:
    """Validate the token and issue an access + refresh token pair.

    Raises UnauthorizedException for any failure (expired, used, unknown).
    """
    token_hash = hash_token(raw_token)
    row = (
        await db.execute(select(MagicLinkToken).where(MagicLinkToken.token_hash == token_hash))
    ).scalar_one_or_none()

    if not row:
        raise UnauthorizedException("Invalid or expired sign-in link")
    if row.used_at is not None:
        raise UnauthorizedException("This sign-in link has already been used")
    if row.expires_at <= datetime.now(timezone.utc):
        raise UnauthorizedException("This sign-in link has expired")

    user = (
        await db.execute(select(User).where(User.email == row.email, User.deleted_at.is_(None)))
    ).scalar_one_or_none()
    if not user:
        raise UnauthorizedException("Account not found")

    row.used_at = datetime.now(timezone.utc)
    row.used_from_ip = ip
    db.add(row)
    await db.commit()

    # Defer to auth.service for token issuance so cookie behaviour stays consistent.
    from app.modules.auth import service as auth_service

    tokens = await auth_service._issue_tokens(db, user)
    return user, tokens
