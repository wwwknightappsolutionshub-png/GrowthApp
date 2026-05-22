"""Booking form templates, tenant overrides, customer referral fields.

Revision ID: 033_booking_widget_forms
Revises: 032_booking_feedback
"""
from alembic import op
import sqlalchemy as sa

from app.core.db_types import JSONBType, UUIDType

revision = "033_booking_widget_forms"
down_revision = "032_booking_feedback"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "booking_form_templates",
        sa.Column("category", sa.String(60), primary_key=True),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("schema", JSONBType, nullable=False, server_default="{}"),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("updated_by", UUIDType, nullable=True),
    )
    op.add_column(
        "booking_settings",
        sa.Column("booking_form_override", JSONBType, nullable=False, server_default="{}"),
    )
    op.add_column("customers", sa.Column("ref_count", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("customers", sa.Column("referral_program_id", UUIDType, nullable=True))
    op.add_column("customers", sa.Column("reward_amount", sa.Numeric(14, 2), nullable=True))
    op.add_column("customers", sa.Column("reward_type", sa.String(30), nullable=True))
    op.add_column("customers", sa.Column("reward_delivery_method", sa.String(30), nullable=True))
    op.create_foreign_key(
        "fk_customers_referral_program_id",
        "customers",
        "referral_programs",
        ["referral_program_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint("fk_customers_referral_program_id", "customers", type_="foreignkey")
    op.drop_column("customers", "reward_delivery_method")
    op.drop_column("customers", "reward_type")
    op.drop_column("customers", "reward_amount")
    op.drop_column("customers", "referral_program_id")
    op.drop_column("customers", "ref_count")
    op.drop_column("booking_settings", "booking_form_override")
    op.drop_table("booking_form_templates")
