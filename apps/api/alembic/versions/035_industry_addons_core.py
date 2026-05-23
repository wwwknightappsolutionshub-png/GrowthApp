"""Industry add-ons: tenant vertical profile.

Revision ID: 035_industry_addons_core
Revises: 034_accounting_addon
"""
from alembic import op
import sqlalchemy as sa

from app.core.db_types import JSONBType, UUIDType

revision = "035_industry_addons_core"
down_revision = "034_accounting_addon"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "tenant_industry_profile",
        sa.Column("tenant_id", UUIDType, sa.ForeignKey("tenants.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("vertical", sa.String(30), nullable=False, server_default="salon"),
        sa.Column("settings", JSONBType, nullable=False, server_default="{}"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("tenant_industry_profile")
