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
    "membership_signup": 200,
    "refer_win": 100,
    "review_left": 75,
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
    }
)
