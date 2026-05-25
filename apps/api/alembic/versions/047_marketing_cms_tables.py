"""Add marketing CMS tables (sections, reviews, landing templates).

Revision ID: 047_marketing_cms_tables
Revises: 046_mr_customer_notifications
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

from app.core.db_types import JSONBType, UUIDType

revision = "047_marketing_cms_tables"
down_revision = "046_mr_customer_notifications"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "marketing_sections",
        sa.Column("id", UUIDType(), nullable=False),
        sa.Column("key", sa.String(length=64), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("data", JSONBType(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("is_published", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("updated_by_user_id", UUIDType(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_marketing_sections_key"), "marketing_sections", ["key"], unique=True)

    op.create_table(
        "marketing_reviews",
        sa.Column("id", UUIDType(), nullable=False),
        sa.Column("author_name", sa.String(length=120), nullable=False),
        sa.Column("author_role", sa.String(length=180), nullable=True),
        sa.Column("author_location", sa.String(length=120), nullable=True),
        sa.Column("author_email", sa.String(length=255), nullable=True),
        sa.Column("author_company", sa.String(length=180), nullable=True),
        sa.Column("rating", sa.Integer(), nullable=False, server_default=sa.text("5")),
        sa.Column("quote", sa.Text(), nullable=False),
        sa.Column("quote_raw", sa.Text(), nullable=False),
        sa.Column("metric", sa.String(length=180), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="approved"),
        sa.Column("is_featured", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("is_carousel", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("sanitised", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("gmb_status", sa.String(length=20), nullable=False, server_default="not_pushed"),
        sa.Column("gmb_pushed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("gmb_url", sa.String(length=500), nullable=True),
        sa.Column("trustpilot_status", sa.String(length=20), nullable=False, server_default="not_pushed"),
        sa.Column("trustpilot_pushed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("trustpilot_url", sa.String(length=500), nullable=True),
        sa.Column("capture_source", sa.String(length=40), nullable=False, server_default="exit_intent"),
        sa.Column("referrer_url", sa.String(length=500), nullable=True),
        sa.Column("user_agent", sa.String(length=500), nullable=True),
        sa.Column("ip_address", sa.String(length=45), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_marketing_reviews_status"), "marketing_reviews", ["status"], unique=False)

    op.create_table(
        "landing_page_templates",
        sa.Column("id", UUIDType(), nullable=False),
        sa.Column("slug", sa.String(length=80), nullable=False),
        sa.Column("name", sa.String(length=180), nullable=False),
        sa.Column("niche", sa.String(length=40), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("preview_image_url", sa.String(length=500), nullable=True),
        sa.Column("theme", JSONBType(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("sections", JSONBType(), nullable=False, server_default=sa.text("'[]'")),
        sa.Column("is_published", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_landing_page_templates_slug"), "landing_page_templates", ["slug"], unique=True)
    op.create_index(op.f("ix_landing_page_templates_niche"), "landing_page_templates", ["niche"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_landing_page_templates_niche"), table_name="landing_page_templates")
    op.drop_index(op.f("ix_landing_page_templates_slug"), table_name="landing_page_templates")
    op.drop_table("landing_page_templates")
    op.drop_index(op.f("ix_marketing_reviews_status"), table_name="marketing_reviews")
    op.drop_table("marketing_reviews")
    op.drop_index(op.f("ix_marketing_sections_key"), table_name="marketing_sections")
    op.drop_table("marketing_sections")
