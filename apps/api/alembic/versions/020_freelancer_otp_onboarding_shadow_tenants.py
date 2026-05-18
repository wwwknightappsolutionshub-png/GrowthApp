"""User onboarding/phone-verified flags + Tenant shadow-client fields + OTP/pending-signup tables.

Revision ID: 020_freelancer_otp_onboarding_shadow_tenants
Revises: 019
Create Date: 2026-05-13

This migration:
  * Adds users.phone_verified_at, users.onboarding_completed
  * Adds tenants.owner_user_id, tenants.is_managed_client, tenants.social_handles
  * Creates otp_codes (signup OTP storage)
  * Creates pending_signups (form-state during pre-registration OTP verification)
"""
from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "020_freelancer_otp_onboarding_shadow_tenants"
down_revision = "019"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # users — new columns
    with op.batch_alter_table("users") as batch:
        batch.add_column(sa.Column("phone_verified_at", sa.DateTime(timezone=True), nullable=True))
        batch.add_column(
            sa.Column(
                "onboarding_completed",
                sa.Boolean(),
                nullable=False,
                server_default=sa.text("0"),
            )
        )

    # tenants — shadow-client wiring
    with op.batch_alter_table("tenants") as batch:
        batch.add_column(sa.Column("owner_user_id", sa.String(length=36), nullable=True))
        batch.add_column(
            sa.Column(
                "is_managed_client",
                sa.Boolean(),
                nullable=False,
                server_default=sa.text("0"),
            )
        )
        batch.add_column(
            sa.Column(
                "social_handles",
                sa.JSON(),
                nullable=False,
                server_default=sa.text("'{}'"),
            )
        )
        batch.create_index("ix_tenants_owner_user_id", ["owner_user_id"])

    # otp_codes — short-lived verification codes
    op.create_table(
        "otp_codes",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("purpose", sa.String(length=40), nullable=False, index=True),
        sa.Column("destination", sa.String(length=255), nullable=False, index=True),
        sa.Column("channel", sa.String(length=20), nullable=False),  # email | sms | whatsapp
        sa.Column("code_hash", sa.String(length=128), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("max_attempts", sa.Integer(), nullable=False, server_default=sa.text("5")),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )

    # pending_signups — form state during pre-registration OTP verification
    op.create_table(
        "pending_signups",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("email", sa.String(length=255), nullable=False, index=True),
        sa.Column("phone", sa.String(length=50), nullable=False),
        sa.Column("user_type", sa.String(length=20), nullable=False),
        sa.Column("password_hash", sa.Text(), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("phone_channel_attempted", sa.String(length=20), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )


def downgrade() -> None:
    op.drop_table("pending_signups")
    op.drop_table("otp_codes")
    with op.batch_alter_table("tenants") as batch:
        batch.drop_index("ix_tenants_owner_user_id")
        batch.drop_column("social_handles")
        batch.drop_column("is_managed_client")
        batch.drop_column("owner_user_id")
    with op.batch_alter_table("users") as batch:
        batch.drop_column("onboarding_completed")
        batch.drop_column("phone_verified_at")
