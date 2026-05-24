"""Customer loyalty portal — credentials, magic links, QR tokens, push subs.

Revision ID: 041_loyalty_customer_portal
Revises: 040_drop_referrals_system
"""

from alembic import op
import sqlalchemy as sa

from app.core.db_types import JSONBType, UUIDType

revision = "041_loyalty_customer_portal"
down_revision = "040_drop_referrals_system"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "mr_customer_credentials",
        sa.Column("tenant_id", UUIDType, sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("customer_id", UUIDType, sa.ForeignKey("customers.id", ondelete="CASCADE"), nullable=False),
        sa.Column("password_hash", sa.Text, nullable=True),
        sa.Column("must_change_password", sa.Boolean, nullable=False, server_default="0"),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("tenant_id", "customer_id", name="pk_mr_customer_credentials"),
    )

    op.create_table(
        "mr_customer_magic_links",
        sa.Column("id", UUIDType, primary_key=True),
        sa.Column("tenant_id", UUIDType, sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("customer_id", UUIDType, sa.ForeignKey("customers.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("token_hash", sa.String(64), nullable=False, unique=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("used_from_ip", sa.String(45), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_mr_customer_magic_links_expires", "mr_customer_magic_links", ["expires_at"])

    op.create_table(
        "mr_customer_qr_tokens",
        sa.Column("id", UUIDType, primary_key=True),
        sa.Column("tenant_id", UUIDType, sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("customer_id", UUIDType, sa.ForeignKey("customers.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("token_hash", sa.String(64), nullable=False, unique=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index(
        "ix_mr_customer_qr_tokens_tenant_customer",
        "mr_customer_qr_tokens",
        ["tenant_id", "customer_id"],
    )

    op.create_table(
        "mr_qr_scan_events",
        sa.Column("id", UUIDType, primary_key=True),
        sa.Column("tenant_id", UUIDType, sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("customer_id", UUIDType, sa.ForeignKey("customers.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("staff_user_id", UUIDType, sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("qr_token_id", UUIDType, sa.ForeignKey("mr_customer_qr_tokens.id", ondelete="SET NULL"), nullable=True),
        sa.Column("points_awarded", sa.Integer, nullable=True),
        sa.Column("scanned_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "mr_customer_push_subscriptions",
        sa.Column("id", UUIDType, primary_key=True),
        sa.Column("tenant_id", UUIDType, sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("customer_id", UUIDType, sa.ForeignKey("customers.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("endpoint", sa.Text, nullable=False),
        sa.Column("p256dh", sa.String(255), nullable=False),
        sa.Column("auth", sa.String(255), nullable=False),
        sa.Column("user_agent", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("tenant_id", "customer_id", "endpoint", name="uq_mr_customer_push_endpoint"),
    )


def downgrade() -> None:
    op.drop_table("mr_customer_push_subscriptions")
    op.drop_table("mr_qr_scan_events")
    op.drop_table("mr_customer_qr_tokens")
    op.drop_table("mr_customer_magic_links")
    op.drop_table("mr_customer_credentials")
