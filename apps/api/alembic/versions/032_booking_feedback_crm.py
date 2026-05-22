"""Booking feedback tokens and rating fields.

Revision ID: 032_booking_feedback
Revises: 031_ai_assistant_expiry
"""
from alembic import op
import sqlalchemy as sa

revision = "032_booking_feedback"
down_revision = "031_ai_assistant_expiry"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("bookings", sa.Column("feedback_token", sa.String(64), nullable=True))
    op.add_column("bookings", sa.Column("feedback_requested_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("bookings", sa.Column("feedback_submitted_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("bookings", sa.Column("service_rating", sa.Integer(), nullable=True))
    op.add_column("bookings", sa.Column("feedback_text", sa.Text(), nullable=True))
    op.create_index("ix_bookings_feedback_token", "bookings", ["feedback_token"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_bookings_feedback_token", table_name="bookings")
    op.drop_column("bookings", "feedback_text")
    op.drop_column("bookings", "service_rating")
    op.drop_column("bookings", "feedback_submitted_at")
    op.drop_column("bookings", "feedback_requested_at")
    op.drop_column("bookings", "feedback_token")
