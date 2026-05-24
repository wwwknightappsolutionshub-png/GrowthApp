"""Customer DOB, loyalty preferences, birthday & expiring reminder support.

Revision ID: 043_loyalty_birthday_preferences
Revises: 042_loyalty_redemption_fulfillment
"""

from alembic import op
import sqlalchemy as sa

revision = "043_loyalty_birthday_preferences"
down_revision = "042_loyalty_redemption_fulfillment"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("customers", sa.Column("date_of_birth", sa.Date(), nullable=True))

    op.create_table(
        "mr_customer_preferences",
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("customer_id", sa.UUID(), nullable=False),
        sa.Column("marketing_email", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("marketing_sms", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("birthday_participation", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("expiring_points_reminders", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("last_expiring_points_notice_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["customer_id"], ["customers.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("tenant_id", "customer_id"),
    )


def downgrade() -> None:
    op.drop_table("mr_customer_preferences")
    op.drop_column("customers", "date_of_birth")
