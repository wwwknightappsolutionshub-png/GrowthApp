"""Add adaptive landing pages CMS table.

Revision ID: 022_adaptive_landing_pages
Revises: 021_subscription_plan_is_active
Create Date: 2026-05-17
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

from app.core.db_types import JSONBType, UUIDType

revision = "022_adaptive_landing_pages"
down_revision = "021_subscription_plan_is_active"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "adaptive_landing_pages",
        sa.Column("id", UUIDType(), nullable=False),
        sa.Column("niche_id", sa.String(length=80), nullable=False),
        sa.Column("label", sa.String(length=180), nullable=False),
        sa.Column("data", JSONBType(), nullable=False),
        sa.Column("is_published", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column("updated_by_user_id", UUIDType(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_adaptive_landing_pages_niche_id"),
        "adaptive_landing_pages",
        ["niche_id"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_adaptive_landing_pages_niche_id"), table_name="adaptive_landing_pages")
    op.drop_table("adaptive_landing_pages")
