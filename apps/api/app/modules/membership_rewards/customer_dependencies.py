"""FastAPI dependencies for customer loyalty portal JWT auth."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import Cookie, Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db, set_rls_context
from app.core.dependencies import _resolve_token
from app.core.exceptions import ForbiddenException, UnauthorizedException
from app.core.security import decode_access_token
from app.modules.crm.models import Customer
from app.modules.tenants.models import Tenant

bearer_scheme = HTTPBearer(auto_error=False)
_CUSTOMER_COOKIE = "loyalty_access_token"


async def get_current_customer(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    db: AsyncSession = Depends(get_db),
    cookie_token: str | None = Cookie(default=None, alias=_CUSTOMER_COOKIE),
) -> tuple[Customer, Tenant]:
    """Validate a customer-scoped JWT (role=customer)."""
    token = _resolve_token(credentials, cookie_token)
    if not token:
        raise UnauthorizedException("Missing authentication token")

    try:
        payload = decode_access_token(token)
        if payload.get("role") != "customer":
            raise UnauthorizedException("Customer access required")
        if payload.get("type") not in (None, "access"):
            raise UnauthorizedException("Wrong token type")
        customer_id = payload.get("sub")
        tenant_id = payload.get("tid")
        if not customer_id or not tenant_id:
            raise UnauthorizedException("Invalid token payload")
    except JWTError:
        raise UnauthorizedException("Invalid or expired token")

    tenant = (
        await db.execute(select(Tenant).where(Tenant.id == UUID(tenant_id), Tenant.is_active.is_(True)))
    ).scalar_one_or_none()
    if not tenant:
        raise ForbiddenException("Business not found")

    customer = (
        await db.execute(
            select(Customer).where(
                Customer.id == UUID(customer_id),
                Customer.tenant_id == tenant.id,
                Customer.deleted_at.is_(None),
            )
        )
    ).scalar_one_or_none()
    if not customer:
        raise UnauthorizedException("Customer not found")

    await set_rls_context(db, tenant.id)
    return customer, tenant


CurrentCustomerContext = Annotated[tuple[Customer, Tenant], Depends(get_current_customer)]
