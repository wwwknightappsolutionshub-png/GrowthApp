"""Phase 2: AI columns (Lead.score etc.) + ai_assistant_messages

Revision ID: 005
Revises: 004
Create Date: 2026-05-11 22:00:00.000000

* Adds AI scoring columns to `leads`.
* Adds `ai_assistant_threads` and `ai_assistant_messages` for the AI assistant
  chat module (conversation history).
* Adds `customer_segments` for AI customer segmentation.
* Adds an `auto_replies` queue table for the inbound auto-reply agent.

Postgres-only.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "005"
down_revision: Union[str, None] = "004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


NEW_TENANT_TABLES = [
    "ai_assistant_threads",
    "ai_assistant_messages",
    "customer_segments",
    "auto_replies",
]


def _is_postgres() -> bool:
    return op.get_context().dialect.name == "postgresql"


def upgrade() -> None:
    if not _is_postgres():
        return

    # ── leads: AI scoring columns ───────────────────────────────────────
    op.add_column("leads", sa.Column("score", sa.Integer(), nullable=True))
    op.add_column("leads", sa.Column("score_label", sa.String(20), nullable=True))
    op.add_column("leads", sa.Column("score_reason", sa.Text(), nullable=True))
    op.add_column("leads", sa.Column("scored_at", sa.DateTime(timezone=True), nullable=True))
    op.create_index("ix_leads_score", "leads", ["score"])
    op.create_index("ix_leads_tenant_score", "leads", ["tenant_id", "score"])

    # ── ai_assistant_threads ────────────────────────────────────────────
    op.create_table(
        "ai_assistant_threads",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("title", sa.String(255), nullable=False, server_default="New conversation"),
        sa.Column("pinned", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("last_message_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("archived_at", sa.DateTime(timezone=True)),
    )

    # ── ai_assistant_messages ───────────────────────────────────────────
    op.create_table(
        "ai_assistant_messages",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("thread_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("ai_assistant_threads.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("role", sa.String(20), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("tool_calls", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("tool_call_id", sa.String(100)),
        sa.Column("provider", sa.String(20)),
        sa.Column("model", sa.String(100)),
        sa.Column("input_tokens", sa.Integer()),
        sa.Column("output_tokens", sa.Integer()),
        sa.Column("cost_pence", sa.Integer()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, index=True),
    )

    # ── customer_segments ──────────────────────────────────────────────
    op.create_table(
        "customer_segments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("rules", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("size", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("computed_at", sa.DateTime(timezone=True)),
        sa.Column("is_system", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_by_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # ── auto_replies ───────────────────────────────────────────────────
    op.create_table(
        "auto_replies",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("conversation_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("inbound_message_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("channel", sa.String(20), nullable=False),
        sa.Column("draft", sa.Text(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("rule", sa.String(100)),
        sa.Column("reviewed_by_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True)),
        sa.Column("sent_at", sa.DateTime(timezone=True)),
        sa.Column("provider", sa.String(20)),
        sa.Column("model", sa.String(100)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, index=True),
    )

    # ── RLS for the new tenant-scoped tables ───────────────────────────
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

    op.drop_table("auto_replies")
    op.drop_table("customer_segments")
    op.drop_table("ai_assistant_messages")
    op.drop_table("ai_assistant_threads")

    op.drop_index("ix_leads_tenant_score", table_name="leads")
    op.drop_index("ix_leads_score", table_name="leads")
    op.drop_column("leads", "scored_at")
    op.drop_column("leads", "score_reason")
    op.drop_column("leads", "score_label")
    op.drop_column("leads", "score")
