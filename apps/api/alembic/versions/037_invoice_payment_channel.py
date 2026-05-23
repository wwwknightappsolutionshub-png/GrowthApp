"""Add invoice payment_channel for cash-saved deposits view.

Revision ID: 037_invoice_payment_channel
Revises: 036_industry_salon_garage
"""
from alembic import op
import sqlalchemy as sa

revision = "037_invoice_payment_channel"
down_revision = "036_industry_salon_garage"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "invoices",
        sa.Column("payment_channel", sa.String(30), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("invoices", "payment_channel")
