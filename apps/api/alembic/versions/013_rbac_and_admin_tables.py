"""013_rbac_and_admin_tables

Revision ID: 013
Revises: 012
Create Date: 2026-05-12

Creates:
  - admin_roles
  - admin_activity_logs
  - comm_templates
  - broadcasts
  - system_logs
  - blocked_ips
  - system_settings
  - support_tickets
  - ticket_replies
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "013"
down_revision = "012"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "admin_roles",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(60), nullable=False, unique=True),
        sa.Column("permissions", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
    )

    op.create_table(
        "admin_activity_logs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("action", sa.String(120), nullable=False),
        sa.Column("resource_type", sa.String(60), nullable=True),
        sa.Column("resource_id", sa.String(36), nullable=True),
        sa.Column("ip_address", sa.String(50), nullable=True),
        sa.Column("extra_data", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
    )
    op.create_index("ix_admin_activity_logs_user_id", "admin_activity_logs", ["user_id"])

    op.create_table(
        "comm_templates",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("channel", sa.String(20), nullable=False),
        sa.Column("subject", sa.String(255), nullable=True),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
    )

    op.create_table(
        "broadcasts",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("channel", sa.String(20), nullable=False),
        sa.Column("template_id", sa.String(36), sa.ForeignKey("comm_templates.id", ondelete="SET NULL"), nullable=True),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("target_filter", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("recipient_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
    )

    op.create_table(
        "system_logs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("level", sa.String(20), nullable=False, server_default="info"),
        sa.Column("service", sa.String(60), nullable=True),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("extra_data", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
    )
    op.create_index("ix_system_logs_level", "system_logs", ["level"])
    op.create_index("ix_system_logs_service", "system_logs", ["service"])

    op.create_table(
        "blocked_ips",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("ip_address", sa.String(50), nullable=False, unique=True),
        sa.Column("reason", sa.Text(), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
    )

    op.create_table(
        "system_settings",
        sa.Column("key", sa.String(120), primary_key=True),
        sa.Column("value", sa.JSON(), nullable=True),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("is_secret", sa.Boolean(), nullable=False, server_default="0"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
    )

    op.create_table(
        "support_tickets",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), sa.ForeignKey("tenants.id", ondelete="SET NULL"), nullable=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("assigned_to", sa.String(36), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("subject", sa.String(255), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("priority", sa.String(20), nullable=False, server_default="normal"),
        sa.Column("status", sa.String(20), nullable=False, server_default="open"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
    )
    op.create_index("ix_support_tickets_status", "support_tickets", ["status"])
    op.create_index("ix_support_tickets_tenant_id", "support_tickets", ["tenant_id"])

    op.create_table(
        "ticket_replies",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("ticket_id", sa.String(36), sa.ForeignKey("support_tickets.id", ondelete="CASCADE"), nullable=False),
        sa.Column("author_id", sa.String(36), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("is_internal", sa.Boolean(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
    )
    op.create_index("ix_ticket_replies_ticket_id", "ticket_replies", ["ticket_id"])

    # Seed default RBAC roles
    import uuid
    from datetime import datetime
    op.bulk_insert(
        sa.table(
            "admin_roles",
            sa.column("id", sa.String),
            sa.column("name", sa.String),
            sa.column("permissions", sa.JSON),
            sa.column("description", sa.Text),
            sa.column("created_at", sa.DateTime),
        ),
        [
            {"id": str(uuid.uuid4()), "name": "super_admin", "permissions": ["*"], "description": "Full platform access", "created_at": datetime.utcnow()},
            {"id": str(uuid.uuid4()), "name": "admin", "permissions": ["tenants.*", "billing.*", "users.*"], "description": "General admin", "created_at": datetime.utcnow()},
            {"id": str(uuid.uuid4()), "name": "support", "permissions": ["support.*", "tenants.read"], "description": "Support agent", "created_at": datetime.utcnow()},
            {"id": str(uuid.uuid4()), "name": "scraper_manager", "permissions": ["scraper.*", "ai_engine.*"], "description": "Manages scraper and AI engine", "created_at": datetime.utcnow()},
            {"id": str(uuid.uuid4()), "name": "billing_manager", "permissions": ["billing.*"], "description": "Billing and plans", "created_at": datetime.utcnow()},
            {"id": str(uuid.uuid4()), "name": "marketplace_manager", "permissions": ["marketplace.*"], "description": "Lead marketplace", "created_at": datetime.utcnow()},
        ],
    )


def downgrade() -> None:
    op.drop_table("ticket_replies")
    op.drop_table("support_tickets")
    op.drop_table("system_settings")
    op.drop_table("blocked_ips")
    op.drop_table("system_logs")
    op.drop_table("broadcasts")
    op.drop_table("comm_templates")
    op.drop_table("admin_activity_logs")
    op.drop_table("admin_roles")
