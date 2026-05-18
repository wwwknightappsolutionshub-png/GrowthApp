"""010 - CRM visit fields + lead requests + plan quota

Revision ID: 010
Revises: 009
Create Date: 2026-05-12
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "010"
down_revision = "009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── Customer visit & follow-up fields ─────────────────────────────────────
    with op.batch_alter_table("customers") as batch_op:
        batch_op.add_column(sa.Column("first_visit_date", sa.DateTime(timezone=True), nullable=True))
        batch_op.add_column(sa.Column("next_visit_date", sa.DateTime(timezone=True), nullable=True))
        batch_op.add_column(
            sa.Column(
                "requires_followup",
                sa.Boolean(),
                nullable=False,
                server_default=sa.text("false"),
            )
        )
        batch_op.add_column(sa.Column("followup_reminder_at", sa.DateTime(timezone=True), nullable=True))
        batch_op.add_column(sa.Column("special_comments", sa.Text(), nullable=True))

    # ── SubscriptionPlan – AI lead request quota ──────────────────────────────
    with op.batch_alter_table("subscription_plans") as batch_op:
        batch_op.add_column(
            sa.Column(
                "ai_lead_requests_per_month",
                sa.Integer(),
                nullable=False,
                server_default=sa.text("0"),
            )
        )

    # ── lead_requests table ───────────────────────────────────────────────────
    op.create_table(
        "lead_requests",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), sa.ForeignKey("tenants.id"), nullable=False, index=True),
        sa.Column("month_year", sa.String(7), nullable=False),
        sa.Column("requested_count", sa.Integer(), nullable=False),
        sa.Column("approved_count", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("tenant_notes", sa.Text(), nullable=True),
        sa.Column("admin_notes", sa.Text(), nullable=True),
        sa.Column("fulfilled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
    )

    # Postgres-only RLS / unique index
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute("ALTER TABLE lead_requests ENABLE ROW LEVEL SECURITY")
        op.execute(
            "CREATE POLICY tenant_isolation ON lead_requests "
            "USING (tenant_id::text = current_setting('app.current_tenant_id', true))"
        )
        op.create_index(
            "ix_lead_requests_tenant_month",
            "lead_requests",
            ["tenant_id", "month_year"],
        )


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute("DROP POLICY IF EXISTS tenant_isolation ON lead_requests")

    op.drop_table("lead_requests")

    with op.batch_alter_table("subscription_plans") as batch_op:
        batch_op.drop_column("ai_lead_requests_per_month")

    with op.batch_alter_table("customers") as batch_op:
        batch_op.drop_column("special_comments")
        batch_op.drop_column("followup_reminder_at")
        batch_op.drop_column("requires_followup")
        batch_op.drop_column("next_visit_date")
        batch_op.drop_column("first_visit_date")
