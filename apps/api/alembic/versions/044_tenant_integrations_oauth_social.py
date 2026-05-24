"""Tenant-owned Google OAuth credentials + social webhook channels + sync logs.

Revision ID: 044_tenant_integrations_oauth_social
Revises: 043_loyalty_birthday_preferences
"""

from alembic import op
import sqlalchemy as sa

revision = "044_tenant_integrations_oauth_social"
down_revision = "043_loyalty_birthday_preferences"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "tenant_google_credentials",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("google_client_id", sa.String(length=512), nullable=False),
        sa.Column("google_client_secret_encrypted", sa.Text(), nullable=False),
        sa.Column("access_token_encrypted", sa.Text(), nullable=True),
        sa.Column("refresh_token_encrypted", sa.Text(), nullable=True),
        sa.Column("scopes", sa.Text(), nullable=True),
        sa.Column("redirect_uri", sa.String(length=1024), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("connected_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("status", sa.String(length=20), server_default="pending", nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", name="uq_tenant_google_credentials_tenant"),
    )
    op.create_index("ix_tenant_google_credentials_tenant_id", "tenant_google_credentials", ["tenant_id"])

    op.create_table(
        "tenant_social_channels",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("channel_type", sa.String(length=30), nullable=False),
        sa.Column("webhook_url", sa.String(length=1024), nullable=False),
        sa.Column("api_key", sa.String(length=64), nullable=False),
        sa.Column("api_secret_encrypted", sa.Text(), nullable=False),
        sa.Column("zapier_integration_key", sa.String(length=128), nullable=True),
        sa.Column("make_integration_key", sa.String(length=128), nullable=True),
        sa.Column("status", sa.String(length=20), server_default="pending", nullable=False),
        sa.Column("connected_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "channel_type", name="uq_tenant_social_channel_type"),
    )
    op.create_index("ix_tenant_social_channels_tenant_id", "tenant_social_channels", ["tenant_id"])

    op.create_table(
        "tenant_social_webhook_logs",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("channel_type", sa.String(length=30), nullable=False),
        sa.Column("incoming_payload", sa.JSON(), nullable=False),
        sa.Column("processed_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("status", sa.String(length=30), server_default="received", nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_tenant_social_webhook_logs_tenant_id", "tenant_social_webhook_logs", ["tenant_id"])

    op.create_table(
        "tenant_google_sync_logs",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("data_type", sa.String(length=30), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("synced_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("status", sa.String(length=30), server_default="success", nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_tenant_google_sync_logs_tenant_id", "tenant_google_sync_logs", ["tenant_id"])

    op.add_column(
        "tenants",
        sa.Column(
            "integrations_onboarding",
            sa.JSON(),
            server_default=sa.text("'{}'"),
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_column("tenants", "integrations_onboarding")
    op.drop_index("ix_tenant_google_sync_logs_tenant_id", table_name="tenant_google_sync_logs")
    op.drop_table("tenant_google_sync_logs")
    op.drop_index("ix_tenant_social_webhook_logs_tenant_id", table_name="tenant_social_webhook_logs")
    op.drop_table("tenant_social_webhook_logs")
    op.drop_index("ix_tenant_social_channels_tenant_id", table_name="tenant_social_channels")
    op.drop_table("tenant_social_channels")
    op.drop_index("ix_tenant_google_credentials_tenant_id", table_name="tenant_google_credentials")
    op.drop_table("tenant_google_credentials")
