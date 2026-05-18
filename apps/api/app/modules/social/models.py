import uuid
from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, String, Text, Boolean, Integer, func
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base
from app.core.db_types import UUIDType, JSONBType


class SocialAccount(Base):
    __tablename__ = "social_accounts"
    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUIDType, ForeignKey("tenants.id"), nullable=False)
    platform: Mapped[str] = mapped_column(String(30), nullable=False)
    account_id: Mapped[str] = mapped_column(String(255), nullable=False)
    page_id: Mapped[str | None] = mapped_column(String(255))
    access_token: Mapped[str | None] = mapped_column(Text)
    token_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class SocialPost(Base):
    __tablename__ = "social_posts"
    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUIDType, ForeignKey("tenants.id"), nullable=False, index=True)
    deal_id: Mapped[uuid.UUID | None] = mapped_column(UUIDType, ForeignKey("deals.id"), nullable=True)
    platform: Mapped[str] = mapped_column(String(30), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    image_urls: Mapped[list] = mapped_column(JSONBType, default=list)
    status: Mapped[str] = mapped_column(String(30), default="pending_approval")
    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    platform_post_id: Mapped[str | None] = mapped_column(String(255))
    error: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


# =======================
# AI SOCIAL MODULE MODELS
# =======================

class SocialBrandIdentity(Base):
    __tablename__ = "social_brand_identities"
    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUIDType, ForeignKey("tenants.id"), nullable=False)
    brand_colors: Mapped[dict] = mapped_column(JSONBType, default=dict)
    brand_fonts: Mapped[dict] = mapped_column(JSONBType, default=dict)
    tone_of_voice: Mapped[str | None] = mapped_column(String(100))
    logo_url: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class SocialSampleUploads(Base):
    __tablename__ = "social_sample_uploads"
    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUIDType, ForeignKey("tenants.id"), nullable=False)
    file_url: Mapped[str] = mapped_column(Text, nullable=False)
    file_type: Mapped[str] = mapped_column(String(10), nullable=False)  # IMAGE, VIDEO, PDF
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class SocialPostingPreferences(Base):
    __tablename__ = "social_posting_preferences"
    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUIDType, ForeignKey("tenants.id"), nullable=False)
    posts_per_week: Mapped[int] = mapped_column(Integer, default=3)
    preferred_days: Mapped[list] = mapped_column(JSONBType, default=list)
    preferred_time_range: Mapped[str | None] = mapped_column(String(50))


class SocialContentDraft(Base):
    __tablename__ = "social_content_drafts"
    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUIDType, ForeignKey("tenants.id"), nullable=False)
    text_content: Mapped[str | None] = mapped_column(Text)
    image_url: Mapped[str | None] = mapped_column(Text)
    ai_notes: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), default="PENDING")  # PENDING, APPROVED, REVISE
    scheduled_for: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class SocialApprovalQueue(Base):
    __tablename__ = "social_approval_queue"
    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUIDType, ForeignKey("tenants.id"), nullable=False)
    draft_id: Mapped[uuid.UUID] = mapped_column(UUIDType, ForeignKey("social_content_drafts.id"), nullable=False)
    delivery_channel: Mapped[str] = mapped_column(String(20), nullable=False)  # EMAIL, WHATSAPP
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    response_received: Mapped[bool] = mapped_column(Boolean, default=False)
    response_text: Mapped[str | None] = mapped_column(Text)


class SocialScheduleQueue(Base):
    __tablename__ = "social_schedule_queue"
    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUIDType, ForeignKey("tenants.id"), nullable=False)
    draft_id: Mapped[uuid.UUID] = mapped_column(UUIDType, ForeignKey("social_content_drafts.id"), nullable=False)
    platform: Mapped[str] = mapped_column(String(20), nullable=False)  # FB, IG, TIKTOK, TWITTER
    scheduled_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    posted_status: Mapped[str | None] = mapped_column(String(30))
