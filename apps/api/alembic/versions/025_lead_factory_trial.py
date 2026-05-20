"""Lead factory pool, trial deliveries, scraper source catalog fields.

Revision ID: 025_lead_factory_trial
Revises: 024_google_business_integrations
Create Date: 2026-05-20
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

from app.core.db_types import UUIDType

revision = "025_lead_factory_trial"
down_revision = "024_google_business_integrations"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "ai_scraper_sources",
        sa.Column("source_platform", sa.String(length=40), nullable=False, server_default="directory"),
    )
    op.add_column(
        "ai_scraper_sources",
        sa.Column("postcode_prefix", sa.String(length=12), nullable=True),
    )
    op.add_column(
        "ai_scraper_sources",
        sa.Column("region_label", sa.String(length=120), nullable=True),
    )
    op.add_column(
        "ai_scraper_sources",
        sa.Column("is_catalog_default", sa.Boolean(), nullable=False, server_default=sa.text("0")),
    )

    op.add_column(
        "tenants",
        sa.Column("trial_reminder_sent_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table(
        "trial_lead_deliveries",
        sa.Column("id", UUIDType(), nullable=False),
        sa.Column("tenant_id", UUIDType(), nullable=False),
        sa.Column("marketplace_item_id", UUIDType(), nullable=False),
        sa.Column("pool_lead_id", UUIDType(), nullable=False),
        sa.Column("tenant_lead_id", UUIDType(), nullable=False),
        sa.Column("delivered_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["marketplace_item_id"], ["lead_marketplace.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["pool_lead_id"], ["leads.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tenant_lead_id"], ["leads.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("marketplace_item_id", name="uq_trial_delivery_marketplace_item"),
        sa.UniqueConstraint("tenant_lead_id", name="uq_trial_delivery_tenant_lead"),
    )
    op.create_index(op.f("ix_trial_lead_deliveries_tenant_id"), "trial_lead_deliveries", ["tenant_id"])
    op.create_index(
        "ix_trial_lead_deliveries_tenant_delivered",
        "trial_lead_deliveries",
        ["tenant_id", "delivered_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_trial_lead_deliveries_tenant_delivered", table_name="trial_lead_deliveries")
    op.drop_index(op.f("ix_trial_lead_deliveries_tenant_id"), table_name="trial_lead_deliveries")
    op.drop_table("trial_lead_deliveries")
    op.drop_column("tenants", "trial_reminder_sent_at")
    op.drop_column("ai_scraper_sources", "is_catalog_default")
    op.drop_column("ai_scraper_sources", "region_label")
    op.drop_column("ai_scraper_sources", "postcode_prefix")
    op.drop_column("ai_scraper_sources", "source_platform")
