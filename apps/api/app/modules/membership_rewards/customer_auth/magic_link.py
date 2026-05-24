"""Customer magic-link authentication (primary login method)."""

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
from app.core.security import create_access_token, hash_token
from app.modules.crm.models import Customer
from app.modules.membership_rewards.constants import CUSTOMER_MAGIC_LINK_EXPIRE_MINUTES
from app.modules.membership_rewards.models import MrCustomerMagicLink
from app.modules.tenants.models import Tenant

logger = logging.getLogger(__name__)


async def create_magic_link_token(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    customer_id: uuid.UUID,
    email: str,
) -> tuple[str, str] | None:
    """Persist a magic link and return (raw_token, verify_url). Does not send email."""
    email = email.lower().strip()
    customer = (
        await db.execute(
            select(Customer).where(
                Customer.id == customer_id,
                Customer.tenant_id == tenant_id,
                Customer.deleted_at.is_(None),
            )
        )
    ).scalar_one_or_none()
    if not customer:
        return None

    tenant = await db.get(Tenant, tenant_id)
    slug = tenant.slug if tenant else str(tenant_id)

    raw = secrets.token_urlsafe(48)
    token_hash = hash_token(raw)
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=CUSTOMER_MAGIC_LINK_EXPIRE_MINUTES)

    db.add(
        MrCustomerMagicLink(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            customer_id=customer_id,
            email=email,
            token_hash=token_hash,
            expires_at=expires_at,
        )
    )
    await db.flush()

    qs = urlencode({"token": raw, "tenant": slug})
    base = settings.FRONTEND_URL.rstrip("/")
    url = f"{base}/rewards/{slug}/auth/verify?{qs}"
    return raw, url


async def issue_magic_link(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    customer_id: uuid.UUID,
    email: str,
    next_path: str | None = None,
    ip: str | None = None,
) -> None:
    """Mint a single-use customer login link. Silent if customer not found."""
    email = email.lower().strip()
    created = await create_magic_link_token(
        db, tenant_id=tenant_id, customer_id=customer_id, email=email
    )
    if not created:
        return
    _, url = created
    if next_path:
        url = f"{url}&{urlencode({'next': next_path})}"

    await db.commit()

    customer = (
        await db.execute(
            select(Customer).where(
                Customer.id == customer_id,
                Customer.tenant_id == tenant_id,
                Customer.deleted_at.is_(None),
            )
        )
    ).scalar_one_or_none()
    tenant = await db.get(Tenant, tenant_id)
    tenant_name = tenant.name if tenant else "Rewards"
    try:
        await get_email_adapter().send(
            EmailMessage(
                to=email,
                to_name=customer.first_name if customer else email,
                subject=f"Your {tenant_name} rewards login link",
                html_body=(
                    f"<p>Hi {customer.first_name if customer else 'there'},</p>"
                    f"<p>Click below to open your rewards wallet (expires in "
                    f"{CUSTOMER_MAGIC_LINK_EXPIRE_MINUTES} minutes):</p>"
                    f'<p><a href="{url}">Open Rewards App</a></p>'
                ),
            )
        )
    except Exception as exc:
        logger.warning("customer magic-link email failed for %s: %s", email, exc)


async def consume_magic_link(
    db: AsyncSession,
    *,
    raw_token: str,
    tenant_id: uuid.UUID,
    ip: str | None = None,
) -> dict:
    token_hash = hash_token(raw_token)
    row = (
        await db.execute(
            select(MrCustomerMagicLink).where(
                MrCustomerMagicLink.token_hash == token_hash,
                MrCustomerMagicLink.tenant_id == tenant_id,
            )
        )
    ).scalar_one_or_none()

    if not row:
        raise UnauthorizedException("Invalid or expired sign-in link")
    if row.used_at is not None:
        raise UnauthorizedException("This sign-in link has already been used")
    expires = row.expires_at
    if expires.tzinfo is None:
        expires = expires.replace(tzinfo=timezone.utc)
    if expires <= datetime.now(timezone.utc):
        raise UnauthorizedException("This sign-in link has expired")

    row.used_at = datetime.now(timezone.utc)
    row.used_from_ip = ip
    await db.commit()

    access_token = create_access_token(
        subject=row.customer_id,
        tenant_id=tenant_id,
        role="customer",
    )
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "customer_id": str(row.customer_id),
    }
