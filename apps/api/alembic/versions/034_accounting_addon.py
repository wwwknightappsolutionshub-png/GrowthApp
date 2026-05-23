"""Accounting add-on: entitlements, expenses, recurring schedules, invoice/quote tracking.

Revision ID: 034_accounting_addon
Revises: 033_booking_widget_forms
"""
from alembic import op
import sqlalchemy as sa

from app.core.db_types import JSONBType, UUIDType

revision = "034_accounting_addon"
down_revision = "033_booking_widget_forms"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "tenant_addons",
        sa.Column("id", UUIDType, primary_key=True),
        sa.Column("tenant_id", UUIDType, sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("feature_code", sa.String(50), nullable=False),
        sa.Column("status", sa.String(30), nullable=False, server_default="active"),
        sa.Column("stripe_subscription_item_id", sa.String(255), nullable=True),
        sa.Column("stripe_checkout_session_id", sa.String(255), nullable=True),
        sa.Column("granted_by", UUIDType, sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("granted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("tenant_id", "feature_code", name="uq_tenant_addons_tenant_feature"),
    )
    op.create_index("ix_tenant_addons_tenant_id", "tenant_addons", ["tenant_id"])

    op.create_table(
        "tenant_accounting_settings",
        sa.Column("tenant_id", UUIDType, sa.ForeignKey("tenants.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("vat_scheme", sa.String(30), nullable=False, server_default="standard"),
        sa.Column("flat_rate_percent", sa.Integer, nullable=True),
        sa.Column("late_fee_enabled", sa.Boolean, nullable=False, server_default="0"),
        sa.Column("late_fee_percent", sa.Integer, nullable=False, server_default="0"),
        sa.Column("auto_invoice_on_booking_complete", sa.Boolean, nullable=False, server_default="1"),
        sa.Column("reminder_days", JSONBType, nullable=False, server_default="[7, 14]"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "expenses",
        sa.Column("id", UUIDType, primary_key=True),
        sa.Column("tenant_id", UUIDType, sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("customer_id", UUIDType, sa.ForeignKey("customers.id", ondelete="SET NULL"), nullable=True),
        sa.Column("deal_id", UUIDType, sa.ForeignKey("deals.id", ondelete="SET NULL"), nullable=True),
        sa.Column("booking_id", UUIDType, sa.ForeignKey("bookings.id", ondelete="SET NULL"), nullable=True),
        sa.Column("description", sa.String(500), nullable=False),
        sa.Column("amount_pence", sa.Integer, nullable=False),
        sa.Column("vat_rate", sa.Integer, nullable=False, server_default="20"),
        sa.Column("vat_pence", sa.Integer, nullable=False, server_default="0"),
        sa.Column("category", sa.String(80), nullable=False, server_default="general"),
        sa.Column("expense_date", sa.Date, nullable=False),
        sa.Column("receipt_url", sa.Text, nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_expenses_tenant_id", "expenses", ["tenant_id"])

    op.create_table(
        "recurring_invoice_schedules",
        sa.Column("id", UUIDType, primary_key=True),
        sa.Column("tenant_id", UUIDType, sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("customer_id", UUIDType, sa.ForeignKey("customers.id", ondelete="CASCADE"), nullable=False),
        sa.Column("deal_id", UUIDType, sa.ForeignKey("deals.id", ondelete="SET NULL"), nullable=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("interval_unit", sa.String(20), nullable=False, server_default="monthly"),
        sa.Column("interval_count", sa.Integer, nullable=False, server_default="1"),
        sa.Column("next_run_at", sa.Date, nullable=False),
        sa.Column("line_items", JSONBType, nullable=False, server_default="[]"),
        sa.Column("auto_charge", sa.Boolean, nullable=False, server_default="0"),
        sa.Column("auto_send", sa.Boolean, nullable=False, server_default="1"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_recurring_invoice_schedules_tenant_id", "recurring_invoice_schedules", ["tenant_id"])

    op.add_column("quotes", sa.Column("viewed_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("invoices", sa.Column("viewed_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("invoices", sa.Column("booking_id", UUIDType, sa.ForeignKey("bookings.id", ondelete="SET NULL"), nullable=True))
    op.add_column("invoices", sa.Column("last_reminder_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("invoices", sa.Column("currency", sa.String(10), nullable=False, server_default="gbp"))


def downgrade() -> None:
    op.drop_column("invoices", "currency")
    op.drop_column("invoices", "last_reminder_at")
    op.drop_column("invoices", "booking_id")
    op.drop_column("invoices", "viewed_at")
    op.drop_column("quotes", "viewed_at")
    op.drop_table("recurring_invoice_schedules")
    op.drop_table("expenses")
    op.drop_table("tenant_accounting_settings")
    op.drop_table("tenant_addons")
