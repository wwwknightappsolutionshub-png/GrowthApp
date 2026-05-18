"""Phase 3: Landing pages

Revision ID: 007
Revises: 006
Create Date: 2026-05-11 23:55:00.000000

* Adds `landing_pages` table.
* Enables RLS for tenant isolation.

Postgres-only.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "007"
down_revision: Union[str, None] = "006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _is_postgres() -> bool:
    return op.get_context().dialect.name == "postgresql"


def upgrade() -> None:
    if not _is_postgres():
        return

    op.create_table(
        "landing_pages",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("slug", sa.String(120), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("meta_description", sa.String(400)),
        sa.Column("cover_image_url", sa.Text()),
        sa.Column("theme", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("sections", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("is_published", sa.Boolean(), nullable=False, server_default=sa.false(), index=True),
        sa.Column("published_at", sa.DateTime(timezone=True)),
        sa.Column("extra", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("ai_provider", sa.String(20)),
        sa.Column("ai_model", sa.String(100)),
        sa.Column("ai_prompt", sa.Text()),
        sa.Column("created_by_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint("tenant_id", "slug", name="uq_landing_pages_tenant_slug"),
    )

    op.execute('ALTER TABLE "landing_pages" ENABLE ROW LEVEL SECURITY;')
    op.execute('ALTER TABLE "landing_pages" FORCE ROW LEVEL SECURITY;')
    op.execute('DROP POLICY IF EXISTS tenant_isolation ON "landing_pages";')
    op.execute(
        """
        CREATE POLICY tenant_isolation ON "landing_pages"
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
        """
    )


def downgrade() -> None:
    if not _is_postgres():
        return
    op.execute('DROP POLICY IF EXISTS tenant_isolation ON "landing_pages";')
    op.execute('ALTER TABLE "landing_pages" NO FORCE ROW LEVEL SECURITY;')
    op.execute('ALTER TABLE "landing_pages" DISABLE ROW LEVEL SECURITY;')
    op.drop_table("landing_pages")
