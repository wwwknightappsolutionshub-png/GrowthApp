"""Marketplace ingest result types."""
from __future__ import annotations

from dataclasses import dataclass

from app.modules.lead_marketplace.models import LeadMarketplace


@dataclass(frozen=True)
class MarketplaceIngestResult:
    marketplace: LeadMarketplace | None
    status: str
    detail: str | None = None

    @property
    def ingested(self) -> bool:
        return self.marketplace is not None and self.status == "ingested"
