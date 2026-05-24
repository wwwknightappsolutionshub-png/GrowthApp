"""Welcome email after public loyalty tier enrollment."""

from __future__ import annotations

import logging
import urllib.parse

from app.adapters import get_email_adapter
from app.adapters.email.base import EmailMessage

logger = logging.getLogger(__name__)

QR_API = "https://api.qrserver.com/v1/create-qr-code/"


def _qr_img_url(link: str, size: int = 180) -> str:
    return f"{QR_API}?size={size}x{size}&data={urllib.parse.quote(link, safe='')}"


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
