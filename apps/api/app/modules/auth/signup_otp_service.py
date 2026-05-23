"""Pre-registration OTP signup flow (email OTP only).

Two endpoints back this:
  * POST /auth/signup/initiate  -> create a PendingSignup row + email OTP
  * POST /auth/signup/verify    -> validate email code, then commit user/tenant

Phone is stored on the account when provided but is not OTP-verified.
The /auth/register endpoint remains as a non-OTP fallback.
"""
from __future__ import annotations

import json
import logging
import os
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters import get_email_adapter, get_sms_adapter, get_whatsapp_adapter
from app.adapters.email.base import EmailMessage
from app.adapters.sms.base import SMSMessage
from app.adapters.whatsapp.base import WhatsAppMessage
from app.core.exceptions import ConflictException, NotFoundException, UnauthorizedException
from app.core.security import hash_password
from app.modules.auth.models import User
from app.modules.auth.otp_models import OtpCode, PendingSignup
from app.modules.tenants import models as _tenant_models  # noqa: F401 — register TenantMember for User ORM
from app.modules.auth.otp_service import (
    OTP_TTL_MINUTES,
    _normalize_phone,
    issue_email_otp,
    is_likely_whatsapp,
    verify_otp,
)
from app.modules.auth.schemas import SignupInitiateRequest, SignupVerifyRequest
from app.modules.auth.service import _issue_tokens

log = logging.getLogger(__name__)

PENDING_TTL_MINUTES = 15


def _mask_phone(phone: str) -> str:
    norm = _normalize_phone(phone)
    if len(norm) < 6:
        return "***"
    return f"{norm[:3]}***{norm[-3:]}"


# ── Initiate ────────────────────────────────────────────────────────────────

async def initiate(db: AsyncSession, data: SignupInitiateRequest) -> dict:
    """Create the pending signup record and dispatch the email OTP."""
    email = data.email.lower()
    existing = (
        await db.execute(select(User).where(User.email == email))
    ).scalar_one_or_none()
    if existing:
        raise ConflictException("An account with this email already exists")

    # Wipe any prior pending signup for this email — last one wins.
    await db.execute(delete(PendingSignup).where(PendingSignup.email == email))

    payload = {
        "full_name": data.full_name,
        "user_type": data.user_type,
        "business_name": data.business_name,
        "business_type": data.business_type,
        "postcode": data.postcode,
        "estimated_client_count": data.estimated_client_count,
    }
    pending = PendingSignup(
        id=uuid.uuid4(),
        email=email,
        phone=_normalize_phone(data.phone or ""),
        user_type=data.user_type,
        password_hash=hash_password(data.password),
        payload=payload,
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=PENDING_TTL_MINUTES),
    )
    db.add(pending)
    await db.flush()

    await issue_email_otp(db, email=email, full_name=data.full_name)
    # Signup never issues phone/SMS OTP — phone is optional contact info only.
    await db.commit()

    return {
        "pending_id": pending.id,
        "email": email,
        "expires_in_seconds": OTP_TTL_MINUTES * 60,
    }


# ── Verify ──────────────────────────────────────────────────────────────────

async def verify_and_complete(
    db: AsyncSession, data: SignupVerifyRequest
) -> tuple[User, dict]:
    """Verify the email OTP; on success commit the registration and return tokens."""
    pending = (
        await db.execute(select(PendingSignup).where(PendingSignup.id == data.pending_id))
    ).scalar_one_or_none()
    if pending is None:
        raise NotFoundException("Signup session not found or expired")
    if pending.expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
        await db.delete(pending)
        await db.commit()
        raise UnauthorizedException("Signup session expired — please start again")

    email_ok = await verify_otp(
        db, purpose="signup_email", destination=pending.email, code=data.email_code
    )
    if not email_ok:
        await db.commit()
        raise UnauthorizedException("Verification failed — check your email code and try again.")

    payload = pending.payload or {}
    now = datetime.now(timezone.utc)
    user = User(
        id=uuid.uuid4(),
        email=pending.email,
        password_hash=pending.password_hash,
        full_name=payload.get("full_name") or pending.email.split("@")[0],
        phone=pending.phone,
        user_type=pending.user_type,
        email_verified_at=now,
        phone_verified_at=None,
        estimated_client_count=(
            payload.get("estimated_client_count") if pending.user_type == "freelancer" else None
        ),
        onboarding_completed=False,
    )
    db.add(user)
    await db.flush()

    if pending.user_type == "freelancer":
        from app.modules.billing.freelancer_pricing import calculate_freelancer_price
        from app.modules.billing.models import FreelancerBilling

        count = int(payload.get("estimated_client_count") or 0)
        price = calculate_freelancer_price(count)
        db.add(FreelancerBilling(
            id=uuid.uuid4(),
            user_id=user.id,
            estimated_client_count=count,
            calculated_price=price,
            calculation_source="auto",
        ))
    else:
        # tenant signup → create tenant + owner membership (mirror service.register)
        from app.modules.tenants.models import Tenant, TenantMember
        from app.modules.tenants.service import _slugify

        tenant = Tenant(
            id=uuid.uuid4(),
            slug=_slugify(payload.get("business_name") or pending.email.split("@")[0]),
            name=payload.get("business_name") or "My Business",
            business_type=payload.get("business_type") or "other",
            postcode=(payload.get("postcode") or "").upper(),
        )
        db.add(tenant)
        await db.flush()
        db.add(TenantMember(
            id=uuid.uuid4(),
            tenant_id=tenant.id,
            user_id=user.id,
            role="owner",
            joined_at=now,
        ))

    await db.delete(pending)
    await db.commit()
    await db.refresh(user)

    # Dispatch welcome messaging — best-effort.
    await _send_welcome_messages(user=user, payload=payload, pending_phone=pending.phone)

    tokens = await _issue_tokens(db, user)

    if pending.user_type == "tenant":
        try:
            from app.modules.tenants.models import Tenant, TenantMember
            from app.modules.membership_rewards.hooks import on_tenant_signup

            tenant_row = (
                await db.execute(
                    select(Tenant)
                    .join(TenantMember, TenantMember.tenant_id == Tenant.id)
                    .where(TenantMember.user_id == user.id, TenantMember.role == "owner")
                )
            ).scalar_one_or_none()
            if tenant_row:
                await on_tenant_signup(db, tenant_row.id)
        except Exception:  # noqa: BLE001
            log.exception("Post-signup membership trial start failed for user %s", user.id)

    return user, tokens


# ── Welcome dispatch ────────────────────────────────────────────────────────

async def _send_welcome_messages(*, user: User, payload: dict, pending_phone: str) -> None:
    """Send welcome email + WhatsApp/SMS. Never raise — best-effort."""
    frontend_url = os.getenv("FRONTEND_URL", "https://app.customerflow.ai")
    onboarding_url = f"{frontend_url}/onboarding"
    user_type = user.user_type

    # ── Email ──
    try:
        from app.templates.renderer import render_welcome

        adapter = get_email_adapter()
        subject = (
            f"Welcome to CustomerFlow AI — {payload.get('business_name', '')}".strip(" —")
            if user_type == "tenant"
            else "Welcome to CustomerFlow AI — Your freelancer workspace is ready"
        )
        trial_ends = (datetime.now(timezone.utc) + timedelta(days=14)).strftime("%d %B %Y")
        await adapter.send(
            EmailMessage(
                to=user.email,
                to_name=user.full_name,
                subject=subject,
                html_body=render_welcome(
                    full_name=user.full_name,
                    email=user.email,
                    business_name=payload.get("business_name")
                    or ("Your freelancer workspace" if user_type == "freelancer" else ""),
                    dashboard_url=onboarding_url,
                    trial_ends=trial_ends,
                ),
            )
        )
    except Exception as exc:  # noqa: BLE001
        log.warning("Welcome email send failed for %s: %s", user.email, exc)

    # ── WhatsApp / SMS welcome ──
    short_msg = (
        f"Welcome to CustomerFlow AI, {user.full_name.split(' ')[0]}! 🎉 "
        f"Your account is ready — finish setup here: {onboarding_url}"
    )
    delivered = False
    if pending_phone and is_likely_whatsapp(pending_phone):
        try:
            wa = get_whatsapp_adapter()
            res = await wa.send(WhatsAppMessage(to=pending_phone, body=short_msg))
            if res and getattr(res, "status", "").lower() not in {"failed", "error"}:
                delivered = True
        except Exception as exc:  # noqa: BLE001
            log.info("WhatsApp welcome failed for %s: %s — falling back to SMS", pending_phone, exc)

    if not delivered and pending_phone:
        try:
            sms = get_sms_adapter()
            await sms.send(SMSMessage(to=pending_phone, body=short_msg))
        except Exception as exc:  # noqa: BLE001
            log.warning("SMS welcome failed for %s: %s", pending_phone, exc)


# ── Resend ──────────────────────────────────────────────────────────────────

async def resend_code(db: AsyncSession, *, pending_id: uuid.UUID, channel: str) -> dict:
    pending = (
        await db.execute(select(PendingSignup).where(PendingSignup.id == pending_id))
    ).scalar_one_or_none()
    if pending is None:
        raise NotFoundException("Signup session not found")

    if channel != "email":
        raise UnauthorizedException("Only email verification is used for signup")
    await issue_email_otp(db, email=pending.email, full_name=(pending.payload or {}).get("full_name"))
    await db.commit()
    return {"channel": "email", "destination_masked": pending.email}
