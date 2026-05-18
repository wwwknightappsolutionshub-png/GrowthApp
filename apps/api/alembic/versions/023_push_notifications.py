"""Add push notification subscriptions and preferences.

Revision ID: 023_push_notifications
Revises: 022_adaptive_landing_pages
Create Date: 2026-05-18
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

from app.core.db_types import UUIDType

revision = "023_push_notifications"
down_revision = "022_adaptive_landing_pages"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "push_subscriptions",
        sa.Column("id", UUIDType(), nullable=False),
        sa.Column("tenant_id", UUIDType(), nullable=False),
        sa.Column("user_id", UUIDType(), nullable=False),
        sa.Column("endpoint", sa.Text(), nullable=False),
        sa.Column("p256dh", sa.Text(), nullable=False),
        sa.Column("auth", sa.Text(), nullable=False),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("endpoint", name="uq_push_subscriptions_endpoint"),
    )
    op.create_index(op.f("ix_push_subscriptions_tenant_id"), "push_subscriptions", ["tenant_id"])
    op.create_index(op.f("ix_push_subscriptions_user_id"), "push_subscriptions", ["user_id"])

    op.create_table(
        "notification_preferences",
        sa.Column("id", UUIDType(), nullable=False),
        sa.Column("tenant_id", UUIDType(), nullable=False),
        sa.Column("user_id", UUIDType(), nullable=False),
        sa.Column("kind", sa.String(length=50), nullable=False),
        sa.Column("in_app_enabled", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column("push_enabled", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "user_id", "kind", name="uq_notification_pref_user_kind"),
    )
    op.create_index(op.f("ix_notification_preferences_tenant_id"), "notification_preferences", ["tenant_id"])
    op.create_index(op.f("ix_notification_preferences_user_id"), "notification_preferences", ["user_id"])
    op.create_index(op.f("ix_notification_preferences_kind"), "notification_preferences", ["kind"])


def downgrade() -> None:
    op.drop_index(op.f("ix_notification_preferences_kind"), table_name="notification_preferences")
    op.drop_index(op.f("ix_notification_preferences_user_id"), table_name="notification_preferences")
    op.drop_index(op.f("ix_notification_preferences_tenant_id"), table_name="notification_preferences")
    op.drop_table("notification_preferences")
    op.drop_index(op.f("ix_push_subscriptions_user_id"), table_name="push_subscriptions")
    op.drop_index(op.f("ix_push_subscriptions_tenant_id"), table_name="push_subscriptions")
    op.drop_table("push_subscriptions")
