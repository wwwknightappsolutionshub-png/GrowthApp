"""Result types for crawler lead insertion."""
from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any


@dataclass
class InsertLeadResult:
    inserted: bool
    lead_id: uuid.UUID | None = None
    skip_reason: str | None = None
    extraction_method: str | None = None
    marketplace_status: str | None = None
    marketplace_detail: str | None = None

    def to_log_dict(self) -> dict[str, Any]:
        return {
            "inserted": self.inserted,
            "lead_id": str(self.lead_id) if self.lead_id else None,
            "skip_reason": self.skip_reason,
            "extraction_method": self.extraction_method,
            "marketplace_status": self.marketplace_status,
            "marketplace_detail": self.marketplace_detail,
        }
