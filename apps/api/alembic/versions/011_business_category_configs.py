"""011 - business_category_configs table

Revision ID: 011
Revises: 010
Create Date: 2026-05-12
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "011"
down_revision = "010"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "business_category_configs",
        sa.Column("category", sa.String(60), primary_key=True),
        sa.Column("enabled_tools", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_by",
            sa.String(36),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_table("business_category_configs")
