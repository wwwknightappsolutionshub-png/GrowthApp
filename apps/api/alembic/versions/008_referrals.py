"""Referral programs, links, events, payouts.

Revision ID: 008
Revises: 007
Create Date: 2026-05-12

Postgres-only (matches 007 pattern).
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "008"
down_revision: Union[str, None] = "007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _is_postgres() -> bool:
    return op.get_context().dialect.name == "postgresql"


def upgrade() -> None:
    if not _is_postgres():
        return

    op.create_table(
        "referral_programs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("type", sa.String(20), nullable=False, index=True),
        sa.Column(
            "owner_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
            index=True,
        ),
        sa.Column("reward_amount", sa.Numeric(14, 2), nullable=False, server_default="0"),
        sa.Column("reward_type", sa.String(30), nullable=False),
        sa.Column("reward_delivery_method", sa.String(30), nullable=False),
        sa.Column("rules", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("status", sa.String(20), nullable=False, server_default="disabled", index=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_table(
        "referral_links",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "program_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("referral_programs.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("ref_code", sa.String(64), nullable=False, unique=True, index=True),
        sa.Column("ref_link", sa.Text(), nullable=False),
        sa.Column("qr_code_url", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_table(
        "referral_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "referrer_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "referral_program_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("referral_programs.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "referred_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
            index=True,
        ),
        sa.Column("status", sa.String(30), nullable=False, server_default="clicked", index=True),
        sa.Column("reward_amount", sa.Numeric(14, 2), nullable=False, server_default="0"),
        sa.Column("reward_status", sa.String(20), nullable=False, server_default="pending", index=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_table(
        "referral_payouts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "event_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("referral_events.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "referrer_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("payout_method", sa.String(30), nullable=False),
        sa.Column("payout_status", sa.String(20), nullable=False, server_default="pending", index=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    if not _is_postgres():
        return
    op.drop_table("referral_payouts")
    op.drop_table("referral_events")
    op.drop_table("referral_links")
    op.drop_table("referral_programs")
