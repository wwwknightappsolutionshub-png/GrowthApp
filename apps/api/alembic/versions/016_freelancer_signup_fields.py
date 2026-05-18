"""016 – Freelancer signup fields on users.

Revision ID: 016
Revises: 015
Create Date: 2026-05-13
"""

from alembic import op
import sqlalchemy as sa


revision = "016"
down_revision = "015"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "users",
        sa.Column(
            "user_type",
            sa.String(length=20),
            nullable=False,
            server_default="tenant",
        ),
    )
    op.add_column(
        "users",
        sa.Column("estimated_client_count", sa.Integer(), nullable=True),
    )


def downgrade():
    op.drop_column("users", "estimated_client_count")
    op.drop_column("users", "user_type")
