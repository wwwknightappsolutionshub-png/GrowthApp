import hashlib
import secrets
import string
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID

import pyotp
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, InvalidHashError
from jose import JWTError, jwt

from app.core.config import settings

ph = PasswordHasher(
    time_cost=2,
    memory_cost=65536,
    parallelism=2,
    hash_len=32,
    salt_len=16,
)

# A lighter hasher for backup codes (don't need full argon2 security here,
# but we still use argon2 for consistency)
_backup_ph = PasswordHasher(time_cost=1, memory_cost=16384, parallelism=1)


# ── Password helpers ───────────────────────────────────────────────────────

def hash_password(plain_password: str) -> str:
    return ph.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return ph.verify(hashed_password, plain_password)
    except (VerifyMismatchError, InvalidHashError):
        return False


def needs_rehash(hashed_password: str) -> bool:
    return ph.check_needs_rehash(hashed_password)


# ── JWT helpers ────────────────────────────────────────────────────────────

def create_access_token(
    subject: str | UUID,
    tenant_id: str | UUID | None = None,
    role: str | None = None,
    expires_delta: timedelta | None = None,
) -> str:
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    payload: dict[str, Any] = {
        "sub": str(subject),
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "access",
    }
    if tenant_id:
        payload["tid"] = str(tenant_id)
    if role:
        payload["role"] = role
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token() -> tuple[str, str]:
    """Returns (raw_token, hashed_token). Store hash in DB, send raw to client."""
    raw = secrets.token_urlsafe(64)
    hashed = hashlib.sha256(raw.encode()).hexdigest()
    return raw, hashed


def hash_token(raw_token: str) -> str:
    return hashlib.sha256(raw_token.encode()).hexdigest()


def decode_access_token(token: str) -> dict[str, Any]:
    """Raises JWTError on invalid/expired token."""
    return jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])


def create_short_lived_token(purpose: str, subject: str, expire_hours: int = 24) -> str:
    """For email verification, password reset, etc."""
    expire = datetime.now(timezone.utc) + timedelta(hours=expire_hours)
    payload = {
        "sub": subject,
        "purpose": purpose,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def decode_short_lived_token(token: str, expected_purpose: str) -> str:
    """Returns the subject (e.g. user_id or email) or raises JWTError."""
    payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
    if payload.get("purpose") != expected_purpose:
        raise JWTError("Invalid token purpose")
    return payload["sub"]


# ── 2FA / TOTP helpers ─────────────────────────────────────────────────────

def generate_totp_secret() -> str:
    """Generate a new base32 TOTP secret."""
    return pyotp.random_base32()


def get_totp_provisioning_uri(secret: str, email: str, issuer: str = "CustomerFlow AI") -> str:
    """Return the otpauth:// URI for QR code generation."""
    totp = pyotp.TOTP(secret)
    return totp.provisioning_uri(name=email, issuer_name=issuer)


def verify_totp_code(secret: str, code: str) -> bool:
    """Verify a 6-digit TOTP code. Allows ±1 step (±30s) drift."""
    if not secret or not code:
        return False
    totp = pyotp.TOTP(secret)
    return totp.verify(code, valid_window=1)


def generate_backup_codes(count: int = 8) -> list[str]:
    """
    Generate `count` one-time backup codes in format XXXX-XXXX-XXXX.
    Returns plain-text codes (show once to user, then store hashed).
    """
    alphabet = string.ascii_uppercase + string.digits
    codes = []
    for _ in range(count):
        parts = [
            "".join(secrets.choice(alphabet) for _ in range(4))
            for _ in range(3)
        ]
        codes.append("-".join(parts))
    return codes


def hash_backup_code(plain_code: str) -> str:
    """Hash a backup code for safe storage."""
    return _backup_ph.hash(plain_code.upper().replace("-", "").strip())


def verify_backup_code(plain_code: str, hashed: str) -> bool:
    """Verify a backup code against its hash."""
    try:
        normalised = plain_code.upper().replace("-", "").strip()
        return _backup_ph.verify(hashed, normalised)
    except (VerifyMismatchError, InvalidHashError):
        return False


def create_2fa_pending_token(user_id: str) -> str:
    """
    Short-lived JWT (5 min) issued after password check passes,
    when TOTP code is still required. Purpose: '2fa_pending'.
    """
    expire = datetime.now(timezone.utc) + timedelta(minutes=5)
    payload = {
        "sub": user_id,
        "purpose": "2fa_pending",
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def decode_2fa_pending_token(token: str) -> str:
    """Returns user_id or raises JWTError."""
    payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
    if payload.get("purpose") != "2fa_pending":
        raise JWTError("Invalid token purpose")
    return payload["sub"]
