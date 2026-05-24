"""Welcome emails for loyalty program enrollment and portal provisioning."""

from __future__ import annotations

import logging
import urllib.parse

from app.adapters import get_email_adapter
from app.adapters.email.base import EmailMessage
from app.modules.membership_rewards.constants import CUSTOMER_MAGIC_LINK_EXPIRE_MINUTES

logger = logging.getLogger(__name__)

QR_API = "https://api.qrserver.com/v1/create-qr-code/"


def _qr_img_url(link: str, size: int = 180) -> str:
    return f"{QR_API}?size={size}x{size}&data={urllib.parse.quote(link, safe='')}"


def build_portal_welcome_html(
    *,
    customer_name: str,
    tenant_name: str,
    rewards_portal_url: str,
    magic_link_url: str | None,
    temp_password: str | None = None,
    signup_bonus_points: int = 0,
    points_balance: int = 0,
    refer_win_url: str | None = None,
    memberships_url: str | None = None,
    tier_name: str | None = None,
    wallet_checkin_qr_url: str | None = None,
) -> str:
    portal_qr = _qr_img_url(rewards_portal_url)
    checkin_qr_block = ""
    if wallet_checkin_qr_url:
        checkin_qr = _qr_img_url(wallet_checkin_qr_url)
        checkin_qr_block = f"""
  <h2 style="font-size:18px;color:#025422;margin-top:28px;">In-store check-in QR</h2>
  <p style="text-align:center;margin:20px 0;">
    <img src="{checkin_qr}" alt="In-store check-in QR code" width="180" height="180"
         style="border:1px solid #e5e7eb;border-radius:8px;padding:8px;" />
  </p>
  <p style="text-align:center;font-size:13px;color:#6b7280;">
    Show this code at the counter for visit points. For security it expires — open your wallet app anytime for a fresh QR.
  </p>"""
    bonus_block = ""
    if signup_bonus_points > 0:
        bonus_block = f"""
  <p style="background:#ecfdf5;border:1px solid #a7f3d0;border-radius:8px;padding:14px 16px;margin:20px 0;">
    <strong>+{signup_bonus_points} welcome points</strong> have been added to your account.
    Your balance is now <strong>{points_balance}</strong> points.
  </p>"""
    tier_line = f" You&apos;re on the <strong>{tier_name}</strong> tier." if tier_name else ""
    password_block = ""
    if temp_password:
        password_block = f"""
  <p style="background:#eff6ff;border:1px solid #bfdbfe;border-radius:8px;padding:14px 16px;margin:20px 0;">
    <strong>Your temporary password:</strong> <code style="font-size:16px;">{temp_password}</code><br/>
    <span style="font-size:13px;color:#475569;">Sign in at your rewards wallet with this email and password, or use the magic link below. You&apos;ll be asked to set a new password on first login.</span>
  </p>"""
    login_block = ""
    if magic_link_url:
        login_block = f"""
  <p style="text-align:center;margin:24px 0;">
    <a href="{magic_link_url}"
       style="display:inline-block;background:#025422;color:#fff;padding:14px 28px;
              border-radius:8px;text-decoration:none;font-weight:600;">Open your rewards wallet</a>
  </p>
  <p style="font-size:13px;color:#6b7280;text-align:center;">
    This secure link expires in {CUSTOMER_MAGIC_LINK_EXPIRE_MINUTES} minutes.
    You can request a new login link anytime from the rewards app.
  </p>"""
    refer_block = ""
    if refer_win_url:
        refer_qr = _qr_img_url(refer_win_url)
        refer_block = f"""
  <h2 style="font-size:18px;color:#025422;margin-top:28px;">Refer &amp; Win</h2>
  <p>Share your referral link with friends. When they become customers, you earn loyalty points.</p>
  <p style="text-align:center;margin:20px 0;">
    <img src="{refer_qr}" alt="Refer and Win QR code" width="180" height="180"
         style="border:1px solid #e5e7eb;border-radius:8px;padding:8px;" />
  </p>
  <p style="text-align:center;">
    <a href="{refer_win_url}"
       style="display:inline-block;background:#025422;color:#fff;padding:12px 24px;
              border-radius:8px;text-decoration:none;font-weight:600;">Refer Now</a>
  </p>"""
    memberships_block = ""
    if memberships_url:
        memberships_block = f"""
  <h2 style="font-size:18px;color:#025422;margin-top:28px;">Membership plans</h2>
  <p>Explore membership options for exclusive discounts and bonus points.</p>
  <p style="text-align:center;">
    <a href="{memberships_url}"
       style="display:inline-block;background:#20ccce;color:#0a2e2e;padding:12px 24px;
              border-radius:8px;text-decoration:none;font-weight:600;">View membership plans</a>
  </p>"""
    return f"""
<div style="font-family:system-ui,sans-serif;max-width:560px;margin:0 auto;color:#1a1a1a;">
  <p>Hi {customer_name},</p>
  <p>Your rewards wallet is ready.{tier_line} Track points, view rewards, and redeem perks online or in-store.</p>
  {bonus_block}
  {password_block}

  <h2 style="font-size:18px;color:#025422;margin-top:28px;">Your rewards app</h2>
  <p style="text-align:center;margin:20px 0;">
    <img src="{portal_qr}" alt="Rewards app QR code" width="180" height="180"
         style="border:1px solid #e5e7eb;border-radius:8px;padding:8px;" />
  </p>
  <p style="text-align:center;font-size:13px;color:#6b7280;">Scan to open your wallet, or use the button below.</p>
  {login_block}
  {checkin_qr_block}
  {refer_block}
  {memberships_block}

  <p style="margin-top:32px;font-size:13px;color:#6b7280;">— {tenant_name}</p>
</div>
"""


async def send_portal_welcome_email(
    *,
    to: str,
    customer_name: str,
    tenant_name: str,
    rewards_portal_url: str,
    magic_link_url: str | None = None,
    temp_password: str | None = None,
    signup_bonus_points: int = 0,
    points_balance: int = 0,
    refer_win_url: str | None = None,
    memberships_url: str | None = None,
    tier_name: str | None = None,
    wallet_checkin_qr_url: str | None = None,
) -> None:
    if not (to or "").strip():
        return
    subject = f"Your {tenant_name} rewards wallet is ready"
    html = build_portal_welcome_html(
        customer_name=customer_name,
        tenant_name=tenant_name,
        rewards_portal_url=rewards_portal_url,
        magic_link_url=magic_link_url,
        temp_password=temp_password,
        signup_bonus_points=signup_bonus_points,
        points_balance=points_balance,
        refer_win_url=refer_win_url,
        memberships_url=memberships_url,
        tier_name=tier_name,
        wallet_checkin_qr_url=wallet_checkin_qr_url,
    )
    try:
        adapter = get_email_adapter()
        await adapter.send(
            EmailMessage(to=to.strip(), to_name=customer_name, subject=subject, html_body=html)
        )
    except Exception:  # noqa: BLE001
        logger.exception("Failed to send portal welcome email to %s", to)


def build_loyalty_welcome_html(
    *,
    customer_name: str,
    tenant_name: str,
    tier_name: str,
    signup_bonus_points: int,
    points_balance: int,
    refer_win_url: str,
    memberships_url: str,
) -> str:
    refer_qr = _qr_img_url(refer_win_url)
    bonus_block = ""
    if signup_bonus_points > 0:
        bonus_block = f"""
  <p style="background:#ecfdf5;border:1px solid #a7f3d0;border-radius:8px;padding:14px 16px;margin:20px 0;">
    <strong>+{signup_bonus_points} membership points</strong> have been added to your account.
    Your balance is now <strong>{points_balance}</strong> points.
  </p>"""
    return f"""
<div style="font-family:system-ui,sans-serif;max-width:560px;margin:0 auto;color:#1a1a1a;">
  <p>Hi {customer_name},</p>
  <p>Thank you for signing up to our loyalty program! You&apos;ve joined at the
  <strong>{tier_name}</strong> tier — start earning points on every visit.</p>
  {bonus_block}

  <h2 style="font-size:18px;color:#025422;margin-top:28px;">Refer &amp; Win</h2>
  <p>Share your referral link with friends. When they become customers, you earn loyalty points.</p>
  <p style="text-align:center;margin:20px 0;">
    <img src="{refer_qr}" alt="Refer and Win QR code" width="180" height="180"
         style="border:1px solid #e5e7eb;border-radius:8px;padding:8px;" />
  </p>
  <p style="text-align:center;">
    <a href="{refer_win_url}"
       style="display:inline-block;background:#025422;color:#fff;padding:12px 24px;
              border-radius:8px;text-decoration:none;font-weight:600;">Refer Now</a>
  </p>

  <h2 style="font-size:18px;color:#025422;margin-top:28px;">Membership plans</h2>
  <p>Explore our membership options for exclusive discounts, included services, and bonus points.</p>
  <p style="text-align:center;">
    <a href="{memberships_url}"
       style="display:inline-block;background:#20ccce;color:#0a2e2e;padding:12px 24px;
              border-radius:8px;text-decoration:none;font-weight:600;">View membership plans</a>
  </p>

  <p style="margin-top:32px;font-size:13px;color:#6b7280;">— {tenant_name}</p>
</div>
"""


async def send_loyalty_welcome_email(
    *,
    to: str,
    customer_name: str,
    tenant_name: str,
    tier_name: str,
    signup_bonus_points: int = 0,
    points_balance: int = 0,
    refer_win_url: str,
    memberships_url: str,
) -> None:
    if not (to or "").strip():
        return
    subject = f"Welcome to {tenant_name}'s loyalty program"
    html = build_loyalty_welcome_html(
        customer_name=customer_name,
        tenant_name=tenant_name,
        tier_name=tier_name,
        signup_bonus_points=signup_bonus_points,
        points_balance=points_balance,
        refer_win_url=refer_win_url,
        memberships_url=memberships_url,
    )
    try:
        adapter = get_email_adapter()
        await adapter.send(
            EmailMessage(to=to.strip(), to_name=customer_name, subject=subject, html_body=html)
        )
    except Exception:  # noqa: BLE001
        logger.exception("Failed to send loyalty welcome email to %s", to)
