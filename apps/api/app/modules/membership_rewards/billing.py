"""Stripe billing sync for the Membership & Rewards tenant add-on."""

from __future__ import annotations

import logging
import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.modules.accounting.models import TenantAddon
from app.modules.billing.models import Subscription
from app.modules.membership_rewards.constants import FEATURE_MEMBERSHIP_REWARDS

logger = logging.getLogger(__name__)

_ACTIVE_STRIPE_STATUSES = frozenset({"active", "trialing"})
_REVOKED_STRIPE_STATUSES = frozenset({"canceled", "unpaid", "incomplete_expired"})


def resolve_stripe_subscription_item_from_checkout(checkout_session_id: str) -> str | None:
    """Return the subscription item id for the membership price from a completed checkout."""
    if not checkout_session_id or not settings.STRIPE_PRICE_MEMBERSHIP_REWARDS:
        return None
    import stripe

    stripe.api_key = settings.STRIPE_SECRET_KEY
    try:
        session = stripe.checkout.Session.retrieve(
            checkout_session_id,
            expand=["subscription.items.data.price"],
        )
    except Exception as exc:
        logger.warning("Stripe checkout retrieve failed for %s: %s", checkout_session_id, exc)
        return None

    sub = session.get("subscription") if isinstance(session, dict) else getattr(session, "subscription", None)
    if not sub:
        return None

    items = _subscription_items(sub)
    for item in items:
        price_id = _item_price_id(item)
        if price_id == settings.STRIPE_PRICE_MEMBERSHIP_REWARDS:
            return _item_id(item)
    return _item_id(items[0]) if items else None


def _subscription_items(sub: Any) -> list[Any]:
    if isinstance(sub, dict):
        return (sub.get("items") or {}).get("data") or []
    items_obj = getattr(sub, "items", None)
    if items_obj is None:
        return []
    data = getattr(items_obj, "data", None)
    return list(data or [])


def _item_id(item: Any) -> str | None:
    if isinstance(item, dict):
        return item.get("id")
    return getattr(item, "id", None)


def _item_price_id(item: Any) -> str | None:
    if isinstance(item, dict):
        price = item.get("price") or {}
        return price.get("id") if isinstance(price, dict) else None
    price = getattr(item, "price", None)
    return getattr(price, "id", None) if price else None


def _membership_item_from_subscription(stripe_sub: dict[str, Any]) -> tuple[str | None, str | None]:
    """Return (subscription_item_id, price_id) for the membership SKU if present."""
    for item in stripe_sub.get("items", {}).get("data") or []:
        price_id = _item_price_id(item)
        if price_id == settings.STRIPE_PRICE_MEMBERSHIP_REWARDS:
            return _item_id(item), price_id
    return None, None


async def sync_addon_from_stripe_subscription(
    db: AsyncSession,
    *,
    stripe_subscription_id: str,
    stripe_sub: dict[str, Any] | None = None,
) -> None:
    """Activate or revoke membership_rewards from a Stripe subscription lifecycle event."""
    if not settings.STRIPE_PRICE_MEMBERSHIP_REWARDS:
        return

    import stripe

    stripe.api_key = settings.STRIPE_SECRET_KEY
    if stripe_sub is None:
        try:
            raw = stripe.Subscription.retrieve(
                stripe_subscription_id,
                expand=["items.data.price"],
            )
            stripe_sub = raw.to_dict() if hasattr(raw, "to_dict") else dict(raw)
        except Exception as exc:
            logger.warning("Stripe subscription retrieve failed for %s: %s", stripe_subscription_id, exc)
            return

    status = str(stripe_sub.get("status") or "")
    membership_item_id, _ = _membership_item_from_subscription(stripe_sub)

    tenant_id: uuid.UUID | None = None
    addon_row: TenantAddon | None = None

    if membership_item_id:
        addon_row = (
            await db.execute(
                select(TenantAddon).where(
                    TenantAddon.stripe_subscription_item_id == membership_item_id,
                    TenantAddon.feature_code == FEATURE_MEMBERSHIP_REWARDS,
                )
            )
        ).scalar_one_or_none()

    if addon_row:
        tenant_id = addon_row.tenant_id
    else:
        db_sub = (
            await db.execute(
                select(Subscription).where(Subscription.stripe_subscription_id == stripe_subscription_id)
            )
        ).scalar_one_or_none()
        if db_sub and membership_item_id:
            tenant_id = db_sub.tenant_id

    if tenant_id is None:
        return

    from app.modules.membership_rewards import service as mr_service

    if status in _ACTIVE_STRIPE_STATUSES and membership_item_id:
        await mr_service.activate_from_checkout_metadata(
            db,
            tenant_id=tenant_id,
            stripe_subscription_item_id=membership_item_id,
        )
        logger.info(
            "Membership & Rewards activated for tenant %s (subscription %s, status=%s)",
            tenant_id,
            stripe_subscription_id,
            status,
        )
    elif status in _REVOKED_STRIPE_STATUSES:
        await mr_service.revoke_addon(db, tenant_id)
        logger.info(
            "Membership & Rewards revoked for tenant %s (subscription %s, status=%s)",
            tenant_id,
            stripe_subscription_id,
            status,
        )
