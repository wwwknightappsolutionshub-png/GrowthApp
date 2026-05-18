"""Phase 1: tasks, notifications, magic-link, API keys, RBAC

Revision ID: 004
Revises: 003
Create Date: 2026-05-11 21:00:00.000000

Adds the Phase 1 CustomerFlow AI schema in one migration:

  * ``tasks`` — kanban-style operational tasks
  * ``notifications`` — in-app notification feed
  * ``magic_link_tokens`` — passwordless sign-in tokens
  * ``api_keys`` — programmatic access keys
  * ``permission_templates`` — platform-wide RBAC defaults
  * ``tenant_permission_overrides`` — per-tenant grant/revoke deltas

Postgres-only. SQLite previews and the test suite use ``Base.metadata.
create_all()`` (see ``tests/conftest.py``) which produces the same schema
from the SQLAlchemy models. All tenant-scoped tables get RLS enabled with
the standard ``tenant_isolation`` policy.
"""
import json
import uuid
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "004"
down_revision: Union[str, None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


NEW_TENANT_TABLES = [
    "tasks",
    "notifications",
    "api_keys",
    "tenant_permission_overrides",
    "ai_usage_events",
]


def _is_postgres() -> bool:
    return op.get_context().dialect.name == "postgresql"


def upgrade() -> None:
    if not _is_postgres():
        # Tests + dev SQLite use Base.metadata.create_all() — skip migration.
        return

    # ── tasks ─────────────────────────────────────────────────────────────
    op.create_table(
        "tasks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("status", sa.String(20), nullable=False, server_default="todo", index=True),
        sa.Column("priority", sa.String(20), nullable=False, server_default="normal"),
        sa.Column("position", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("labels", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("related_type", sa.String(20), index=True),
        sa.Column("related_id", postgresql.UUID(as_uuid=True), index=True),
        sa.Column("assigned_user_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True),
        sa.Column("created_by_user_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("due_at", sa.DateTime(timezone=True), index=True),
        sa.Column("reminder_at", sa.DateTime(timezone=True), index=True),
        sa.Column("reminded_at", sa.DateTime(timezone=True)),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_tasks_tenant_status_position", "tasks", ["tenant_id", "status", "position"])

    # ── notifications ─────────────────────────────────────────────────────
    op.create_table(
        "notifications",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True),
        sa.Column("kind", sa.String(50), nullable=False, index=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("body", sa.Text()),
        sa.Column("link", sa.String(500)),
        sa.Column("extra", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("read_at", sa.DateTime(timezone=True)),
        sa.Column("archived_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, index=True),
    )
    op.create_index("ix_notifications_tenant_user", "notifications", ["tenant_id", "user_id"])

    # ── magic_link_tokens (NOT tenant-scoped — pre-auth) ───────────────────
    op.create_table(
        "magic_link_tokens",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(255), nullable=False, index=True),
        sa.Column("token_hash", sa.String(128), nullable=False, unique=True, index=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("next_path", sa.String(500)),
        sa.Column("issued_to_ip", sa.String(45)),
        sa.Column("issued_user_agent", sa.Text()),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True)),
        sa.Column("used_from_ip", sa.String(45)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_magic_link_tokens_expires_at", "magic_link_tokens", ["expires_at"])

    # ── api_keys ──────────────────────────────────────────────────────────
    op.create_table(
        "api_keys",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("prefix", sa.String(16), nullable=False, index=True),
        sa.Column("key_hash", sa.String(128), nullable=False, unique=True, index=True),
        sa.Column("scopes", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("last_used_at", sa.DateTime(timezone=True)),
        sa.Column("expires_at", sa.DateTime(timezone=True)),
        sa.Column("revoked_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # ── permission_templates (global) ────────────────────────────────────
    op.create_table(
        "permission_templates",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("role", sa.String(50), nullable=False, unique=True, index=True),
        sa.Column("permissions", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("description", sa.String(255)),
        sa.Column("is_system", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # ── ai_usage_events ──────────────────────────────────────────────────
    op.create_table(
        "ai_usage_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("tenants.id", ondelete="SET NULL"), nullable=True, index=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("purpose", sa.String(50), nullable=False, index=True),
        sa.Column("provider", sa.String(20), nullable=False),
        sa.Column("model", sa.String(100), nullable=False),
        sa.Column("input_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("output_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("cost_pence", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("latency_ms", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("fallback_depth", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("status", sa.String(20), nullable=False, server_default="success"),
        sa.Column("error_message", sa.Text()),
        sa.Column("extra", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, index=True),
    )
    op.create_index("ix_ai_usage_tenant_created", "ai_usage_events", ["tenant_id", "created_at"])

    # ── tenant_permission_overrides ──────────────────────────────────────
    op.create_table(
        "tenant_permission_overrides",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("role", sa.String(50), nullable=False, index=True),
        sa.Column("permission", sa.String(80), nullable=False),
        sa.Column("effect", sa.String(10), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("tenant_id", "role", "permission", "effect", name="uq_tpo_unique"),
    )

    # ── Seed default permission templates ────────────────────────────────
    from app.modules.rbac.models import DEFAULT_TEMPLATES

    conn = op.get_bind()
    for role, perms in DEFAULT_TEMPLATES.items():
        conn.execute(
            sa.text(
                "INSERT INTO permission_templates "
                "(id, role, permissions, description, is_system, created_at, updated_at) "
                "VALUES (:id, :role, CAST(:perms AS jsonb), :desc, TRUE, NOW(), NOW())"
            ),
            {
                "id": uuid.uuid4(),
                "role": role,
                "perms": json.dumps(list(perms)),
                "desc": f"Default permission template for {role}",
            },
        )

    # ── RLS on the new tenant-scoped tables ──────────────────────────────
    for table in NEW_TENANT_TABLES:
        op.execute(f'ALTER TABLE "{table}" ENABLE ROW LEVEL SECURITY;')
        op.execute(f'ALTER TABLE "{table}" FORCE ROW LEVEL SECURITY;')
        op.execute(f'DROP POLICY IF EXISTS tenant_isolation ON "{table}";')
        op.execute(f"""
            CREATE POLICY tenant_isolation ON "{table}"
            USING (
                current_setting('app.current_tenant', true) = ''
                OR current_setting('app.current_tenant', true) IS NULL
                OR "tenant_id"::text = current_setting('app.current_tenant', true)
            )
            WITH CHECK (
                current_setting('app.current_tenant', true) = ''
                OR current_setting('app.current_tenant', true) IS NULL
                OR "tenant_id"::text = current_setting('app.current_tenant', true)
            );
        """)


def downgrade() -> None:
    if not _is_postgres():
        return

    for table in NEW_TENANT_TABLES:
        op.execute(f'DROP POLICY IF EXISTS tenant_isolation ON "{table}";')
        op.execute(f'ALTER TABLE "{table}" NO FORCE ROW LEVEL SECURITY;')
        op.execute(f'ALTER TABLE "{table}" DISABLE ROW LEVEL SECURITY;')

    op.drop_table("tenant_permission_overrides")
    op.drop_table("permission_templates")
    op.drop_index("ix_ai_usage_tenant_created", table_name="ai_usage_events")
    op.drop_table("ai_usage_events")
    op.drop_table("api_keys")
    op.drop_index("ix_magic_link_tokens_expires_at", table_name="magic_link_tokens")
    op.drop_table("magic_link_tokens")
    op.drop_index("ix_notifications_tenant_user", table_name="notifications")
    op.drop_table("notifications")
    op.drop_index("ix_tasks_tenant_status_position", table_name="tasks")
    op.drop_table("tasks")
