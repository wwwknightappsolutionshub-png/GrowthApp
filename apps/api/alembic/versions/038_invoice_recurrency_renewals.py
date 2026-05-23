"""Invoice recurrency and customer service renewal tracking.

Revision ID: 038_invoice_recurrency_renewals
Revises: 037_invoice_payment_channel
"""
from alembic import op
import sqlalchemy as sa

from app.core.db_types import UUIDType

revision = "038_invoice_recurrency_renewals"
down_revision = "037_invoice_payment_channel"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("invoices", sa.Column("recurrency", sa.String(30), nullable=True))
    op.add_column("invoices", sa.Column("renewal_due_date", sa.Date(), nullable=True))
    op.add_column(
        "invoices",
        sa.Column("renewal_reminder_sent_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_invoices_renewal_due_date", "invoices", ["renewal_due_date"])

    op.add_column("customers", sa.Column("service_recurrency", sa.String(30), nullable=True))
    op.add_column("customers", sa.Column("service_renewal_date", sa.Date(), nullable=True))
    op.add_column(
        "customers",
        sa.Column("service_renewal_invoice_id", UUIDType, nullable=True),
    )


def downgrade() -> None:
    op.drop_column("customers", "service_renewal_invoice_id")
    op.drop_column("customers", "service_renewal_date")
    op.drop_column("customers", "service_recurrency")
    op.drop_index("ix_invoices_renewal_due_date", table_name="invoices")
    op.drop_column("invoices", "renewal_reminder_sent_at")
    op.drop_column("invoices", "renewal_due_date")
    op.drop_column("invoices", "recurrency")
