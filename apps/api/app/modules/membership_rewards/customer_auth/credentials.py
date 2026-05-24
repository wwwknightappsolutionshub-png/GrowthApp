"""Customer portal credential storage and password login."""

from __future__ import annotations

import secrets
import string
import uuid
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import UnauthorizedException
from app.core.security import create_access_token, hash_password, verify_password
from app.modules.membership_rewards.models import MrCustomerCredentials


def generate_temp_password(length: int = 12) -> str:
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


async def get_credentials(
    db: AsyncSession, tenant_id: uuid.UUID, customer_id: uuid.UUID
) -> MrCustomerCredentials | None:
    return await db.get(MrCustomerCredentials, {"tenant_id": tenant_id, "customer_id": customer_id})


async def ensure_credentials(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    customer_id: uuid.UUID,
    *,
    temp_password: str | None = None,
) -> tuple[MrCustomerCredentials, str | None]:
    """Create credentials if missing. Returns (row, plain_temp_password_if_new)."""
    row = await get_credentials(db, tenant_id, customer_id)
    issued: str | None = None
    if not row:
        plain = temp_password or generate_temp_password()
        row = MrCustomerCredentials(
            tenant_id=tenant_id,
            customer_id=customer_id,
            password_hash=hash_password(plain),
            must_change_password=True,
        )
        db.add(row)
        await db.flush()
        issued = plain
    return row, issued


async def set_password(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    customer_id: uuid.UUID,
    new_password: str,
    *,
    must_change: bool = False,
) -> None:
    row, _ = await ensure_credentials(db, tenant_id, customer_id)
    row.password_hash = hash_password(new_password)
    row.must_change_password = must_change
    await db.commit()


async def authenticate_customer(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    customer_id: uuid.UUID,
    password: str,
) -> dict:
    row = await get_credentials(db, tenant_id, customer_id)
    if not row or not row.password_hash or not verify_password(password, row.password_hash):
        raise UnauthorizedException("Invalid email or password")

    row.last_login_at = datetime.now(timezone.utc)
    await db.commit()

    access_token = create_access_token(
        subject=customer_id,
        tenant_id=tenant_id,
        role="customer",
    )
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "customer_id": str(customer_id),
        "must_change_password": row.must_change_password,
    }
