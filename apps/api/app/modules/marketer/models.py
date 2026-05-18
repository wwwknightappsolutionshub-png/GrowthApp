import uuid
from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base
from app.core.db_types import UUIDType, JSONBType


# ============================
# MARKETER TOOLS DB MODELS
# ============================

class MarketerFunnelBlueprint(Base):
    __tablename__ = "marketer_funnel_blueprints"
    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUIDType, ForeignKey("tenants.id"), nullable=False)
    funnel_type: Mapped[str | None] = mapped_column(String(100))
    steps_json: Mapped[list] = mapped_column(JSONBType, default=list)
    ai_notes: Mapped[str | None] = mapped_column(Text)


class AudienceResearchReport(Base):
    __tablename__ = "audience_research_reports"
    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUIDType, ForeignKey("tenants.id"), nullable=False)
    industry: Mapped[str | None] = mapped_column(String(100))
    demographics_json: Mapped[dict] = mapped_column(JSONBType, default=dict)
    pain_points_json: Mapped[list] = mapped_column(JSONBType, default=list)
    opportunities_json: Mapped[list] = mapped_column(JSONBType, default=list)


class CompetitorIntelligenceReport(Base):
    __tablename__ = "competitor_intelligence_reports"
    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUIDType, ForeignKey("tenants.id"), nullable=False)
    competitor_name: Mapped[str | None] = mapped_column(String(255))
    website: Mapped[str | None] = mapped_column(Text)
    strengths_json: Mapped[list] = mapped_column(JSONBType, default=list)
    weaknesses_json: Mapped[list] = mapped_column(JSONBType, default=list)
    pricing_json: Mapped[dict] = mapped_column(JSONBType, default=dict)


class MarketerQuota(Base):
    __tablename__ = "marketer_quotas"
    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUIDType, ForeignKey("tenants.id"), nullable=False)
    max_reports_per_month: Mapped[int] = mapped_column(Integer, default=5)
    used_reports: Mapped[int] = mapped_column(Integer, default=0)
