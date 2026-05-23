"""Industry add-on feature codes and vertical identifiers."""

from __future__ import annotations

from enum import StrEnum

# Paid add-on SKUs (stored in tenant_addons.feature_code)
FEATURE_INDUSTRY_BOOKING = "industry_booking"
FEATURE_INDUSTRY_BILLING = "industry_billing"
FEATURE_INDUSTRY_CRM = "industry_crm"

INDUSTRY_FEATURE_CODES: frozenset[str] = frozenset(
    {
        FEATURE_INDUSTRY_BOOKING,
        FEATURE_INDUSTRY_BILLING,
        FEATURE_INDUSTRY_CRM,
    }
)


class Vertical(StrEnum):
    SALON = "salon"
    REALTOR = "realtor"
    GARAGE = "garage"


# Maps common business_type strings → vertical (fallback: salon)
BUSINESS_TYPE_VERTICAL_MAP: dict[str, Vertical] = {
    "salon": Vertical.SALON,
    "beautician": Vertical.SALON,
    "barber": Vertical.SALON,
    "spa": Vertical.SALON,
    "hair": Vertical.SALON,
    "realtor": Vertical.REALTOR,
    "estate agent": Vertical.REALTOR,
    "estate_agent": Vertical.REALTOR,
    "property": Vertical.REALTOR,
    "garage": Vertical.GARAGE,
    "mechanic": Vertical.GARAGE,
    "auto": Vertical.GARAGE,
    "mot": Vertical.GARAGE,
    "automotive": Vertical.GARAGE,
}
