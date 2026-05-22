from typing import Annotated
from uuid import UUID

from fastapi import Cookie, Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db, set_rls_context
from app.core.exceptions import UnauthorizedException, ForbiddenException, QuotaExceededException
from app.core.security import decode_access_token
from app.modules.auth.models import User
from app.modules.tenants.models import Tenant, TenantMember
from app.modules.billing.models import Subscription, SubscriptionPlan

bearer_scheme = HTTPBearer(auto_error=False)
_ACCESS_COOKIE = "access_token"


def _resolve_token(
    credentials: HTTPAuthorizationCredentials | None,
    cookie_token: str | None,
) -> str | None:
    """Prefer Authorization header, fall back to httpOnly access cookie."""
    if credentials and credentials.credentials:
        return credentials.credentials
    return cookie_token or None


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    db: AsyncSession = Depends(get_db),
    cookie_token: str | None = Cookie(default=None, alias=_ACCESS_COOKIE),
) -> User:
    """Extract and validate the caller's credentials.

    Accepts:
      * JWT access token via ``Authorization: Bearer <jwt>`` or the access_token cookie
      * Programmatic API key via ``Authorization: Bearer cf_live_...`` (header only)
    """
    token = _resolve_token(credentials, cookie_token)
    if not token:
        raise UnauthorizedException("Missing authentication token")

    # API-key path
    if token.startswith("cf_"):
        from app.modules.api_keys.service import resolve_api_key

        api_key = await resolve_api_key(db, token)
        if not api_key.user_id:
            raise UnauthorizedException("API key has no associated user")
        user = (
            await db.execute(
                select(User).where(User.id == api_key.user_id, User.deleted_at.is_(None))
            )
        ).scalar_one_or_none()
        if not user:
            raise UnauthorizedException("User not found")
        return user

    try:
        payload = decode_access_token(token)
        user_id: str = payload.get("sub")
        if not user_id:
            raise UnauthorizedException("Invalid token payload")
        if payload.get("type") not in (None, "access"):
            raise UnauthorizedException("Wrong token type")
    except JWTError:
        raise UnauthorizedException("Invalid or expired token")

    result = await db.execute(
        select(User).where(User.id == UUID(user_id), User.deleted_at.is_(None))
    )
    user = result.scalar_one_or_none()
    if not user:
        raise UnauthorizedException("User not found")

    return user


async def get_current_tenant(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    request: Request,
    db: AsyncSession = Depends(get_db),
    cookie_token: str | None = Cookie(default=None, alias=_ACCESS_COOKIE),
) -> tuple[User, Tenant, str]:
    """
    Returns (user, tenant, role). Sets RLS context on the session.
    Raises 401/403 if not authenticated or not a member.

    Accepts either a JWT or an API key (``cf_*``) in the same Authorization
    header / cookie slot.
    """
    token = _resolve_token(credentials, cookie_token)
    if not token:
        raise UnauthorizedException("Missing authentication token")

    user_id: str | None
    tenant_id: str | None

    if token.startswith("cf_"):
        from app.modules.api_keys.service import resolve_api_key

        api_key = await resolve_api_key(db, token)
        user_id = str(api_key.user_id) if api_key.user_id else None
        tenant_id = str(api_key.tenant_id)
        if not user_id or not tenant_id:
            raise UnauthorizedException("API key has no tenant/user binding")
    else:
        try:
            payload = decode_access_token(token)
            user_id = payload.get("sub")
            tenant_id = payload.get("tid")
            if payload.get("type") not in (None, "access"):
                raise UnauthorizedException("Wrong token type")
        except JWTError:
            raise UnauthorizedException("Invalid or expired token")

    if not user_id:
        raise UnauthorizedException("Token missing tenant context")

    # Fetch user
    user_result = await db.execute(
        select(User).where(User.id == UUID(user_id), User.deleted_at.is_(None))
    )
    user = user_result.scalar_one_or_none()
    if not user:
        raise UnauthorizedException("User not found")

    if user.user_type == "freelancer":
        active_client_id = request.headers.get("x-freelancer-client-id")
        if active_client_id:
            try:
                tenant_id = str(UUID(active_client_id))
            except ValueError:
                raise ForbiddenException("Invalid freelancer client context")

    # Backfill tenant id for access tokens issued without ``tid`` (legacy refresh).
    if not tenant_id:
        from app.modules.tenants.service import resolve_primary_tenant_membership

        pair = await resolve_primary_tenant_membership(
            db,
            user.id,
            prefer_freelancer_clients=user.user_type == "freelancer",
        )
        if pair:
            tenant_id = str(pair[1].id)

    if not tenant_id:
        raise UnauthorizedException("Token missing tenant context")

    # Fetch tenant membership
    member_result = await db.execute(
        select(TenantMember, Tenant)
        .join(Tenant, TenantMember.tenant_id == Tenant.id)
        .where(
            TenantMember.user_id == UUID(user_id),
            TenantMember.tenant_id == UUID(tenant_id),
            Tenant.is_active == True,  # noqa: E712
        )
    )
    row = member_result.first()
    if not row:
        if user.is_superadmin:
            tenant = (
                await db.execute(
                    select(Tenant).where(
                        Tenant.id == UUID(tenant_id),
                        Tenant.is_active == True,  # noqa: E712
                    )
                )
            ).scalar_one_or_none()
            if tenant:
                await set_rls_context(db, tenant.id)
                return user, tenant, "owner"
        raise ForbiddenException("Not a member of this tenant")

    member, tenant = row

    # Set RLS context
    await set_rls_context(db, tenant.id)

    return user, tenant, member.role


# Type aliases for cleaner endpoint signatures
CurrentUser = Annotated[User, Depends(get_current_user)]
CurrentTenantContext = Annotated[tuple[User, Tenant, str], Depends(get_current_tenant)]


def require_owner(ctx: CurrentTenantContext) -> tuple[User, Tenant, str]:
    """Raise 403 if the current user is not the tenant owner."""
    user, tenant, role = ctx
    if role != "owner":
        raise ForbiddenException("Owner access required")
    return ctx


OwnerContext = Annotated[tuple[User, Tenant, str], Depends(require_owner)]


async def require_superadmin(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Raise 403 unless the current user has `is_superadmin=True`.

    Super-admins bypass RLS for platform queries — we explicitly clear the
    `app.current_tenant` GUC so SELECTs see every tenant's rows.
    """
    if not current_user.is_superadmin:
        raise ForbiddenException("Super-admin access required")
    await set_rls_context(db, None)
    return current_user


SuperAdmin = Annotated[User, Depends(require_superadmin)]


def require_permission(*perms: str):
    """Return a FastAPI dependency that 403s unless the user holds ALL of `perms`.

    Usage:

        @router.get("/foo", dependencies=[Depends(require_permission("crm.read"))])
        async def list_foo(...): ...

    Owners and super-admins always pass. For all other roles we consult the
    RBAC template (+ tenant overrides).
    """
    async def _checker(
        ctx: "CurrentTenantContext",
        db: AsyncSession = Depends(get_db),
    ) -> None:
        user, tenant, role = ctx
        if user.is_superadmin or role == "owner":
            return
        from app.modules.rbac.service import get_permissions_for_role

        granted = await get_permissions_for_role(db, tenant.id, role)
        missing = [p for p in perms if p not in granted]
        if missing:
            raise ForbiddenException(f"Missing permission(s): {', '.join(missing)}")

    return _checker


async def check_quota(
    resource: str,
    tenant: Tenant,
    db: AsyncSession,
    increment: int = 1,
) -> None:
    """
    Check if tenant has quota for the given resource.
    Raises QuotaExceededException if limit is reached.
    """
    # Get subscription and plan
    sub_result = await db.execute(
        select(Subscription, SubscriptionPlan)
        .join(SubscriptionPlan, Subscription.plan_id == SubscriptionPlan.id)
        .where(Subscription.tenant_id == tenant.id)
    )
    row = sub_result.first()

    if not row:
        # No subscription — allow with default limits (trial)
        return

    subscription, plan = row

    # Check subscription is active
    if subscription.status not in ("active", "trialing"):
        raise QuotaExceededException(resource)

    # Resource-specific quota checks (to be expanded)
    if resource == "locations":
        from app.modules.tenants.models import Location
        count_result = await db.execute(
            select(Location).where(Location.tenant_id == tenant.id)
        )
        count = len(count_result.scalars().all())
        if count >= plan.max_locations:
            raise QuotaExceededException("locations")

    elif resource == "users":
        count_result = await db.execute(
            select(TenantMember).where(TenantMember.tenant_id == tenant.id)
        )
        count = len(count_result.scalars().all())
        if count >= plan.max_users:
            raise QuotaExceededException("users")

    elif resource == "social_posting":
        if not plan.has_social_posting:
            raise QuotaExceededException("social_posting")

    elif resource == "ai_content":
        if not plan.has_ai_content:
            raise QuotaExceededException("ai_content")
