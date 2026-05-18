"""019 – FreelancerBilling.override_price (admin manual override).

Revision ID: 019
Revises: 018
Create Date: 2026-05-13
"""

from alembic import op
import sqlalchemy as sa


revision = "019"
down_revision = "018"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "freelancer_billings",
        sa.Column("override_price", sa.Numeric(10, 2), nullable=True),
    )


def downgrade():
    op.drop_column("freelancer_billings", "override_price")
