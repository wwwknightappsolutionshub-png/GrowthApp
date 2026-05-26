import uuid
from datetime import datetime, timedelta, timezone
from urllib.parse import quote

from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    BadRequestException,
    ConflictException,
    NotFoundException,
    UnauthorizedException,
)
from app.core.security import (
    create_2fa_pending_token,
    create_access_token,
    create_refresh_token,
    create_short_lived_token,
    decode_2fa_pending_token,
    decode_short_lived_token,
    generate_backup_codes,
    generate_totp_secret,
    get_totp_provisioning_uri,
    hash_backup_code,
    hash_password,
    hash_token,
    needs_rehash,
    verify_backup_code,
    verify_password,
    verify_totp_code,
)
from app.core.audit import log_action
from app.modules.auth.models import RefreshToken, User
from app.modules.auth.schemas import (
    LoginRequest,
    RegisterRequest,
    TwoFADisableRequest,
    TwoFAEnableRequest,
)
from app.core.config import settings


# ── Registration ───────────────────────────────────────────────────────────

async def register(db: AsyncSession, data: RegisterRequest) -> tuple[User, dict]:
    """Create user (+ tenant for tenant signups). Returns (user, tokens_dict)
    where tokens_dict has access_token, refresh_token, expires_in (mirrors
    `_issue_tokens`)."""
    existing = (await db.execute(select(User).where(User.email == data.email.lower()))).scalar_one_or_none()
    if existing:
        raise ConflictException("An account with this email already exists")

    user = User(
        id=uuid.uuid4(),
        email=data.email.lower(),
        password_hash=hash_password(data.password),
        full_name=data.full_name,
        phone=data.phone,
        user_type=data.user_type,
        estimated_client_count=data.estimated_client_count if data.user_type == "freelancer" else None,
        membership_rewards_opt_in=data.enable_membership_rewards,
        totp_backup_codes=[],
    )
    db.add(user)
    await db.flush()

    if data.user_type == "freelancer":
        from app.modules.billing.freelancer_pricing import calculate_freelancer_price
        from app.modules.billing.models import FreelancerBilling

        price = calculate_freelancer_price(int(data.estimated_client_count))
        billing = FreelancerBilling(
            id=uuid.uuid4(),
            user_id=user.id,
            estimated_client_count=int(data.estimated_client_count),
            calculated_price=price,
            calculation_source="auto",
        )
        db.add(billing)

        await log_action(
            db,
            action="user.registered",
            resource="user",
            resource_id=user.id,
            user_id=user.id,
            metadata={
                "email": user.email,
                "user_type": "freelancer",
                "estimated_client_count": data.estimated_client_count,
                "calculated_price": str(price),
                "calculation_source": "auto",
            },
        )
        await db.commit()
        await db.refresh(user)
        tokens = await _issue_tokens(db, user)
        return user, tokens

    # ── Tenant signup (default, behaviour unchanged) ───────────────────────
    from app.modules.tenants.models import Tenant, TenantMember
    from app.modules.tenants.service import unique_tenant_slug

    slug = await unique_tenant_slug(db, data.business_name or data.email.split("@")[0])
    tenant = Tenant(
        id=uuid.uuid4(),
        slug=slug,
        name=data.business_name,
        business_type=data.business_type,
        postcode=data.postcode.upper(),
    )
    db.add(tenant)
    await db.flush()

    member = TenantMember(
        id=uuid.uuid4(),
        tenant_id=tenant.id,
        user_id=user.id,
        role="owner",
        joined_at=datetime.now(timezone.utc),
    )
    db.add(member)
    await log_action(
        db,
        action="user.registered",
        resource="user",
        resource_id=user.id,
        user_id=user.id,
        tenant_id=tenant.id,
        metadata={"email": user.email, "business_name": data.business_name},
    )
    await db.commit()
    await db.refresh(user)

    try:
        from app.modules.membership_rewards.hooks import on_tenant_signup

        if user.membership_rewards_opt_in:
            await on_tenant_signup(db, tenant.id)
    except Exception:  # noqa: BLE001
        import logging

        logging.getLogger(__name__).exception(
            "Membership & Rewards trial start failed for tenant %s", tenant.id
        )

    # Welcome email — best-effort (don't block registration on send failures)
    try:
        import os
        from app.adapters.email import get_email_adapter
        from app.adapters.email.base import EmailMessage
        from app.templates.renderer import render_welcome
        frontend_url = os.getenv("FRONTEND_URL", "https://app.customerflow.ai")
        trial_ends = (datetime.now(timezone.utc) + timedelta(days=14)).strftime("%d %B %Y")
        adapter = get_email_adapter()
        await adapter.send(EmailMessage(
            to=user.email,
            to_name=user.full_name,
            subject=f"Welcome to CustomerFlow AI — {data.business_name}",
            html_body=render_welcome(
                full_name=user.full_name,
                email=user.email,
                business_name=data.business_name,
                dashboard_url=f"{frontend_url}/dashboard",
                trial_ends=trial_ends,
            ),
        ))
    except Exception:  # noqa: BLE001 — best-effort welcome
        pass

    tokens = await _issue_tokens(db, user)
    return user, tokens


# ── Login ──────────────────────────────────────────────────────────────────

async def login(db: AsyncSession, data: LoginRequest) -> dict:
    """
    Returns:
      - Normal:  {'access_token': ..., 'requires_2fa': False}
      - 2FA req: {'requires_2fa': True, 'temp_token': ...}
    """
    user = (await db.execute(select(User).where(User.email == data.email.lower()))).scalar_one_or_none()
    if not user or not verify_password(data.password, user.password_hash):
        if user:
            await log_action(
                db,
                action="user.login_failed",
                resource="user",
                resource_id=user.id,
                user_id=user.id,
                metadata={"reason": "bad_password"},
            )
            await db.commit()
        raise UnauthorizedException("Invalid email or password")

    if user.deleted_at:
        await log_action(
            db,
            action="user.login_failed",
            resource="user",
            resource_id=user.id,
            user_id=user.id,
            metadata={"reason": "deactivated"},
        )
        await db.commit()
        raise UnauthorizedException("Account has been deactivated")

    if needs_rehash(user.password_hash):
        user.password_hash = hash_password(data.password)
        db.add(user)
        await db.commit()

    if user.totp_enabled:
        temp_token = create_2fa_pending_token(str(user.id))
        await log_action(
            db,
            action="user.login_2fa_required",
            resource="user",
            resource_id=user.id,
            user_id=user.id,
        )
        await db.commit()
        return {"requires_2fa": True, "temp_token": temp_token}

    await log_action(
        db,
        action="user.login_succeeded",
        resource="user",
        resource_id=user.id,
        user_id=user.id,
    )
    return await _issue_tokens(db, user)


async def _issue_tokens(db: AsyncSession, user: User) -> dict:
    """Find the user's primary active tenant and issue access + refresh tokens.

    Freelancers can own multiple managed-client tenants. Some clients may be
    soft-deactivated, so token tenant context must never point at an inactive
    tenant or every tenant-scoped module will 403 after login.
    """
    from app.modules.tenants.service import resolve_primary_tenant_membership_for_login

    pair = await resolve_primary_tenant_membership_for_login(
        db,
        user.id,
        prefer_freelancer_clients=user.user_type == "freelancer",
    )
    if pair:
        member, tenant = pair
        tenant_id = member.tenant_id
        role = member.role
        if user.user_type == "tenant" and not tenant.is_active:
            # Still issue tokens — dashboard can show suspension; matches admin suspend UX.
            pass
    else:
        tenant_id = None
        role = None
        if user.user_type == "tenant" and not user.is_superadmin:
            raise UnauthorizedException(
                "No business workspace is linked to this account. "
                "If you recently registered, try completing signup again or contact support."
            )

    access_token = create_access_token(subject=user.id, tenant_id=tenant_id, role=role)
    raw_refresh, hashed_refresh = create_refresh_token()

    expires_at = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    rt = RefreshToken(
        id=uuid.uuid4(),
        user_id=user.id,
        token_hash=hashed_refresh,
        expires_at=expires_at,
    )
    db.add(rt)
    await db.commit()

    return {
        "access_token": access_token,
        "refresh_token": raw_refresh,
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "requires_2fa": False,
    }


# ── 2FA verify (called after password + temp_token) ────────────────────────

async def verify_2fa_and_login(db: AsyncSession, temp_token: str, code: str) -> dict:
    """Validate temp_token, verify TOTP or backup code, issue full tokens."""
    try:
        user_id = decode_2fa_pending_token(temp_token)
    except JWTError:
        raise UnauthorizedException("Invalid or expired verification token")

    user = (await db.execute(select(User).where(User.id == uuid.UUID(user_id)))).scalar_one_or_none()
    if not user or not user.totp_enabled:
        raise UnauthorizedException("2FA not configured")

    # Try TOTP first (6 digits)
    clean_code = code.strip()
    if len(clean_code) == 6 and clean_code.isdigit():
        if not verify_totp_code(user.totp_secret, clean_code):
            raise UnauthorizedException("Invalid authenticator code")
    else:
        # Try backup code
        matched_index = None
        for i, hashed in enumerate(user.totp_backup_codes):
            if verify_backup_code(clean_code, hashed):
                matched_index = i
                break
        if matched_index is None:
            raise UnauthorizedException("Invalid code or backup code")
        # Consume backup code (remove from list)
        new_codes = [c for j, c in enumerate(user.totp_backup_codes) if j != matched_index]
        user.totp_backup_codes = new_codes
        db.add(user)

    return await _issue_tokens(db, user)


# ── 2FA setup ──────────────────────────────────────────────────────────────

async def setup_2fa(db: AsyncSession, user: User) -> dict:
    """
    Generate a new TOTP secret and store it (not yet enabled).
    Returns secret + QR URI — user must call enable_2fa() to activate.
    """
    secret = generate_totp_secret()
    uri = get_totp_provisioning_uri(secret, user.email)
    qr_image = f"https://api.qrserver.com/v1/create-qr-code/?size=200x200&data={quote(uri)}"

    # Store secret (overwrite pending secret if any); enabled stays False
    user.totp_secret = secret
    db.add(user)
    await db.commit()

    return {"secret": secret, "qr_code_url": uri, "qr_code_image_url": qr_image}


async def enable_2fa(db: AsyncSession, user: User, data: TwoFAEnableRequest) -> dict:
    """
    Verify the TOTP code from the user's app and flip totp_enabled=True.
    Returns 8 backup codes (shown once, then stored hashed).
    """
    if not user.totp_secret:
        raise BadRequestException("Call /auth/2fa/setup first to generate a secret")

    if not verify_totp_code(user.totp_secret, data.code):
        raise BadRequestException("Invalid authenticator code — please try again")

    plain_codes = generate_backup_codes(8)
    hashed_codes = [hash_backup_code(c) for c in plain_codes]

    user.totp_enabled = True
    user.totp_backup_codes = hashed_codes
    db.add(user)
    await log_action(
        db,
        action="user.2fa_enabled",
        resource="user",
        resource_id=user.id,
        user_id=user.id,
    )
    await db.commit()

    return {"message": "2FA enabled successfully", "backup_codes": plain_codes}


async def disable_2fa(db: AsyncSession, user: User, data: TwoFADisableRequest) -> None:
    """Require both password AND TOTP code to disable 2FA."""
    if not verify_password(data.password, user.password_hash):
        raise UnauthorizedException("Incorrect password")

    if not user.totp_enabled:
        raise BadRequestException("2FA is not currently enabled")

    if not verify_totp_code(user.totp_secret, data.code):
        raise UnauthorizedException("Invalid authenticator code")

    user.totp_enabled = False
    user.totp_secret = None
    user.totp_backup_codes = []
    db.add(user)
    await log_action(
        db,
        action="user.2fa_disabled",
        resource="user",
        resource_id=user.id,
        user_id=user.id,
    )
    await db.commit()


# ── Refresh ────────────────────────────────────────────────────────────────

async def refresh_access_token(db: AsyncSession, raw_token: str) -> dict:
    token_hash = hash_token(raw_token)
    rt = (
        await db.execute(
            select(RefreshToken).where(
                RefreshToken.token_hash == token_hash,
                RefreshToken.revoked_at.is_(None),
                RefreshToken.expires_at > datetime.now(timezone.utc),
            )
        )
    ).scalar_one_or_none()

    if not rt:
        raise UnauthorizedException("Invalid or expired refresh token")

    user = (await db.execute(select(User).where(User.id == rt.user_id))).scalar_one_or_none()
    if not user:
        raise UnauthorizedException("User not found")

    # Revoke old refresh token (rotation)
    rt.revoked_at = datetime.now(timezone.utc)
    db.add(rt)

    return await _issue_tokens(db, user)


async def logout(db: AsyncSession, raw_token: str) -> None:
    token_hash = hash_token(raw_token)
    rt = (await db.execute(select(RefreshToken).where(RefreshToken.token_hash == token_hash))).scalar_one_or_none()
    if rt:
        rt.revoked_at = datetime.now(timezone.utc)
        db.add(rt)
        await log_action(
            db,
            action="user.logout",
            resource="user",
            resource_id=rt.user_id,
            user_id=rt.user_id,
        )
        await db.commit()


# ── Password reset ─────────────────────────────────────────────────────────

async def forgot_password(db: AsyncSession, email: str) -> None:
    user = (await db.execute(select(User).where(User.email == email.lower()))).scalar_one_or_none()
    if not user:
        return  # Silent — don't leak user existence

    await log_action(
        db,
        action="user.password_reset_requested",
        resource="user",
        resource_id=user.id,
        user_id=user.id,
    )
    await db.commit()

    reset_token = create_short_lived_token("password_reset", str(user.id), expire_hours=2)

    frontend_url = settings.FRONTEND_URL.rstrip("/")
    reset_url = f"{frontend_url}/reset-password?token={reset_token}"

    from app.adapters.email import get_email_adapter
    from app.adapters.email.base import EmailMessage
    from app.templates.renderer import render_password_reset
    adapter = get_email_adapter()
    await adapter.send(EmailMessage(
        to=user.email,
        to_name=user.full_name,
        subject="Reset your CustomerFlow AI password",
        html_body=render_password_reset(
            full_name=user.full_name,
            email=user.email,
            reset_url=reset_url,
            expires_in_minutes=120,
        ),
    ))


async def reset_password(db: AsyncSession, token: str, new_password: str) -> None:
    try:
        user_id = decode_short_lived_token(token, "password_reset")
    except JWTError:
        raise BadRequestException("Invalid or expired reset link")

    user = (await db.execute(select(User).where(User.id == uuid.UUID(user_id)))).scalar_one_or_none()
    if not user:
        raise NotFoundException("User")

    user.password_hash = hash_password(new_password)
    db.add(user)

    from sqlalchemy import update
    await db.execute(
        update(RefreshToken)
        .where(RefreshToken.user_id == user.id, RefreshToken.revoked_at.is_(None))
        .values(revoked_at=datetime.now(timezone.utc))
    )
    await log_action(
        db,
        action="user.password_reset",
        resource="user",
        resource_id=user.id,
        user_id=user.id,
    )
    await db.commit()
