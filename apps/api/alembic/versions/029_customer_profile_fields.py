"""Customer profile: client type, business, upsell, reminders, events."""
from alembic import op
import sqlalchemy as sa

revision = "029_customer_profile"
down_revision = "028_crm_enterprise"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "customers",
        sa.Column("client_type", sa.String(20), nullable=False, server_default="individual"),
    )
    op.add_column("customers", sa.Column("business_name", sa.String(255), nullable=True))
    op.add_column("customers", sa.Column("upsell_date", sa.DateTime(timezone=True), nullable=True))
    op.add_column("customers", sa.Column("special_event", sa.Text(), nullable=True))
    op.add_column(
        "customers",
        sa.Column("needs_reminders", sa.Boolean(), nullable=False, server_default="false"),
    )


def downgrade() -> None:
    op.drop_column("customers", "needs_reminders")
    op.drop_column("customers", "special_event")
    op.drop_column("customers", "upsell_date")
    op.drop_column("customers", "business_name")
    op.drop_column("customers", "client_type")
