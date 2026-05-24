"""Membership & Rewards add-on constants."""

from __future__ import annotations

FEATURE_MEMBERSHIP_REWARDS = "membership_rewards"

TRIAL_DAYS = 7
WINBACK_DAY = 15
WINBACK_DISCOUNT_PERCENT = 50

BILLING_CYCLES = frozenset({"weekly", "monthly", "quarterly", "yearly"})

TIER_CODES = ("bronze", "silver", "gold", "platinum")

DEFAULT_TIERS: list[dict] = [
    {"code": "bronze", "name": "Bronze", "min_points_lifetime": 0, "sort_order": 0},
    {"code": "silver", "name": "Silver", "min_points_lifetime": 500, "sort_order": 1},
    {"code": "gold", "name": "Gold", "min_points_lifetime": 2000, "sort_order": 2},
    {"code": "platinum", "name": "Platinum", "min_points_lifetime": 5000, "sort_order": 3},
]

DEFAULT_EARN_RULES: dict = {
    "booking_completed": 50,
    "purchase_per_pound": 10,
    "product_per_pound": 10,
    "product_per_item": 5,
    "membership_signup": 200,
    "refer_win": 100,
    "review_left": 75,
    "qr_checkin": 25,
    "birthday_bonus": 100,
}

POINT_SOURCES = frozenset(
    {
        "booking",
        "purchase",
        "membership",
        "refer_win",
        "review",
        "milestone",
        "redeem",
        "adjustment",
        "expiration",
        "qr_checkin",
        "birthday",
    }
)

CUSTOMER_MAGIC_LINK_EXPIRE_MINUTES = 30
CUSTOMER_QR_TOKEN_EXPIRE_MINUTES = 10
