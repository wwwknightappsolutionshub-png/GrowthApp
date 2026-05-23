"""Drop legacy referrals tables and customer referral-program columns.

Revision ID: 040_drop_referrals_system
Revises: 039_membership_rewards_core
"""

from alembic import op
import sqlalchemy as sa

revision = "040_drop_referrals_system"
down_revision = "039_membership_rewards_core"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())

    if "customers" in tables:
        fks = {fk["name"] for fk in inspector.get_foreign_keys("customers")}
        if "fk_customers_referral_program_id" in fks:
            op.drop_constraint("fk_customers_referral_program_id", "customers", type_="foreignkey")
        cols = {c["name"] for c in inspector.get_columns("customers")}
        for col in ("referral_program_id", "reward_amount", "reward_type", "reward_delivery_method"):
            if col in cols:
                op.drop_column("customers", col)

    for table in ("referral_payouts", "referral_events", "referral_links", "referral_programs"):
        if table in tables:
            op.drop_table(table)


def downgrade() -> None:
    # Referrals module removed; downgrade not supported.
    pass
