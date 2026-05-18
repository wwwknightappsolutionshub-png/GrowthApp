"""AI Scraper module: categories, sources, tasks, results, settings.

Revision ID: 009
Revises: 008
Create Date: 2026-05-12

Postgres-only — matches the pattern used by 007 and 008.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "009"
down_revision: Union[str, None] = "008"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _is_postgres() -> bool:
    return op.get_context().dialect.name == "postgresql"


def upgrade() -> None:
    if not _is_postgres():
        return

    op.create_table(
        "ai_scraper_categories",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(160), nullable=False, unique=True, index=True),
        sa.Column("description", sa.Text()),
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
    )

    op.create_table(
        "ai_scraper_sources",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False, index=True),
        sa.Column("url_pattern", sa.Text(), nullable=False),
        sa.Column("scraping_type", sa.String(20), nullable=False, server_default="html"),
        sa.Column(
            "category_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("ai_scraper_categories.id", ondelete="RESTRICT"),
            nullable=False,
            index=True,
        ),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("notes", sa.Text()),
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
    )

    op.create_table(
        "ai_scraper_tasks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "source_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("ai_scraper_sources.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "category_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("ai_scraper_categories.id", ondelete="RESTRICT"),
            nullable=False,
            index=True,
        ),
        sa.Column("aggression_level", sa.String(20), nullable=False, server_default="low"),
        sa.Column("frequency", sa.String(120), nullable=False),
        sa.Column("last_run", sa.DateTime(timezone=True)),
        sa.Column("next_run", sa.DateTime(timezone=True)),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending", index=True),
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
    )

    op.create_table(
        "ai_scraper_results",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "task_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("ai_scraper_tasks.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("raw_payload", sa.Text()),
        sa.Column("cleaned_payload", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("ai_extracted_data", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("ai_score", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("new_leads_created", sa.Integer(), nullable=False, server_default="0"),
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
    )

    op.create_table(
        "ai_scraper_settings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("thread_count", sa.Integer(), nullable=False, server_default="2"),
        sa.Column(
            "global_aggression_mode",
            sa.String(20),
            nullable=False,
            server_default="low",
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )


def downgrade() -> None:
    if not _is_postgres():
        return
    op.drop_table("ai_scraper_settings")
    op.drop_table("ai_scraper_results")
    op.drop_table("ai_scraper_tasks")
    op.drop_table("ai_scraper_sources")
    op.drop_table("ai_scraper_categories")
