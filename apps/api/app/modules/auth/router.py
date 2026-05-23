from fastapi import APIRouter, Cookie, Depends, Query, Request, Response
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.middleware import limiter
from app.modules.auth import magic_link as ml_service
from app.modules.auth import service
from app.modules.auth import signup_otp_service
from app.modules.auth.schemas import (
    ForgotPasswordRequest,
    LoginRequest,
    LoginResponse,
    MessageResponse,
    RefreshRequest,
    RegisterRequest,
    ResendOtpRequest,
    ResetPasswordRequest,
    SignupInitiateRequest,
    SignupInitiateResponse,
    SignupVerifyRequest,
    TokenResponse,
    TwoFADisableRequest,
    TwoFAEnableRequest,
    TwoFAEnableResponse,
    TwoFASetupResponse,
    TwoFAVerifyRequest,
    UserResponse,
)
from app.modules.auth.models import User

router = APIRouter(prefix="/auth", tags=["Auth"])

_ACCESS_COOKIE = "access_token"
_REFRESH_COOKIE = "refresh_token"


def _cookie_kwargs(path: str) -> dict:
    """Shared cookie attributes derived from settings."""
    kwargs = dict(
        httponly=True,
        samesite=settings.COOKIE_SAMESITE,
        secure=settings.COOKIE_SECURE,
        path=path,
    )
    if settings.COOKIE_DOMAIN:
        kwargs["domain"] = settings.COOKIE_DOMAIN
    return kwargs


def _set_auth_cookies(response: Response, access_token: str, refresh_token: str | None = None) -> None:
    """Write access (and optionally refresh) tokens as httpOnly cookies."""
    response.set_cookie(
        key=_ACCESS_COOKIE,
        value=access_token,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        **_cookie_kwargs(path="/"),
    )
    if refresh_token is not None:
        response.set_cookie(
            key=_REFRESH_COOKIE,
            value=refresh_token,
            max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 3600,
            **_cookie_kwargs(path="/api/v1/auth"),
        )


def _clear_auth_cookies(response: Response) -> None:
    response.delete_cookie(key=_ACCESS_COOKIE, path="/", domain=settings.COOKIE_DOMAIN or None)
    response.delete_cookie(key=_REFRESH_COOKIE, path="/api/v1/auth", domain=settings.COOKIE_DOMAIN or None)


# Backwards-compatible alias for any old callers.
def _set_refresh_cookie(response: Response, raw_token: str) -> None:
    response.set_cookie(
        key=_REFRESH_COOKIE,
        value=raw_token,
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 3600,
        **_cookie_kwargs(path="/api/v1/auth"),
    )


def _clear_refresh_cookie(response: Response) -> None:
    response.delete_cookie(key=_REFRESH_COOKIE, path="/api/v1/auth", domain=settings.COOKIE_DOMAIN or None)


@router.post("/register", response_model=TokenResponse, status_code=201)
@limiter.limit("5/minute;20/hour")
async def register(
    request: Request,
    data: RegisterRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    """Legacy direct registration (no OTP). Retained for compatibility."""
    user, tokens = await service.register(db, data)
    _set_auth_cookies(response, tokens["access_token"], tokens["refresh_token"])
    return TokenResponse(access_token=tokens["access_token"], expires_in=tokens["expires_in"])


@router.post("/signup/initiate", response_model=SignupInitiateResponse, status_code=201)
@limiter.limit("5/minute;20/hour")
async def signup_initiate(
    request: Request,
    data: SignupInitiateRequest,
    db: AsyncSession = Depends(get_db),
):
    """Step 1 of OTP signup — validate form and send email OTP."""
    result = await signup_otp_service.initiate(db, data)
    return SignupInitiateResponse(**result)


@router.post("/signup/verify", response_model=TokenResponse, status_code=201)
@limiter.limit("10/minute;40/hour")
async def signup_verify(
    request: Request,
    data: SignupVerifyRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    """Step 2 of OTP signup — validate email code, create account, issue tokens."""
    user, tokens = await signup_otp_service.verify_and_complete(db, data)
    _set_auth_cookies(response, tokens["access_token"], tokens["refresh_token"])
    return TokenResponse(access_token=tokens["access_token"], expires_in=tokens["expires_in"])


@router.post("/signup/resend-code", response_model=MessageResponse)
@limiter.limit("3/minute;10/hour")
async def signup_resend(
    request: Request,
    data: ResendOtpRequest,
    db: AsyncSession = Depends(get_db),
):
    out = await signup_otp_service.resend_code(db, pending_id=data.pending_id, channel=data.channel)
    return MessageResponse(message=f"Code re-sent via {out['channel']}.")


@router.post("/login", response_model=LoginResponse)
@limiter.limit("10/minute;60/hour")
async def login(
    request: Request,
    data: LoginRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    result = await service.login(db, data)

    if result.get("requires_2fa"):
        return LoginResponse(requires_2fa=True, temp_token=result["temp_token"])

    _set_auth_cookies(response, result["access_token"], result["refresh_token"])
    return LoginResponse(
        access_token=result["access_token"],
        expires_in=result["expires_in"],
        requires_2fa=False,
    )


@router.post("/refresh", response_model=TokenResponse)
@limiter.limit("30/minute")
async def refresh(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
    body: RefreshRequest = RefreshRequest(),
    cookie_token: str | None = Cookie(default=None, alias=_REFRESH_COOKIE),
):
    raw_token = body.refresh_token or cookie_token
    if not raw_token:
        from app.core.exceptions import UnauthorizedException
        raise UnauthorizedException("No refresh token provided")

    result = await service.refresh_access_token(db, raw_token)
    _set_auth_cookies(response, result["access_token"], result["refresh_token"])
    return TokenResponse(access_token=result["access_token"], expires_in=result["expires_in"])


@router.post("/logout", response_model=MessageResponse)
async def logout(
    response: Response,
    db: AsyncSession = Depends(get_db),
    cookie_token: str | None = Cookie(default=None, alias=_REFRESH_COOKIE),
):
    if cookie_token:
        await service.logout(db, cookie_token)
    _clear_auth_cookies(response)
    return MessageResponse(message="Logged out successfully")


@router.get("/me", response_model=UserResponse)
async def me(current_user: User = Depends(get_current_user)):
    return current_user


@router.post("/onboarding/complete", response_model=UserResponse)
async def complete_onboarding(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Mark the current user as having finished the post-signup onboarding tour."""
    if not current_user.onboarding_completed:
        current_user.onboarding_completed = True
        db.add(current_user)
        await db.commit()
        await db.refresh(current_user)
    return current_user


@router.post("/forgot-password", response_model=MessageResponse)
@limiter.limit("3/minute;10/hour")
async def forgot_password(
    request: Request,
    data: ForgotPasswordRequest,
    db: AsyncSession = Depends(get_db),
):
    await service.forgot_password(db, data.email)
    return MessageResponse(message="If that email exists, a reset link has been sent")


@router.post("/reset-password", response_model=MessageResponse)
@limiter.limit("5/minute;20/hour")
async def reset_password(
    request: Request,
    data: ResetPasswordRequest,
    db: AsyncSession = Depends(get_db),
):
    await service.reset_password(db, data.token, data.new_password)
    return MessageResponse(message="Password updated. Please log in again.")


# ── 2FA endpoints ──────────────────────────────────────────────────────────

@router.post("/2fa/setup", response_model=TwoFASetupResponse)
async def setup_2fa(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Generate a TOTP secret + QR code URL.
    The user scans the QR with their authenticator app.
    2FA is NOT active yet — call /auth/2fa/enable with a code to activate.
    """
    result = await service.setup_2fa(db, current_user)
    return TwoFASetupResponse(**result)


@router.post("/2fa/enable", response_model=TwoFAEnableResponse)
async def enable_2fa(
    data: TwoFAEnableRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Confirm setup by submitting a code from the authenticator app.
    Returns 8 backup codes — show to user ONCE and ask them to save.
    """
    result = await service.enable_2fa(db, current_user, data)
    return TwoFAEnableResponse(**result)


@router.post("/2fa/verify", response_model=LoginResponse)
@limiter.limit("10/minute;30/hour")
async def verify_2fa(
    request: Request,
    data: TwoFAVerifyRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    """
    Complete login when requires_2fa=True.
    Submit the temp_token from login + a 6-digit TOTP code (or backup code).
    """
    result = await service.verify_2fa_and_login(db, data.temp_token, data.code)
    _set_auth_cookies(response, result["access_token"], result["refresh_token"])
    return LoginResponse(
        access_token=result["access_token"],
        expires_in=result["expires_in"],
        requires_2fa=False,
    )


@router.post("/2fa/disable", response_model=MessageResponse)
async def disable_2fa(
    data: TwoFADisableRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Disable 2FA. Requires current password AND a valid TOTP code."""
    await service.disable_2fa(db, current_user, data)
    return MessageResponse(message="Two-factor authentication has been disabled")


# ── Magic-link (passwordless) sign-in ──────────────────────────────────────


class MagicLinkRequest(BaseModel):
    email: EmailStr
    next: str | None = Field(default=None, max_length=500)


class MagicLinkVerifyRequest(BaseModel):
    token: str = Field(min_length=10, max_length=200)


@router.post("/magic-link", response_model=MessageResponse)
@limiter.limit("5/minute;20/hour")
async def request_magic_link(
    request: Request,
    data: MagicLinkRequest,
    db: AsyncSession = Depends(get_db),
):
    """Email a single-use sign-in link.

    Always responds 200 to prevent user-enumeration.
    """
    ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    await ml_service.issue_magic_link(
        db,
        email=data.email,
        next_path=data.next,
        ip=ip,
        user_agent=user_agent,
    )
    return MessageResponse(message="If that email exists, a sign-in link has been sent.")


@router.post("/magic-link/verify", response_model=LoginResponse)
@limiter.limit("10/minute")
async def verify_magic_link(
    request: Request,
    response: Response,
    data: MagicLinkVerifyRequest,
    db: AsyncSession = Depends(get_db),
):
    """Redeem a magic-link token and start a session."""
    ip = request.client.host if request.client else None
    user, tokens = await ml_service.consume_magic_link(db, raw_token=data.token, ip=ip)
    _set_auth_cookies(response, tokens["access_token"], tokens["refresh_token"])
    return LoginResponse(
        access_token=tokens["access_token"],
        expires_in=tokens["expires_in"],
        requires_2fa=False,
    )
