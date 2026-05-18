from datetime import datetime
from uuid import UUID
from pydantic import BaseModel


class ReviewRequestResponse(BaseModel):
    model_config = {"from_attributes": True}
    id: UUID
    tenant_id: UUID
    status: str
    sent_at: datetime | None
    created_at: datetime


class ReviewResponse(BaseModel):
    model_config = {"from_attributes": True}
    id: UUID
    tenant_id: UUID
    rating: int
    feedback: str | None
    is_public: bool
    routed_to_google: bool
    created_at: datetime


class ReviewListResponse(BaseModel):
    items: list[ReviewResponse]
    total: int


class ReputationDashboard(BaseModel):
    avg_rating: float
    total_reviews: int
    five_star_count: int
    routed_to_google: int
    pending_requests: int
    this_week_reviews: int
