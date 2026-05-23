"""Membership & Rewards add-on — tenant plans, points ledger, tiers, trial.

Revision ID: 039_membership_rewards_core
Revises: 038_invoice_recurrency_renewals
"""
from alembic import op
import sqlalchemy as sa

from app.core.db_types import JSONBType, UUIDType

revision = "039_membership_rewards_core"
down_revision = "038_invoice_recurrency_renewals"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "mr_tenant_settings",
        sa.Column("tenant_id", UUIDType, sa.ForeignKey("tenants.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("earn_rules", JSONBType, nullable=False, server_default="{}"),
        sa.Column("points_expire_days", sa.Integer, nullable=True),
        sa.Column("landing_slug", sa.String(80), nullable=False, server_default="memberships"),
        sa.Column("landing_published", sa.Boolean, nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "mr_membership_plans",
        sa.Column("id", UUIDType, primary_key=True),
        sa.Column("tenant_id", UUIDType, sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("billing_cycle", sa.String(20), nullable=False, server_default="monthly"),
        sa.Column("price_pence", sa.Integer, nullable=False, server_default="0"),
        sa.Column("included_services", JSONBType, nullable=False, server_default="[]"),
        sa.Column("discount_percent", sa.Integer, nullable=False, server_default="0"),
        sa.Column("rollover_enabled", sa.Boolean, nullable=False, server_default="0"),
        sa.Column("rollover_max_periods", sa.Integer, nullable=False, server_default="1"),
        sa.Column("cancellation_notice_days", sa.Integer, nullable=False, server_default="30"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="1"),
        sa.Column("sort_order", sa.Integer, nullable=False, server_default="0"),
        sa.Column("stripe_price_id", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_mr_membership_plans_tenant_active", "mr_membership_plans", ["tenant_id", "is_active"])

    op.create_table(
        "mr_customer_subscriptions",
        sa.Column("id", UUIDType, primary_key=True),
        sa.Column("tenant_id", UUIDType, sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("customer_id", UUIDType, sa.ForeignKey("customers.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("plan_id", UUIDType, sa.ForeignKey("mr_membership_plans.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("status", sa.String(30), nullable=False, server_default="active"),
        sa.Column("started_at", sa.Date, nullable=True),
        sa.Column("current_period_end", sa.Date, nullable=True),
        sa.Column("canceled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("usage_snapshot", JSONBType, nullable=False, server_default="{}"),
        sa.Column("stripe_subscription_id", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index(
        "ix_mr_customer_subscriptions_tenant_customer",
        "mr_customer_subscriptions",
        ["tenant_id", "customer_id"],
    )

    op.create_table(
        "mr_loyalty_tiers",
        sa.Column("id", UUIDType, primary_key=True),
        sa.Column("tenant_id", UUIDType, sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("code", sa.String(30), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("min_points_lifetime", sa.Integer, nullable=False, server_default="0"),
        sa.Column("benefits", JSONBType, nullable=False, server_default="[]"),
        sa.Column("sort_order", sa.Integer, nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("tenant_id", "code", name="uq_mr_loyalty_tiers_tenant_code"),
    )

    op.create_table(
        "mr_customer_loyalty",
        sa.Column("tenant_id", UUIDType, sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("customer_id", UUIDType, sa.ForeignKey("customers.id", ondelete="CASCADE"), nullable=False),
        sa.Column("points_balance", sa.Integer, nullable=False, server_default="0"),
        sa.Column("points_lifetime", sa.Integer, nullable=False, server_default="0"),
        sa.Column("tier_code", sa.String(30), nullable=False, server_default="bronze"),
        sa.Column("tier_updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("tenant_id", "customer_id", name="pk_mr_customer_loyalty"),
    )

    op.create_table(
        "mr_points_ledger",
        sa.Column("id", UUIDType, primary_key=True),
        sa.Column("tenant_id", UUIDType, sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("customer_id", UUIDType, sa.ForeignKey("customers.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("amount", sa.Integer, nullable=False),
        sa.Column("balance_after", sa.Integer, nullable=False),
        sa.Column("source", sa.String(50), nullable=False),
        sa.Column("reference_type", sa.String(50), nullable=True),
        sa.Column("reference_id", UUIDType, nullable=True),
        sa.Column("description", sa.String(500), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, index=True),
    )
    op.create_index("ix_mr_points_ledger_tenant_customer", "mr_points_ledger", ["tenant_id", "customer_id"])

    op.create_table(
        "mr_reward_catalog",
        sa.Column("id", UUIDType, primary_key=True),
        sa.Column("tenant_id", UUIDType, sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("points_cost", sa.Integer, nullable=False),
        sa.Column("reward_type", sa.String(30), nullable=False, server_default="discount"),
        sa.Column("config", JSONBType, nullable=False, server_default="{}"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="1"),
        sa.Column("stock_remaining", sa.Integer, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "mr_reward_redemptions",
        sa.Column("id", UUIDType, primary_key=True),
        sa.Column("tenant_id", UUIDType, sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("customer_id", UUIDType, sa.ForeignKey("customers.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("catalog_item_id", UUIDType, sa.ForeignKey("mr_reward_catalog.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("points_spent", sa.Integer, nullable=False),
        sa.Column("status", sa.String(30), nullable=False, server_default="pending"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "mr_trial_reminders",
        sa.Column("tenant_id", UUIDType, sa.ForeignKey("tenants.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("trial_started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("trial_ends_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("day3_email_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("day6_email_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("day6_modal_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("day15_winback_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("converted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("winback_discount_percent", sa.Integer, nullable=False, server_default="50"),
    )

    op.create_table(
        "mr_landing_config",
        sa.Column("tenant_id", UUIDType, sa.ForeignKey("tenants.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("meta_description", sa.Text, nullable=True),
        sa.Column("hero", JSONBType, nullable=False, server_default="{}"),
        sa.Column("benefits", JSONBType, nullable=False, server_default="[]"),
        sa.Column("cta_label", sa.String(120), nullable=False, server_default="Join Our Membership Program"),
        sa.Column("cta_href", sa.String(500), nullable=True),
        sa.Column("published", sa.Boolean, nullable=False, server_default="0"),
        sa.Column("auto_generated", sa.Boolean, nullable=False, server_default="1"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("mr_landing_config")
    op.drop_table("mr_trial_reminders")
    op.drop_table("mr_reward_redemptions")
    op.drop_table("mr_reward_catalog")
    op.drop_index("ix_mr_points_ledger_tenant_customer", table_name="mr_points_ledger")
    op.drop_table("mr_points_ledger")
    op.drop_table("mr_customer_loyalty")
    op.drop_table("mr_loyalty_tiers")
    op.drop_index("ix_mr_customer_subscriptions_tenant_customer", table_name="mr_customer_subscriptions")
    op.drop_table("mr_customer_subscriptions")
    op.drop_index("ix_mr_membership_plans_tenant_active", table_name="mr_membership_plans")
    op.drop_table("mr_membership_plans")
    op.drop_table("mr_tenant_settings")
