"""
Vertical strategy registry (Phase 3+).

Each vertical registers booking/billing/crm handlers without hardcoding branches in routers.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.modules.addons.common.constants import Vertical

if TYPE_CHECKING:
    pass

# Placeholder — populated in Phase 3 when salon booking ships.
VERTICAL_MODULES: dict[Vertical, dict[str, str]] = {
    Vertical.SALON: {"booking": "addons.verticals.salon.booking", "billing": "addons.verticals.salon.billing", "crm": "addons.verticals.salon.crm"},
    Vertical.REALTOR: {"booking": "addons.verticals.realtor.booking", "billing": "addons.verticals.realtor.billing", "crm": "addons.verticals.realtor.crm"},
    Vertical.GARAGE: {"booking": "addons.verticals.garage.booking", "billing": "addons.verticals.garage.billing", "crm": "addons.verticals.garage.crm"},
}
