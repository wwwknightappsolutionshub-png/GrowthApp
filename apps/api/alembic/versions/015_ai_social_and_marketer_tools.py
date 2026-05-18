"""015 – AI Social module and Marketer Tools tables.

Revision ID: 015
Revises: 014
Create Date: 2026-05-13
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "015"
down_revision = "014"
branch_labels = None
depends_on = None


def get_json_type():
    try:
        return postgresql.JSONB()
    except Exception:
        return sa.JSON()


def upgrade():
    json_type = get_json_type()

    # ── AI Social Module ───────────────────────────────────────────────

    op.create_table(
        "social_brand_identities",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("brand_colors", json_type, nullable=True),
        sa.Column("brand_fonts", json_type, nullable=True),
        sa.Column("tone_of_voice", sa.String(100), nullable=True),
        sa.Column("logo_url", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "social_sample_uploads",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("file_url", sa.Text, nullable=False),
        sa.Column("file_type", sa.String(10), nullable=False),
        sa.Column("uploaded_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "social_posting_preferences",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("posts_per_week", sa.Integer, nullable=False, server_default="3"),
        sa.Column("preferred_days", json_type, nullable=True),
        sa.Column("preferred_time_range", sa.String(50), nullable=True),
    )

    op.create_table(
        "social_content_drafts",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("text_content", sa.Text, nullable=True),
        sa.Column("image_url", sa.Text, nullable=True),
        sa.Column("ai_notes", sa.Text, nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="PENDING"),
        sa.Column("scheduled_for", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "social_approval_queue",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("draft_id", sa.String(36), sa.ForeignKey("social_content_drafts.id"), nullable=False),
        sa.Column("delivery_channel", sa.String(20), nullable=False),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("response_received", sa.Boolean, nullable=False, server_default="0"),
        sa.Column("response_text", sa.Text, nullable=True),
    )

    op.create_table(
        "social_schedule_queue",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("draft_id", sa.String(36), sa.ForeignKey("social_content_drafts.id"), nullable=False),
        sa.Column("platform", sa.String(20), nullable=False),
        sa.Column("scheduled_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("posted_status", sa.String(30), nullable=True),
    )

    # ── Marketer Tools ─────────────────────────────────────────────────

    op.create_table(
        "marketer_funnel_blueprints",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("funnel_type", sa.String(100), nullable=True),
        sa.Column("steps_json", json_type, nullable=True),
        sa.Column("ai_notes", sa.Text, nullable=True),
    )

    op.create_table(
        "audience_research_reports",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("industry", sa.String(100), nullable=True),
        sa.Column("demographics_json", json_type, nullable=True),
        sa.Column("pain_points_json", json_type, nullable=True),
        sa.Column("opportunities_json", json_type, nullable=True),
    )

    op.create_table(
        "competitor_intelligence_reports",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("competitor_name", sa.String(255), nullable=True),
        sa.Column("website", sa.Text, nullable=True),
        sa.Column("strengths_json", json_type, nullable=True),
        sa.Column("weaknesses_json", json_type, nullable=True),
        sa.Column("pricing_json", json_type, nullable=True),
    )

    op.create_table(
        "marketer_quotas",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("max_reports_per_month", sa.Integer, nullable=False, server_default="5"),
        sa.Column("used_reports", sa.Integer, nullable=False, server_default="0"),
    )


def downgrade():
    op.drop_table("marketer_quotas")
    op.drop_table("competitor_intelligence_reports")
    op.drop_table("audience_research_reports")
    op.drop_table("marketer_funnel_blueprints")
    op.drop_table("social_schedule_queue")
    op.drop_table("social_approval_queue")
    op.drop_table("social_content_drafts")
    op.drop_table("social_posting_preferences")
    op.drop_table("social_sample_uploads")
    op.drop_table("social_brand_identities")
