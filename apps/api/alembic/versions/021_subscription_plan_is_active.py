"""Add is_active to subscription plans.

Revision ID: 021_subscription_plan_is_active
Revises: 020_freelancer_otp_onboarding_shadow_tenants
Create Date: 2026-05-16
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "021_subscription_plan_is_active"
down_revision = "020_freelancer_otp_onboarding_shadow_tenants"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("subscription_plans") as batch:
        batch.add_column(
            sa.Column(
                "is_active",
                sa.Boolean(),
                nullable=False,
                server_default=sa.text("1"),
            )
        )


def downgrade() -> None:
    with op.batch_alter_table("subscription_plans") as batch:
        batch.drop_column("is_active")
