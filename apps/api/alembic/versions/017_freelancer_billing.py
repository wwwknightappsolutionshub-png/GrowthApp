"""017 – Freelancer subscription pricing snapshot.

Revision ID: 017
Revises: 016
Create Date: 2026-05-13
"""

from alembic import op
import sqlalchemy as sa


revision = "017"
down_revision = "016"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "freelancer_billings",
        sa.Column("id", sa.String(length=36), primary_key=True, nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False, unique=True),
        sa.Column("estimated_client_count", sa.Integer(), nullable=False),
        sa.Column("calculated_price", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
    )


def downgrade():
    op.drop_table("freelancer_billings")
