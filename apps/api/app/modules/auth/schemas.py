from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(min_length=1, max_length=255)
    phone: str | None = None
    # Defaults to "tenant" so existing tenant signups remain unchanged.
    user_type: Literal["tenant", "freelancer"] = "tenant"
    # Tenant info (created alongside user) — required when user_type == "tenant".
    business_name: str | None = Field(default=None, max_length=255)
    business_type: str | None = Field(default=None, max_length=100)
    postcode: str | None = Field(default=None, max_length=10)
    # Freelancer info — required when user_type == "freelancer".
    estimated_client_count: int | None = Field(default=None, ge=0)
    enable_membership_rewards: bool = True

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v

    @model_validator(mode="after")
    def _validate_user_type_fields(self) -> "RegisterRequest":
        if self.user_type == "tenant":
            missing: list[str] = []
            if not self.business_name or not self.business_name.strip():
                missing.append("business_name")
            if not self.business_type or not self.business_type.strip():
                missing.append("business_type")
            if not self.postcode or not self.postcode.strip():
                missing.append("postcode")
            if missing:
                raise ValueError(f"Required for tenant signup: {', '.join(missing)}")
        elif self.user_type == "freelancer":
            if self.estimated_client_count is None:
                raise ValueError("estimated_client_count is required for freelancer signup")
        return self


# ── Pre-registration OTP signup flow ───────────────────────────────────────


class SignupInitiateRequest(RegisterRequest):
    """Same payload as RegisterRequest; used to start email OTP signup."""


class SignupInitiateResponse(BaseModel):
    pending_id: UUID
    email: str
    expires_in_seconds: int


class SignupVerifyRequest(BaseModel):
    pending_id: UUID
    email_code: str = Field(min_length=6, max_length=6, pattern=r"^\d{6}$")


class ResendOtpRequest(BaseModel):
    pending_id: UUID
    channel: Literal["email"] = "email"


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class LoginResponse(BaseModel):
    """Returned from POST /auth/login.
    If requires_2fa=True, temp_token must be submitted to /auth/2fa/verify.
    """
    access_token: str | None = None
    token_type: str = "bearer"
    expires_in: int | None = None
    requires_2fa: bool = False
    temp_token: str | None = None


class RefreshRequest(BaseModel):
    refresh_token: str | None = None


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(min_length=8, max_length=128)

    @field_validator("new_password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v


class UserResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: UUID
    email: str
    full_name: str
    phone: str | None
    avatar_url: str | None
    email_verified_at: datetime | None
    phone_verified_at: datetime | None = None
    totp_enabled: bool
    is_superadmin: bool = False
    user_type: str = "tenant"
    estimated_client_count: int | None = None
    onboarding_completed: bool = False
    created_at: datetime


class MessageResponse(BaseModel):
    message: str


# ── 2FA schemas ────────────────────────────────────────────────────────────

class TwoFASetupResponse(BaseModel):
    """Returned from POST /auth/2fa/setup. Show QR to user; do NOT enable yet."""
    secret: str
    qr_code_url: str          # otpauth:// URI — pass to a QR library on frontend
    qr_code_image_url: str    # Convenience: Google Charts QR URL ready to <img>


class TwoFAEnableRequest(BaseModel):
    """User submits TOTP code to confirm they scanned the QR correctly."""
    code: str = Field(min_length=6, max_length=6, pattern=r"^\d{6}$")


class TwoFAEnableResponse(BaseModel):
    message: str
    backup_codes: list[str]   # Show ONCE — never returned again


class TwoFADisableRequest(BaseModel):
    password: str
    code: str = Field(min_length=6, max_length=6, pattern=r"^\d{6}$")


class TwoFAVerifyRequest(BaseModel):
    """Used during login when requires_2fa=True."""
    temp_token: str
    code: str = Field(min_length=6, max_length=20)  # 6-digit TOTP or backup code (XXXX-XXXX-XXXX)
