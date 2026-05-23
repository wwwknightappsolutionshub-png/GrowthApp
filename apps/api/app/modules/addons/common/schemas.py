from __future__ import annotations

from pydantic import BaseModel, Field


class AddonStatusItem(BaseModel):
    feature_code: str
    active: bool


class AddonStatusResponse(BaseModel):
    vertical: str
    industry_booking: bool
    industry_billing: bool
    industry_crm: bool
    membership_rewards: bool = False
    items: list[AddonStatusItem] = Field(default_factory=list)


class SetVerticalRequest(BaseModel):
    vertical: str = Field(..., pattern="^(salon|realtor|garage)$")
