"""Staff profile: address and join date for enterprise roster."""
from alembic import op
import sqlalchemy as sa

revision = "030_staff_profile"
down_revision = "029_customer_profile"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("staff", sa.Column("address", sa.Text(), nullable=True))
    op.add_column("staff", sa.Column("joined_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column("staff", "joined_at")
    op.drop_column("staff", "address")
