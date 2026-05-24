"""PWA install reminder tracking for Membership & Rewards signups.

Revision ID: 045_pwa_install_reminders
Revises: 044_tenant_integrations_oauth_social
"""

from alembic import op
import sqlalchemy as sa

revision = "045_pwa_install_reminders"
down_revision = "044_tenant_integrations_oauth_social"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "mr_pwa_install_reminders",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("audience", sa.String(length=20), nullable=False),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("customer_id", sa.UUID(), nullable=True),
        sa.Column("user_id", sa.UUID(), nullable=True),
        sa.Column("registered_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("reminder_30m_sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reminder_1h_sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reminder_3h_sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["customer_id"], ["customers.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_mr_pwa_install_reminders_tenant_id", "mr_pwa_install_reminders", ["tenant_id"])
    op.create_index("ix_mr_pwa_install_reminders_registered_at", "mr_pwa_install_reminders", ["registered_at"])


def downgrade() -> None:
    op.drop_index("ix_mr_pwa_install_reminders_registered_at", table_name="mr_pwa_install_reminders")
    op.drop_index("ix_mr_pwa_install_reminders_tenant_id", table_name="mr_pwa_install_reminders")
    op.drop_table("mr_pwa_install_reminders")
