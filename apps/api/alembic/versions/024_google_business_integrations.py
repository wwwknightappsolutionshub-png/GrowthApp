"""Google Business Profile OAuth and cached reviews.

Revision ID: 024_google_business_integrations
Revises: 023_push_notifications
Create Date: 2026-05-19
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

from app.core.db_types import JSONBType, UUIDType

revision = "024_google_business_integrations"
down_revision = "023_push_notifications"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "tenant_google_connections",
        sa.Column("id", UUIDType(), nullable=False),
        sa.Column("tenant_id", UUIDType(), nullable=False),
        sa.Column("google_account_name", sa.String(length=255), nullable=False),
        sa.Column("google_location_name", sa.String(length=255), nullable=True),
        sa.Column("location_title", sa.String(length=500), nullable=True),
        sa.Column("access_token_encrypted", sa.Text(), nullable=False),
        sa.Column("refresh_token_encrypted", sa.Text(), nullable=True),
        sa.Column("token_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("connection_metadata", JSONBType(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("connected_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("last_sync_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", name="uq_tenant_google_connections_tenant_id"),
    )
    op.create_index(
        op.f("ix_tenant_google_connections_tenant_id"),
        "tenant_google_connections",
        ["tenant_id"],
    )

    op.create_table(
        "google_business_reviews",
        sa.Column("id", UUIDType(), nullable=False),
        sa.Column("tenant_id", UUIDType(), nullable=False),
        sa.Column("google_review_name", sa.String(length=512), nullable=False),
        sa.Column("reviewer_display_name", sa.String(length=255), nullable=True),
        sa.Column("star_rating", sa.String(length=20), nullable=True),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("reply_comment", sa.Text(), nullable=True),
        sa.Column("review_created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reply_updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("raw_data", JSONBType(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("synced_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "google_review_name", name="uq_google_review_tenant_name"),
    )
    op.create_index(op.f("ix_google_business_reviews_tenant_id"), "google_business_reviews", ["tenant_id"])


def downgrade() -> None:
    op.drop_index(op.f("ix_google_business_reviews_tenant_id"), table_name="google_business_reviews")
    op.drop_table("google_business_reviews")
    op.drop_index(op.f("ix_tenant_google_connections_tenant_id"), table_name="tenant_google_connections")
    op.drop_table("tenant_google_connections")
