"""Phase 3: Outreach engine tables

Revision ID: 006
Revises: 005
Create Date: 2026-05-11 23:30:00.000000

* Adds `outreach_campaigns`, `outreach_enrolments`, `outreach_sends` tables.
* Enables RLS on each (tenant-scoped).
* Adds helper indexes used by the dispatch worker.

Postgres-only.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "006"
down_revision: Union[str, None] = "005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


NEW_TENANT_TABLES = [
    "outreach_campaigns",
    "outreach_enrolments",
    "outreach_sends",
]


def _is_postgres() -> bool:
    return op.get_context().dialect.name == "postgresql"


def upgrade() -> None:
    if not _is_postgres():
        return

    op.create_table(
        "outreach_campaigns",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("kind", sa.String(20), nullable=False, server_default="sequence"),
        sa.Column("channels", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("audience", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("steps", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("status", sa.String(20), nullable=False, server_default="draft", index=True),
        sa.Column("scheduled_at", sa.DateTime(timezone=True)),
        sa.Column("started_at", sa.DateTime(timezone=True)),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column("paused_at", sa.DateTime(timezone=True)),
        sa.Column("enrolled_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("sent_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("replied_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("unsubscribed_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_by_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "outreach_enrolments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("campaign_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("outreach_campaigns.id", ondelete="CASCADE"),
                  nullable=False, index=True),
        sa.Column("customer_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("customers.id", ondelete="CASCADE"),
                  nullable=False, index=True),
        sa.Column("current_step", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("status", sa.String(20), nullable=False, server_default="active", index=True),
        sa.Column("next_run_at", sa.DateTime(timezone=True), index=True),
        sa.Column("last_sent_at", sa.DateTime(timezone=True)),
        sa.Column("replied_at", sa.DateTime(timezone=True)),
        sa.Column("unsubscribed_at", sa.DateTime(timezone=True)),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column("error_message", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index(
        "ix_outreach_enrolments_due",
        "outreach_enrolments",
        ["status", "next_run_at"],
    )
    op.create_index(
        "ix_outreach_enrolments_campaign_customer",
        "outreach_enrolments",
        ["campaign_id", "customer_id"],
        unique=True,
    )

    op.create_table(
        "outreach_sends",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("campaign_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("outreach_campaigns.id", ondelete="CASCADE"),
                  nullable=False, index=True),
        sa.Column("enrolment_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("outreach_enrolments.id", ondelete="CASCADE"),
                  nullable=False, index=True),
        sa.Column("step_index", sa.Integer(), nullable=False),
        sa.Column("channel", sa.String(20), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="sent"),
        sa.Column("provider_message_id", sa.String(255)),
        sa.Column("subject", sa.String(500)),
        sa.Column("body", sa.Text()),
        sa.Column("error_message", sa.Text()),
        sa.Column("opened_at", sa.DateTime(timezone=True)),
        sa.Column("sent_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, index=True),
    )

    # ── RLS for the new tenant-scoped tables ──────────────────────────────
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

    op.drop_table("outreach_sends")
    op.drop_index("ix_outreach_enrolments_campaign_customer", table_name="outreach_enrolments")
    op.drop_index("ix_outreach_enrolments_due", table_name="outreach_enrolments")
    op.drop_table("outreach_enrolments")
    op.drop_table("outreach_campaigns")
