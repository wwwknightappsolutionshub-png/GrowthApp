"""Tenant business site publish fields + primary landing page link.

Revision ID: 027_tenant_business_site
Revises: 026_enterprise_booking
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

from app.core.db_types import UUIDType

revision = "027_tenant_business_site"
down_revision = "026_enterprise_booking"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("tenants", sa.Column("primary_landing_page_id", UUIDType, nullable=True))
    op.add_column(
        "tenants",
        sa.Column("business_site_published", sa.Boolean(), nullable=False, server_default="false"),
    )
    op.add_column(
        "tenants",
        sa.Column("business_site_published_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_tenants_primary_landing_page",
        "tenants",
        "landing_pages",
        ["primary_landing_page_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint("fk_tenants_primary_landing_page", "tenants", type_="foreignkey")
    op.drop_column("tenants", "business_site_published_at")
    op.drop_column("tenants", "business_site_published")
    op.drop_column("tenants", "primary_landing_page_id")
