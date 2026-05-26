"""PWA engagement + white-label addon.

Revision ID: 048_pwa_engagement
Revises: 047_marketing_cms_tables
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

from app.core.db_types import UUIDType

revision = "048_pwa_engagement"
down_revision = "047_marketing_cms_tables"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("membership_rewards_opt_in", sa.Boolean(), nullable=False, server_default=sa.text("true")),
    )
    op.create_table(
        "pwa_engagement_emails",
        sa.Column("id", UUIDType(), nullable=False),
        sa.Column("tenant_id", UUIDType(), nullable=False),
        sa.Column("user_id", UUIDType(), nullable=False),
        sa.Column("kind", sa.String(length=40), nullable=False),
        sa.Column("sent_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "user_id", "kind", name="uq_pwa_engagement_once"),
    )
    op.create_index("ix_pwa_engagement_emails_tenant_id", "pwa_engagement_emails", ["tenant_id"])
    op.create_index("ix_pwa_engagement_emails_user_id", "pwa_engagement_emails", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_pwa_engagement_emails_user_id", table_name="pwa_engagement_emails")
    op.drop_index("ix_pwa_engagement_emails_tenant_id", table_name="pwa_engagement_emails")
    op.drop_table("pwa_engagement_emails")
    op.drop_column("users", "membership_rewards_opt_in")
