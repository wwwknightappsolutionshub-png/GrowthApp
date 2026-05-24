"""Redemption fulfillment codes for in-store staff validation.

Revision ID: 042_loyalty_redemption_fulfillment
Revises: 041_loyalty_customer_portal
"""

from alembic import op
import sqlalchemy as sa

revision = "042_loyalty_redemption_fulfillment"
down_revision = "041_loyalty_customer_portal"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("mr_reward_redemptions", sa.Column("fulfillment_code", sa.String(16), nullable=True))
    op.add_column(
        "mr_reward_redemptions",
        sa.Column("code_expires_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "mr_reward_redemptions",
        sa.Column("fulfilled_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "ix_mr_reward_redemptions_fulfillment_code",
        "mr_reward_redemptions",
        ["fulfillment_code"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("ix_mr_reward_redemptions_fulfillment_code", table_name="mr_reward_redemptions")
    op.drop_column("mr_reward_redemptions", "fulfilled_at")
    op.drop_column("mr_reward_redemptions", "code_expires_at")
    op.drop_column("mr_reward_redemptions", "fulfillment_code")
