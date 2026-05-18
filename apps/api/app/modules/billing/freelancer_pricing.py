"""Freelancer subscription pricing.

Implements the exact tiered formula defined in TASK 2:

    IF estimated_client_count BETWEEN 1 AND 50:
        calculated_price = 50

    IF estimated_client_count BETWEEN 51 AND 100:
        calculated_price = 40

    IF estimated_client_count > 100:
        extra_clients = estimated_client_count - 100
        calculated_price = 40 + (extra_clients * 5)
"""

from decimal import Decimal

_TIER_LOW = Decimal("50")
_TIER_MID = Decimal("40")
_PER_EXTRA_CLIENT = Decimal("5")


def calculate_freelancer_price(estimated_client_count: int) -> Decimal:
    """Return the monthly subscription price (GBP) for a freelancer.

    The spec defines behaviour only for counts >= 1; non-positive counts are
    treated as the lowest tier so a row can always be written.
    """
    if estimated_client_count <= 50:
        return _TIER_LOW
    if estimated_client_count <= 100:
        return _TIER_MID
    extra_clients = estimated_client_count - 100
    return _TIER_MID + (Decimal(extra_clients) * _PER_EXTRA_CLIENT)
