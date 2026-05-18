from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, EmailStr


class LocationBase(BaseModel):
    name: str
    slug: str
    address: str | None = None
    city: str | None = None
    postcode: str | None = None
    phone: str | None = None
    email: EmailStr | None = None
    is_primary: bool = False


class LocationCreate(LocationBase):
    pass


class LocationUpdate(BaseModel):
    name: str | None = None
    address: str | None = None
    city: str | None = None
    postcode: str | None = None
    phone: str | None = None
    email: EmailStr | None = None
    is_primary: bool | None = None


class LocationResponse(LocationBase):
    model_config = {"from_attributes": True}
    id: UUID
    tenant_id: UUID
    created_at: datetime


class TenantUpdate(BaseModel):
    name: str | None = None
    business_type: str | None = None
    logo_url: str | None = None
    primary_color: str | None = None
    website_url: str | None = None
    phone: str | None = None
    email: EmailStr | None = None
    address: str | None = None
    city: str | None = None
    postcode: str | None = None
    google_place_id: str | None = None
    google_review_url: str | None = None
    timezone: str | None = None


class TenantResponse(BaseModel):
    model_config = {"from_attributes": True}
    id: UUID
    slug: str
    name: str
    business_type: str
    logo_url: str | None
    primary_color: str
    website_url: str | None
    phone: str | None
    email: str | None
    address: str | None
    city: str | None
    postcode: str
    country: str
    google_place_id: str | None
    google_review_url: str | None
    timezone: str
    is_active: bool
    onboarding_completed: bool
    created_at: datetime


class MemberResponse(BaseModel):
    model_config = {"from_attributes": True}
    id: UUID
    user_id: UUID
    role: str
    joined_at: datetime | None
    created_at: datetime


class InviteMemberRequest(BaseModel):
    email: EmailStr
    full_name: str
    role: str = "staff"
