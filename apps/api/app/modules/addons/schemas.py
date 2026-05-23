"""Pydantic schemas for industry add-on APIs (salon + garage)."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, Field


# --- Booking ---


class SessionServiceIn(BaseModel):
    service_id: uuid.UUID
    sort_order: int = 0
    duration_minutes: int | None = None


class MultiServiceSessionCreate(BaseModel):
    booking_id: uuid.UUID
    services: list[SessionServiceIn]


class StaffSkillIn(BaseModel):
    staff_id: uuid.UUID
    skill_code: str
    proficiency_level: int = Field(default=1, ge=1, le=5)


class ServiceSkillIn(BaseModel):
    service_id: uuid.UUID
    skill_code: str
    min_proficiency: int = 1


class ResourceAllocateIn(BaseModel):
    booking_id: uuid.UUID
    resource_id: uuid.UUID


class UpsellLineIn(BaseModel):
    product_id: uuid.UUID | None = None
    description: str
    quantity: int = 1
    unit_price_pence: int


class ProductCatalogIn(BaseModel):
    sku: str
    name: str
    description: str | None = None
    unit_price_pence: int = 0


class MechanicSkillIn(BaseModel):
    staff_id: uuid.UUID
    specialization: str
    proficiency_level: int = 1


class VehicleEstimateIn(BaseModel):
    make: str
    model: str
    service_code: str
    duration_minutes: int


class PartsInventoryIn(BaseModel):
    sku: str
    name: str
    category: str = "general"
    quantity_on_hand: int = 0
    unit_cost_pence: int = 0
    reorder_level: int = 5


class VehicleIn(BaseModel):
    customer_id: uuid.UUID
    vin: str | None = None
    make: str
    model: str
    year: int | None = None
    mileage: int | None = None
    registration: str | None = None


# --- Billing ---


class ComboInvoiceLineIn(BaseModel):
    description: str
    quantity: int = 1
    unit_price_pence: int
    vat_rate: int = 20
    line_kind: str = Field(default="service", pattern="^(service|product|labor|part)$")


class IndustryInvoiceCreate(BaseModel):
    customer_id: uuid.UUID
    title: str
    items: list[ComboInvoiceLineIn]
    deal_id: uuid.UUID | None = None
    booking_id: uuid.UUID | None = None
    vehicle_id: uuid.UUID | None = None


class TipIn(BaseModel):
    invoice_id: uuid.UUID
    amount_pence: int
    method: str = "card"


class MembershipIn(BaseModel):
    customer_id: uuid.UUID
    name: str
    monthly_price_pence: int
    benefits: list[str] = Field(default_factory=list)


class ServicePackageIn(BaseModel):
    name: str
    sessions_included: int
    price_pence: int
    valid_days: int = 365
    vertical: str = "salon"


class TemplateIn(BaseModel):
    name: str
    vertical: str = "garage"
    line_items: list[dict[str, Any]] = Field(default_factory=list)


class MarkupRuleIn(BaseModel):
    category: str
    markup_percent: int = Field(ge=0, le=200)


class WarrantyIn(BaseModel):
    invoice_id: uuid.UUID
    months: int = 12
    terms: str | None = None


# --- CRM ---


class SalonProfileIn(BaseModel):
    customer_id: uuid.UUID
    color_formula: str | None = None
    allergies: str | None = None
    stylist_notes: str | None = None
    segment_tags: list[str] = Field(default_factory=list)


class MediaTimelineIn(BaseModel):
    customer_id: uuid.UUID
    image_url: str
    caption: str | None = None
    taken_at: datetime | None = None


class GarageScoreRefreshIn(BaseModel):
    customer_id: uuid.UUID


class CheckoutIn(BaseModel):
    feature_code: str
    success_url: str
    cancel_url: str
