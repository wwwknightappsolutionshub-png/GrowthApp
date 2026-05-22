"""AI assistant thread session expiry and save flag."""
from alembic import op
import sqlalchemy as sa

revision = "031_ai_assistant_expiry"
down_revision = "030_staff_profile"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "ai_assistant_threads",
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "ai_assistant_threads",
        sa.Column("saved_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "ai_assistant_threads",
        sa.Column("save_reminder_sent_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.execute(
        sa.text(
            "UPDATE ai_assistant_threads SET expires_at = created_at + interval '48 hours' "
            "WHERE expires_at IS NULL"
        )
    )


def downgrade() -> None:
    op.drop_column("ai_assistant_threads", "save_reminder_sent_at")
    op.drop_column("ai_assistant_threads", "saved_at")
    op.drop_column("ai_assistant_threads", "expires_at")
