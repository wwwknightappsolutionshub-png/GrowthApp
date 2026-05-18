"""018 – FreelancerBilling: decimal price + calculation_source.

Revision ID: 018
Revises: 017
Create Date: 2026-05-13
"""

from alembic import op
import sqlalchemy as sa


revision = "018"
down_revision = "017"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    dialect = bind.dialect.name

    op.add_column(
        "freelancer_billings",
        sa.Column(
            "calculation_source",
            sa.String(length=20),
            nullable=False,
            server_default="auto",
        ),
    )

    if dialect == "postgresql":
        op.alter_column(
            "freelancer_billings",
            "calculated_price",
            existing_type=sa.Integer(),
            type_=sa.Numeric(10, 2),
            existing_nullable=False,
            postgresql_using="calculated_price::numeric(10,2)",
        )
    elif dialect == "sqlite":
        # SQLite uses dynamic type affinity; existing INTEGER values are read
        # back as Decimal by SQLAlchemy when the ORM column is Numeric(10, 2).
        # No physical alteration required.
        pass
    else:
        op.alter_column(
            "freelancer_billings",
            "calculated_price",
            existing_type=sa.Integer(),
            type_=sa.Numeric(10, 2),
            existing_nullable=False,
        )


def downgrade():
    bind = op.get_bind()
    dialect = bind.dialect.name

    if dialect == "postgresql":
        op.alter_column(
            "freelancer_billings",
            "calculated_price",
            existing_type=sa.Numeric(10, 2),
            type_=sa.Integer(),
            existing_nullable=False,
            postgresql_using="calculated_price::integer",
        )
    elif dialect != "sqlite":
        op.alter_column(
            "freelancer_billings",
            "calculated_price",
            existing_type=sa.Numeric(10, 2),
            type_=sa.Integer(),
            existing_nullable=False,
        )

    op.drop_column("freelancer_billings", "calculation_source")
