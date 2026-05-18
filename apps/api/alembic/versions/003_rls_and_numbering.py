"""Production hardening: row-level security, atomic numbering, unique constraints

Revision ID: 003
Revises: 002
Create Date: 2026-05-11 00:00:00.000000

This migration is PostgreSQL-only. It:

1. Enables Row-Level Security on every tenant-scoped table and installs a
   `tenant_isolation` policy keyed off the `app.current_tenant` GUC.
2. Adds atomic per-tenant numbering counters (`last_quote_number`,
   `last_invoice_number`) on the `tenants` table and a SQL function
   `next_tenant_number(tenant_id, kind)` that uses UPDATE ... RETURNING for
   race-free allocation.
3. Adds `(tenant_id, quote_number)` and `(tenant_id, invoice_number)` unique
   constraints as belt-and-braces.
4. Adds the composite hot-path indexes (tenant_id, status / stage / date).
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Tenant-scoped tables. We keep `tenant_members`, `subscription_plans`,
# `subscriptions`, `billing_invoices` and `audit_logs` here too — they all carry
# a tenant_id and benefit from RLS — except `subscription_plans` which is global.
TENANT_TABLES = [
    "tenants",
    "tenant_members",
    "locations",
    "subscriptions",
    "billing_invoices",
    "audit_logs",
    "lead_sources",
    "leads",
    "customers",
    "deals",
    "deal_activities",
    "staff",
    "availability_slots",
    "bookings",
    "quote_templates",
    "quotes",
    "invoices",
    "payments",
    "message_templates",
    "automations",
    "automation_runs",
    "conversations",
    "messages",
    "review_requests",
    "reviews",
    "social_accounts",
    "social_posts",
    "gdpr_requests",
]

# `tenants` is keyed on `id` rather than `tenant_id`.
TENANT_COLUMN_OVERRIDES = {"tenants": "id"}


def _is_postgres() -> bool:
    return op.get_context().dialect.name == "postgresql"


def upgrade() -> None:
    if not _is_postgres():
        # SQLite dev DB has no RLS and no `gen_random_uuid` — skip entirely.
        return

    # ── 1. Row-Level Security ─────────────────────────────────────────────
    for table in TENANT_TABLES:
        col = TENANT_COLUMN_OVERRIDES.get(table, "tenant_id")
        op.execute(f'ALTER TABLE "{table}" ENABLE ROW LEVEL SECURITY;')
        # FORCE means even table owners go through RLS — important because the
        # app DB user is typically the table owner.
        op.execute(f'ALTER TABLE "{table}" FORCE ROW LEVEL SECURITY;')
        op.execute(f'DROP POLICY IF EXISTS tenant_isolation ON "{table}";')
        op.execute(f"""
            CREATE POLICY tenant_isolation ON "{table}"
            USING (
                current_setting('app.current_tenant', true) = ''
                OR current_setting('app.current_tenant', true) IS NULL
                OR "{col}"::text = current_setting('app.current_tenant', true)
            )
            WITH CHECK (
                current_setting('app.current_tenant', true) = ''
                OR current_setting('app.current_tenant', true) IS NULL
                OR "{col}"::text = current_setting('app.current_tenant', true)
            );
        """)

    # ── 2. Atomic per-tenant numbering ────────────────────────────────────
    op.add_column("tenants", sa.Column("last_quote_number", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("tenants", sa.Column("last_invoice_number", sa.Integer(), nullable=False, server_default="0"))

    op.execute("""
        CREATE OR REPLACE FUNCTION next_tenant_number(p_tenant_id uuid, p_kind text)
        RETURNS integer
        LANGUAGE plpgsql
        AS $$
        DECLARE
            v_next integer;
        BEGIN
            IF p_kind = 'quote' THEN
                UPDATE tenants
                   SET last_quote_number = last_quote_number + 1
                 WHERE id = p_tenant_id
                RETURNING last_quote_number INTO v_next;
            ELSIF p_kind = 'invoice' THEN
                UPDATE tenants
                   SET last_invoice_number = last_invoice_number + 1
                 WHERE id = p_tenant_id
                RETURNING last_invoice_number INTO v_next;
            ELSE
                RAISE EXCEPTION 'unknown numbering kind: %', p_kind;
            END IF;
            IF v_next IS NULL THEN
                RAISE EXCEPTION 'tenant not found: %', p_tenant_id;
            END IF;
            RETURN v_next;
        END;
        $$;
    """)

    # Backfill existing tenants' counters from current max(quote_number) /
    # max(invoice_number) so already-issued numbers are never re-used.
    op.execute("""
        UPDATE tenants t SET last_quote_number = COALESCE(sub.maxnum, 0)
        FROM (
            SELECT tenant_id, MAX(NULLIF(regexp_replace(quote_number, '\\D','','g'), '')::int) AS maxnum
            FROM quotes GROUP BY tenant_id
        ) sub
        WHERE t.id = sub.tenant_id;
    """)
    op.execute("""
        UPDATE tenants t SET last_invoice_number = COALESCE(sub.maxnum, 0)
        FROM (
            SELECT tenant_id, MAX(NULLIF(regexp_replace(invoice_number, '\\D','','g'), '')::int) AS maxnum
            FROM invoices GROUP BY tenant_id
        ) sub
        WHERE t.id = sub.tenant_id;
    """)

    # ── 3. Unique constraints ─────────────────────────────────────────────
    op.create_unique_constraint("uq_quotes_tenant_number", "quotes", ["tenant_id", "quote_number"])
    op.create_unique_constraint("uq_invoices_tenant_number", "invoices", ["tenant_id", "invoice_number"])

    # ── 4. Hot-path composite indexes ─────────────────────────────────────
    op.create_index("ix_deals_tenant_stage", "deals", ["tenant_id", "stage"])
    op.create_index("ix_leads_tenant_status", "leads", ["tenant_id", "status"])
    op.create_index("ix_invoices_tenant_status", "invoices", ["tenant_id", "status"])
    op.create_index("ix_quotes_tenant_status", "quotes", ["tenant_id", "status"])
    op.create_index("ix_bookings_tenant_date", "bookings", ["tenant_id", "booking_date"])

    # Refresh-token rotation hygiene: index for sweep of expired tokens.
    op.create_index("ix_refresh_tokens_expires_at", "refresh_tokens", ["expires_at"])


def downgrade() -> None:
    if not _is_postgres():
        return

    op.drop_index("ix_refresh_tokens_expires_at", table_name="refresh_tokens")
    op.drop_index("ix_bookings_tenant_date", table_name="bookings")
    op.drop_index("ix_quotes_tenant_status", table_name="quotes")
    op.drop_index("ix_invoices_tenant_status", table_name="invoices")
    op.drop_index("ix_leads_tenant_status", table_name="leads")
    op.drop_index("ix_deals_tenant_stage", table_name="deals")

    op.drop_constraint("uq_invoices_tenant_number", "invoices", type_="unique")
    op.drop_constraint("uq_quotes_tenant_number", "quotes", type_="unique")

    op.execute("DROP FUNCTION IF EXISTS next_tenant_number(uuid, text);")
    op.drop_column("tenants", "last_invoice_number")
    op.drop_column("tenants", "last_quote_number")

    for table in TENANT_TABLES:
        op.execute(f'DROP POLICY IF EXISTS tenant_isolation ON "{table}";')
        op.execute(f'ALTER TABLE "{table}" NO FORCE ROW LEVEL SECURITY;')
        op.execute(f'ALTER TABLE "{table}" DISABLE ROW LEVEL SECURITY;')
