"""OTP generation, delivery (email + WhatsApp/SMS) and verification.

Strategy
--------
* Email OTP — always sent via the existing email adapter.
* Phone OTP — heuristic:
    - if the phone number looks like a mobile (UK 07/+447 or +447 prefix or
      generic + sign with a mobile-style length), attempt WhatsApp first.
    - if the WhatsApp adapter fails (or for landlines), fall back to SMS.
* Codes are 6-digit, hashed (sha256) at rest, valid for 10 minutes,
  with up to 5 verification attempts.
"""
from __future__ import annotations

import hashlib
import logging
import re
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Literal

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters import get_email_adapter, get_sms_adapter, get_whatsapp_adapter
from app.adapters.email.base import EmailMessage
from app.adapters.sms.base import SMSMessage
from app.adapters.whatsapp.base import WhatsAppMessage
from app.modules.auth.otp_models import OtpCode

log = logging.getLogger(__name__)

OTP_TTL_MINUTES = 10
OTP_LENGTH = 6
_DIGITS = "0123456789"

# UK mobile numbers and generic international mobiles. Conservative regex —
# anything that doesn't match is treated as a landline (SMS, not WhatsApp).
_MOBILE_RE = re.compile(r"^(?:\+?44\s?7\d{9}|0?7\d{9}|\+\d{8,15})$")


# ── Helpers ────────────────────────────────────────────────────────────────

def _hash_code(code: str) -> str:
    return hashlib.sha256(code.encode("utf-8")).hexdigest()


def _normalize_phone(phone: str) -> str:
    """Strip spaces and dashes. Convert UK '07' prefix to '+447'."""
    if not phone:
        return phone
    cleaned = re.sub(r"[\s\-()]+", "", phone)
    if cleaned.startswith("0044"):
        cleaned = "+44" + cleaned[4:]
    elif cleaned.startswith("44") and len(cleaned) >= 12:
        cleaned = "+" + cleaned
    elif cleaned.startswith("07"):
        cleaned = "+44" + cleaned[1:]
    return cleaned


def is_likely_whatsapp(phone: str) -> bool:
    """Heuristic: looks like a mobile number → assume WhatsApp-enabled."""
    if not phone:
        return False
    norm = _normalize_phone(phone)
    return bool(_MOBILE_RE.match(norm))


def _new_code() -> str:
    return "".join(secrets.choice(_DIGITS) for _ in range(OTP_LENGTH))


# ── Generation + delivery ───────────────────────────────────────────────────

async def issue_email_otp(db: AsyncSession, email: str, full_name: str | None = None) -> str:
    """Generate, persist, and email an OTP. Returns the channel used ('email')."""
    code = _new_code()
    row = OtpCode(
        id=uuid.uuid4(),
        purpose="signup_email",
        destination=email.lower(),
        channel="email",
        code_hash=_hash_code(code),
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=OTP_TTL_MINUTES),
    )
    db.add(row)
    await db.flush()

    adapter = get_email_adapter()
    body = _render_email_otp(full_name=full_name or "there", code=code)
    try:
        await adapter.send(EmailMessage(
            to=email,
            to_name=full_name or "",
            subject=f"Your CustomerFlow verification code: {code}",
            html_body=body,
        ))
    except Exception as exc:  # noqa: BLE001 — log but don't leak to caller
        log.warning("Failed to send signup email OTP to %s: %s", email, exc)
    return "email"


async def issue_phone_otp(db: AsyncSession, phone: str, full_name: str | None = None) -> str:
    """Generate, persist, and send a phone OTP via WhatsApp (preferred) or SMS.

    Returns the channel actually used: 'whatsapp' or 'sms'.
    """
    code = _new_code()
    norm = _normalize_phone(phone)
    use_whatsapp = is_likely_whatsapp(norm)
    channel: Literal["whatsapp", "sms"] = "whatsapp" if use_whatsapp else "sms"

    body_text = (
        f"Your CustomerFlow verification code is {code}. "
        f"It expires in {OTP_TTL_MINUTES} minutes. Don't share this code with anyone."
    )

    delivered = False
    if use_whatsapp:
        try:
            wa = get_whatsapp_adapter()
            res = await wa.send(WhatsAppMessage(to=norm, body=body_text))
            if res and getattr(res, "status", "").lower() not in {"failed", "error"}:
                delivered = True
            else:
                log.info("WhatsApp send returned non-success for %s; falling back to SMS", norm)
        except Exception as exc:  # noqa: BLE001
            log.info("WhatsApp send failed for %s: %s — falling back to SMS", norm, exc)

    if not delivered:
        channel = "sms"
        try:
            sms = get_sms_adapter()
            await sms.send(SMSMessage(to=norm, body=body_text))
        except Exception as exc:  # noqa: BLE001
            log.warning("SMS send also failed for %s: %s", norm, exc)

    row = OtpCode(
        id=uuid.uuid4(),
        purpose="signup_phone",
        destination=norm,
        channel=channel,
        code_hash=_hash_code(code),
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=OTP_TTL_MINUTES),
    )
    db.add(row)
    await db.flush()
    return channel


# ── Verification ────────────────────────────────────────────────────────────

async def verify_otp(
    db: AsyncSession,
    *,
    purpose: str,
    destination: str,
    code: str,
) -> bool:
    """Verify a code. Marks it verified on success. Increments attempts on failure.

    Returns True only when an unexpired, unverified code matches.
    """
    if not code or not code.isdigit() or len(code) != OTP_LENGTH:
        return False

    dest = destination.lower() if "@" in destination else _normalize_phone(destination)
    now = datetime.now(timezone.utc)

    row = (
        await db.execute(
            select(OtpCode)
            .where(
                OtpCode.purpose == purpose,
                OtpCode.destination == dest,
                OtpCode.verified_at.is_(None),
                OtpCode.expires_at > now,
            )
            .order_by(OtpCode.created_at.desc())
            .limit(1)
        )
    ).scalar_one_or_none()

    if row is None:
        return False

    if row.attempts >= row.max_attempts:
        return False

    if row.code_hash != _hash_code(code):
        await db.execute(
            update(OtpCode).where(OtpCode.id == row.id).values(attempts=OtpCode.attempts + 1)
        )
        await db.flush()
        return False

    await db.execute(
        update(OtpCode).where(OtpCode.id == row.id).values(verified_at=now)
    )
    await db.flush()
    return True


# ── Email body renderer ─────────────────────────────────────────────────────

def _render_email_otp(*, full_name: str, code: str) -> str:
    """Minimal-dep HTML email for the signup OTP."""
    return f"""<!doctype html>
<html><body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background:#f6f7f9; padding:24px;">
  <table cellpadding="0" cellspacing="0" border="0" style="max-width:480px; margin:0 auto; background:#ffffff; border-radius:12px; overflow:hidden; border:1px solid #e5e7eb;">
    <tr><td style="padding:24px 28px; border-bottom:1px solid #f1f5f9;">
      <div style="font-weight:700; font-size:18px; color:#0f172a;">CustomerFlow AI</div>
      <div style="font-size:12px; color:#64748b;">Verify your email to finish signing up</div>
    </td></tr>
    <tr><td style="padding:24px 28px;">
      <p style="margin:0 0 12px 0; color:#0f172a;">Hi {full_name},</p>
      <p style="margin:0 0 16px 0; color:#475569; font-size:14px;">
        Enter this 6-digit code on the verification screen to finish creating your account.
        It expires in {OTP_TTL_MINUTES} minutes.
      </p>
      <div style="font-family: 'SF Mono','Menlo','Consolas',monospace; font-size:34px; letter-spacing:0.4em; text-align:center; padding:18px 0; background:#0f172a; color:#fafafa; border-radius:8px; font-weight:700;">
        {code}
      </div>
      <p style="margin:16px 0 0 0; font-size:12px; color:#94a3b8;">
        If you didn't request this code, just ignore this email — no account will be created.
      </p>
    </td></tr>
  </table>
</body></html>"""
