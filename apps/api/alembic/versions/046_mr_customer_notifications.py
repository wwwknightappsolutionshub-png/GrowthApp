"""In-app notifications for loyalty wallet customers.

Revision ID: 046_mr_customer_notifications
Revises: 045_pwa_install_reminders
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "046_mr_customer_notifications"
down_revision = "045_pwa_install_reminders"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "mr_customer_notifications",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("customer_id", sa.UUID(), nullable=False),
        sa.Column("kind", sa.String(length=50), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("body", sa.Text(), nullable=True),
        sa.Column("link", sa.String(length=500), nullable=True),
        sa.Column("extra", postgresql.JSONB(astext_type=sa.Text()), server_default="{}", nullable=False),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["customer_id"], ["customers.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_mr_customer_notifications_tenant_id",
        "mr_customer_notifications",
        ["tenant_id"],
    )
    op.create_index(
        "ix_mr_customer_notifications_customer_id",
        "mr_customer_notifications",
        ["customer_id"],
    )
    op.create_index(
        "ix_mr_customer_notifications_created_at",
        "mr_customer_notifications",
        ["created_at"],
    )
    op.create_index(
        "ix_mr_customer_notifications_kind",
        "mr_customer_notifications",
        ["kind"],
    )


def downgrade() -> None:
    op.drop_index("ix_mr_customer_notifications_kind", table_name="mr_customer_notifications")
    op.drop_index("ix_mr_customer_notifications_created_at", table_name="mr_customer_notifications")
    op.drop_index("ix_mr_customer_notifications_customer_id", table_name="mr_customer_notifications")
    op.drop_index("ix_mr_customer_notifications_tenant_id", table_name="mr_customer_notifications")
    op.drop_table("mr_customer_notifications")
