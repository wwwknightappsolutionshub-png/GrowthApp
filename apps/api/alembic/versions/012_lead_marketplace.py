"""012 - Lead Marketplace tables

Revision ID: 012
Revises: 011
Create Date: 2026-05-12

Creates:
    lead_categories
    lead_quality_rules
    lead_pricing
    lead_territories
    lead_marketplace
    lead_assignment_rules
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "012"
down_revision = "011"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "lead_categories",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(200), nullable=False, unique=True),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
    )
    op.create_index("ix_lead_categories_name", "lead_categories", ["name"])

    op.create_table(
        "lead_quality_rules",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("min_ai_score", sa.Integer, nullable=False, server_default="0"),
        sa.Column("max_age_days", sa.Integer, nullable=False, server_default="30"),
        sa.Column("requires_phone", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("requires_email", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("apply_to_category", sa.String(36), sa.ForeignKey("lead_categories.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
    )
    op.create_index("ix_lead_quality_rules_apply_to_category", "lead_quality_rules", ["apply_to_category"])

    op.create_table(
        "lead_pricing",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("category_id", sa.String(36), sa.ForeignKey("lead_categories.id", ondelete="CASCADE"), nullable=False),
        sa.Column("base_price", sa.Numeric(10, 2), nullable=False),
        sa.Column("high_quality_multiplier", sa.Numeric(6, 3), nullable=False, server_default="1.000"),
        sa.Column("exclusive_multiplier", sa.Numeric(6, 3), nullable=False, server_default="1.000"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
    )
    op.create_index("ix_lead_pricing_category_id", "lead_pricing", ["category_id"])

    op.create_table(
        "lead_territories",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("region_code", sa.String(20), nullable=False),
        sa.Column("country", sa.String(10), nullable=False, server_default="'GB'"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
    )
    op.create_index("ix_lead_territories_name", "lead_territories", ["name"])

    op.create_table(
        "lead_marketplace",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("lead_id", sa.String(36), sa.ForeignKey("leads.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("category_id", sa.String(36), sa.ForeignKey("lead_categories.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("territory_id", sa.String(36), sa.ForeignKey("lead_territories.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("ai_score", sa.Integer, nullable=False, server_default="0"),
        sa.Column("price", sa.Numeric(10, 2), nullable=False, server_default="0"),
        sa.Column("exclusivity", sa.String(20), nullable=False, server_default="'shared'"),
        sa.Column("status", sa.String(20), nullable=False, server_default="'available'"),
        sa.Column("assigned_tenant_id", sa.String(36), sa.ForeignKey("tenants.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
    )
    op.create_index("ix_lead_marketplace_lead_id", "lead_marketplace", ["lead_id"])
    op.create_index("ix_lead_marketplace_category_id", "lead_marketplace", ["category_id"])
    op.create_index("ix_lead_marketplace_territory_id", "lead_marketplace", ["territory_id"])
    op.create_index("ix_lead_marketplace_status", "lead_marketplace", ["status"])
    op.create_index("ix_lead_marketplace_assigned_tenant_id", "lead_marketplace", ["assigned_tenant_id"])

    op.create_table(
        "lead_assignment_rules",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("rule_name", sa.String(200), nullable=False),
        sa.Column("category_id", sa.String(36), sa.ForeignKey("lead_categories.id", ondelete="SET NULL"), nullable=True),
        sa.Column("territory_id", sa.String(36), sa.ForeignKey("lead_territories.id", ondelete="SET NULL"), nullable=True),
        sa.Column("min_subscription_level", sa.Integer, nullable=False, server_default="0"),
        sa.Column("priority_weight", sa.Integer, nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
    )
    op.create_index("ix_lead_assignment_rules_category_id", "lead_assignment_rules", ["category_id"])
    op.create_index("ix_lead_assignment_rules_territory_id", "lead_assignment_rules", ["territory_id"])

    # Enable RLS on PostgreSQL (no-op on SQLite)
    for tbl in (
        "lead_categories", "lead_quality_rules", "lead_pricing",
        "lead_territories", "lead_marketplace", "lead_assignment_rules",
    ):
        op.execute(
            sa.text(f"DO $$ BEGIN IF current_setting('server_version_num')::int >= 90500 THEN "
                    f"ALTER TABLE {tbl} ENABLE ROW LEVEL SECURITY; END IF; END $$;")
        )


def downgrade() -> None:
    op.drop_table("lead_assignment_rules")
    op.drop_table("lead_marketplace")
    op.drop_table("lead_territories")
    op.drop_table("lead_pricing")
    op.drop_table("lead_quality_rules")
    op.drop_table("lead_categories")
