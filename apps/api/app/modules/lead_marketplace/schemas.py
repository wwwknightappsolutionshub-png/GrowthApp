"""Pydantic schemas for the Lead Marketplace module."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, field_validator


# ── LeadCategory ──────────────────────────────────────────────────────────────

class LeadCategoryCreate(BaseModel):
    name: str
    description: Optional[str] = None


class LeadCategoryUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class LeadCategoryResponse(BaseModel):
    model_config = {"from_attributes": True}
    id: uuid.UUID
    name: str
    description: Optional[str]
    created_at: datetime
    updated_at: datetime


# ── LeadQualityRule ───────────────────────────────────────────────────────────

class LeadQualityRuleCreate(BaseModel):
    name: str
    min_ai_score: int = 0
    max_age_days: int = 30
    requires_phone: bool = False
    requires_email: bool = False
    apply_to_category: Optional[uuid.UUID] = None

    @field_validator("min_ai_score")
    @classmethod
    def _score_range(cls, v: int) -> int:
        if not (0 <= v <= 100):
            raise ValueError("min_ai_score must be 0–100")
        return v


class LeadQualityRuleUpdate(BaseModel):
    name: Optional[str] = None
    min_ai_score: Optional[int] = None
    max_age_days: Optional[int] = None
    requires_phone: Optional[bool] = None
    requires_email: Optional[bool] = None
    apply_to_category: Optional[uuid.UUID] = None


class LeadQualityRuleResponse(BaseModel):
    model_config = {"from_attributes": True}
    id: uuid.UUID
    name: str
    min_ai_score: int
    max_age_days: int
    requires_phone: bool
    requires_email: bool
    apply_to_category: Optional[uuid.UUID]
    created_at: datetime
    updated_at: datetime


# ── LeadPricing ───────────────────────────────────────────────────────────────

class LeadPricingCreate(BaseModel):
    category_id: uuid.UUID
    base_price: float
    high_quality_multiplier: float = 1.0
    exclusive_multiplier: float = 1.0


class LeadPricingUpdate(BaseModel):
    category_id: Optional[uuid.UUID] = None
    base_price: Optional[float] = None
    high_quality_multiplier: Optional[float] = None
    exclusive_multiplier: Optional[float] = None


class LeadPricingResponse(BaseModel):
    model_config = {"from_attributes": True}
    id: uuid.UUID
    category_id: uuid.UUID
    base_price: float
    high_quality_multiplier: float
    exclusive_multiplier: float
    created_at: datetime
    updated_at: datetime


# ── LeadTerritory ─────────────────────────────────────────────────────────────

class LeadTerritoryCreate(BaseModel):
    name: str
    region_code: str
    country: str = "GB"


class LeadTerritoryUpdate(BaseModel):
    name: Optional[str] = None
    region_code: Optional[str] = None
    country: Optional[str] = None


class LeadTerritoryResponse(BaseModel):
    model_config = {"from_attributes": True}
    id: uuid.UUID
    name: str
    region_code: str
    country: str
    created_at: datetime
    updated_at: datetime


# ── LeadMarketplace ───────────────────────────────────────────────────────────

ExclusivityLiteral = Literal["shared", "semi-exclusive", "exclusive"]
StatusLiteral = Literal["available", "reserved", "sold", "expired"]


class MarketplaceItemCreate(BaseModel):
    lead_id: uuid.UUID
    category_id: uuid.UUID
    territory_id: uuid.UUID
    ai_score: int = 0
    price: float = 0.0
    exclusivity: ExclusivityLiteral = "shared"
    status: StatusLiteral = "available"


class MarketplaceItemUpdate(BaseModel):
    category_id: Optional[uuid.UUID] = None
    territory_id: Optional[uuid.UUID] = None
    ai_score: Optional[int] = None
    price: Optional[float] = None
    exclusivity: Optional[ExclusivityLiteral] = None
    status: Optional[StatusLiteral] = None
    assigned_tenant_id: Optional[uuid.UUID] = None


class MarketplaceAssignBody(BaseModel):
    tenant_id: uuid.UUID
    status: StatusLiteral = "reserved"


class MarketplaceItemResponse(BaseModel):
    model_config = {"from_attributes": True}
    id: uuid.UUID
    lead_id: uuid.UUID
    category_id: uuid.UUID
    territory_id: uuid.UUID
    ai_score: int
    price: float
    exclusivity: str
    status: str
    assigned_tenant_id: Optional[uuid.UUID]
    created_at: datetime
    updated_at: datetime


class MarketplaceItemDetail(MarketplaceItemResponse):
    """Extended response that joins category/territory names."""
    category_name: Optional[str] = None
    territory_name: Optional[str] = None


# ── LeadAssignmentRule ────────────────────────────────────────────────────────

class LeadAssignmentRuleCreate(BaseModel):
    rule_name: str
    category_id: Optional[uuid.UUID] = None
    territory_id: Optional[uuid.UUID] = None
    min_subscription_level: int = 0
    priority_weight: int = 1


class LeadAssignmentRuleUpdate(BaseModel):
    rule_name: Optional[str] = None
    category_id: Optional[uuid.UUID] = None
    territory_id: Optional[uuid.UUID] = None
    min_subscription_level: Optional[int] = None
    priority_weight: Optional[int] = None


class LeadAssignmentRuleResponse(BaseModel):
    model_config = {"from_attributes": True}
    id: uuid.UUID
    rule_name: str
    category_id: Optional[uuid.UUID]
    territory_id: Optional[uuid.UUID]
    min_subscription_level: int
    priority_weight: int
    created_at: datetime
    updated_at: datetime


# ── Auto-ingest (used by AI scraper worker) ───────────────────────────────────

class IngestLeadRequest(BaseModel):
    lead_id: uuid.UUID
    ai_score: int
    category_hint: Optional[str] = None
    territory_hint: Optional[str] = None


# ── Distribution ──────────────────────────────────────────────────────────────

class DistributionResult(BaseModel):
    marketplace_id: uuid.UUID
    assigned_tenant_id: uuid.UUID
    priority_score: float
    status: str
