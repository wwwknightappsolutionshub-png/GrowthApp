"""CRM enterprise: pipelines, stages, tags, activities, custom fields, imports.

Revision ID: 028_crm_enterprise
Revises: 027_tenant_business_site
"""
from __future__ import annotations

import uuid

import sqlalchemy as sa
from alembic import op

from app.core.db_types import JSONBType, UUIDType

revision = "028_crm_enterprise"
down_revision = "027_tenant_business_site"
branch_labels = None
depends_on = None

DEFAULT_STAGES = (
    ("New", 0, False, False),
    ("Contacted", 1, False, False),
    ("Quoted", 2, False, False),
    ("Booked", 3, False, False),
    ("Completed", 4, True, False),
    ("Lost", 5, False, True),
)

NEW_TENANT_TABLES = [
    "crm_pipelines",
    "crm_stages",
    "crm_assignments",
    "crm_custom_field_definitions",
    "crm_custom_field_values",
    "crm_tags",
    "crm_tag_assignments",
    "crm_attachments",
    "crm_activities",
    "crm_saved_filters",
    "crm_score_rules",
    "crm_import_jobs",
    "crm_duplicate_candidates",
]


def _is_postgres() -> bool:
    return op.get_context().dialect.name == "postgresql"


def _apply_rls() -> None:
    if not _is_postgres():
        return
    for table in NEW_TENANT_TABLES:
        op.execute(f'ALTER TABLE "{table}" ENABLE ROW LEVEL SECURITY;')
        op.execute(f'ALTER TABLE "{table}" FORCE ROW LEVEL SECURITY;')
        op.execute(f'DROP POLICY IF EXISTS tenant_isolation ON "{table}";')
        op.execute(f"""
            CREATE POLICY tenant_isolation ON "{table}"
            USING (
                current_setting('app.current_tenant', true) = ''
                OR current_setting('app.current_tenant', true) IS NULL
                OR tenant_id::text = current_setting('app.current_tenant', true)
            )
            WITH CHECK (
                current_setting('app.current_tenant', true) = ''
                OR current_setting('app.current_tenant', true) IS NULL
                OR tenant_id::text = current_setting('app.current_tenant', true)
            );
        """)


def _drop_rls() -> None:
    if not _is_postgres():
        return
    for table in NEW_TENANT_TABLES:
        op.execute(f'DROP POLICY IF EXISTS tenant_isolation ON "{table}";')
        op.execute(f'ALTER TABLE "{table}" NO FORCE ROW LEVEL SECURITY;')
        op.execute(f'ALTER TABLE "{table}" DISABLE ROW LEVEL SECURITY;')


def _backfill_default_pipelines() -> None:
    conn = op.get_bind()
    tenants = conn.execute(sa.text("SELECT id FROM tenants")).fetchall()
    for (tenant_id,) in tenants:
        tid = tenant_id if isinstance(tenant_id, uuid.UUID) else uuid.UUID(str(tenant_id))
        pipeline_id = uuid.uuid4()
        conn.execute(
            sa.text(
                """
                INSERT INTO crm_pipelines (id, tenant_id, name, description, is_default, is_active, created_at, updated_at)
                VALUES (:id, :tenant_id, 'Sales', NULL, true, true, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                """
            ),
            {"id": pipeline_id, "tenant_id": tid},
        )
        stage_by_name: dict[str, uuid.UUID] = {}
        for name, position, is_won, is_lost in DEFAULT_STAGES:
            stage_id = uuid.uuid4()
            stage_by_name[name] = stage_id
            conn.execute(
                sa.text(
                    """
                    INSERT INTO crm_stages (
                        id, tenant_id, pipeline_id, name, position, color, applies_to,
                        automation_event, is_won, is_lost, created_at
                    )
                    VALUES (
                        :id, :tenant_id, :pipeline_id, :name, :position, NULL, 'both',
                        NULL, :is_won, :is_lost, CURRENT_TIMESTAMP
                    )
                    """
                ),
                {
                    "id": stage_id,
                    "tenant_id": tid,
                    "pipeline_id": pipeline_id,
                    "name": name,
                    "position": position,
                    "is_won": is_won,
                    "is_lost": is_lost,
                },
            )

        new_stage_id = stage_by_name["New"]
        for stage_name, stage_id in stage_by_name.items():
            conn.execute(
                sa.text(
                    """
                    UPDATE deals
                    SET pipeline_id = :pipeline_id, stage_id = :stage_id
                    WHERE tenant_id = :tenant_id AND stage = :stage_name AND deleted_at IS NULL
                    """
                ),
                {
                    "pipeline_id": pipeline_id,
                    "stage_id": stage_id,
                    "tenant_id": tid,
                    "stage_name": stage_name,
                },
            )
        conn.execute(
            sa.text(
                """
                UPDATE deals
                SET pipeline_id = :pipeline_id, stage_id = :stage_id
                WHERE tenant_id = :tenant_id
                  AND (pipeline_id IS NULL OR stage_id IS NULL)
                  AND deleted_at IS NULL
                """
            ),
            {"pipeline_id": pipeline_id, "stage_id": new_stage_id, "tenant_id": tid},
        )
        conn.execute(
            sa.text(
                """
                UPDATE leads
                SET pipeline_id = :pipeline_id, stage_id = :stage_id, stage_order = 0
                WHERE tenant_id = :tenant_id AND deleted_at IS NULL
                """
            ),
            {"pipeline_id": pipeline_id, "stage_id": new_stage_id, "tenant_id": tid},
        )


def upgrade() -> None:
    # ── Pipelines & stages ────────────────────────────────────────────────────
    op.create_table(
        "crm_pipelines",
        sa.Column("id", UUIDType, primary_key=True),
        sa.Column("tenant_id", UUIDType, sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_default", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_crm_pipelines_tenant_id", "crm_pipelines", ["tenant_id"])

    op.create_table(
        "crm_stages",
        sa.Column("id", UUIDType, primary_key=True),
        sa.Column("tenant_id", UUIDType, sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("pipeline_id", UUIDType, sa.ForeignKey("crm_pipelines.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(80), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("color", sa.String(20), nullable=True),
        sa.Column("applies_to", sa.String(10), nullable=False, server_default="both"),
        sa.Column("automation_event", sa.String(80), nullable=True),
        sa.Column("is_won", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("is_lost", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_crm_stages_pipeline_position", "crm_stages", ["pipeline_id", "position"])
    op.create_index("ix_crm_stages_tenant_id", "crm_stages", ["tenant_id"])

    if _is_postgres():
        op.execute(
            """
            CREATE UNIQUE INDEX uq_crm_pipelines_tenant_default
            ON crm_pipelines (tenant_id)
            WHERE is_default = true
            """
        )

    # ── Alter leads / deals / customers / segments (batch for SQLite) ─────────
    with op.batch_alter_table("leads") as batch_op:
        batch_op.add_column(sa.Column("pipeline_id", UUIDType, nullable=True))
        batch_op.add_column(sa.Column("stage_id", UUIDType, nullable=True))
        batch_op.add_column(sa.Column("stage_order", sa.Integer(), nullable=False, server_default="0"))
        batch_op.add_column(sa.Column("assigned_user_id", UUIDType, nullable=True))
        batch_op.create_foreign_key("fk_leads_pipeline", "crm_pipelines", ["pipeline_id"], ["id"], ondelete="SET NULL")
        batch_op.create_foreign_key("fk_leads_stage", "crm_stages", ["stage_id"], ["id"], ondelete="SET NULL")
        batch_op.create_foreign_key("fk_leads_assigned_user", "users", ["assigned_user_id"], ["id"], ondelete="SET NULL")

    with op.batch_alter_table("deals") as batch_op:
        batch_op.add_column(sa.Column("pipeline_id", UUIDType, nullable=True))
        batch_op.add_column(sa.Column("stage_id", UUIDType, nullable=True))
        batch_op.create_foreign_key("fk_deals_pipeline", "crm_pipelines", ["pipeline_id"], ["id"], ondelete="SET NULL")
        batch_op.create_foreign_key("fk_deals_stage", "crm_stages", ["stage_id"], ["id"], ondelete="SET NULL")

    with op.batch_alter_table("customers") as batch_op:
        batch_op.add_column(sa.Column("assigned_user_id", UUIDType, nullable=True))
        batch_op.create_foreign_key(
            "fk_customers_assigned_user", "users", ["assigned_user_id"], ["id"], ondelete="SET NULL"
        )

    op.create_index("ix_leads_tenant_pipeline_stage", "leads", ["tenant_id", "pipeline_id", "stage_id"])
    op.create_index("ix_leads_stage_order", "leads", ["tenant_id", "stage_id", "stage_order"])
    op.create_index("ix_deals_tenant_pipeline_stage", "deals", ["tenant_id", "pipeline_id", "stage_id"])
    op.create_index("ix_deals_stage_order", "deals", ["tenant_id", "stage_id", "stage_order"])
    op.create_index("ix_customers_assigned_user", "customers", ["assigned_user_id"])

    with op.batch_alter_table("customer_segments") as batch_op:
        batch_op.add_column(
            sa.Column("entity_type", sa.String(20), nullable=False, server_default="customer"),
        )

    # ── Supporting CRM tables ─────────────────────────────────────────────────
    op.create_table(
        "crm_assignments",
        sa.Column("id", UUIDType, primary_key=True),
        sa.Column("tenant_id", UUIDType, sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("entity_type", sa.String(20), nullable=False),
        sa.Column("entity_id", UUIDType, nullable=False),
        sa.Column("user_id", UUIDType, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("role", sa.String(30), nullable=False, server_default="collaborator"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("tenant_id", "entity_type", "entity_id", "user_id", name="uq_crm_assignment_entity_user"),
    )
    op.create_index("ix_crm_assignments_entity", "crm_assignments", ["tenant_id", "entity_type", "entity_id"])

    op.create_table(
        "crm_custom_field_definitions",
        sa.Column("id", UUIDType, primary_key=True),
        sa.Column("tenant_id", UUIDType, sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("entity_type", sa.String(20), nullable=False),
        sa.Column("field_key", sa.String(64), nullable=False),
        sa.Column("label", sa.String(120), nullable=False),
        sa.Column("field_type", sa.String(20), nullable=False, server_default="text"),
        sa.Column("options", JSONBType, nullable=False, server_default="{}"),
        sa.Column("is_required", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("position", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("tenant_id", "entity_type", "field_key", name="uq_crm_field_def_key"),
    )

    op.create_table(
        "crm_custom_field_values",
        sa.Column("id", UUIDType, primary_key=True),
        sa.Column("tenant_id", UUIDType, sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column(
            "definition_id",
            UUIDType,
            sa.ForeignKey("crm_custom_field_definitions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("entity_type", sa.String(20), nullable=False),
        sa.Column("entity_id", UUIDType, nullable=False),
        sa.Column("value_text", sa.Text(), nullable=True),
        sa.Column("value_number", sa.Numeric(18, 4), nullable=True),
        sa.Column("value_bool", sa.Boolean(), nullable=True),
        sa.Column("value_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("value_json", JSONBType, nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("definition_id", "entity_id", name="uq_crm_field_value_entity"),
    )
    op.create_index("ix_crm_field_values_entity", "crm_custom_field_values", ["tenant_id", "entity_type", "entity_id"])

    op.create_table(
        "crm_tags",
        sa.Column("id", UUIDType, primary_key=True),
        sa.Column("tenant_id", UUIDType, sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(80), nullable=False),
        sa.Column("color", sa.String(20), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("tenant_id", "name", name="uq_crm_tag_name"),
    )

    op.create_table(
        "crm_tag_assignments",
        sa.Column("id", UUIDType, primary_key=True),
        sa.Column("tenant_id", UUIDType, sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("tag_id", UUIDType, sa.ForeignKey("crm_tags.id", ondelete="CASCADE"), nullable=False),
        sa.Column("entity_type", sa.String(20), nullable=False),
        sa.Column("entity_id", UUIDType, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("tag_id", "entity_type", "entity_id", name="uq_crm_tag_assignment"),
    )

    op.create_table(
        "crm_attachments",
        sa.Column("id", UUIDType, primary_key=True),
        sa.Column("tenant_id", UUIDType, sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("entity_type", sa.String(20), nullable=False),
        sa.Column("entity_id", UUIDType, nullable=False),
        sa.Column("uploaded_by_user_id", UUIDType, sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("file_name", sa.String(255), nullable=False),
        sa.Column("mime_type", sa.String(100), nullable=True),
        sa.Column("size_bytes", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("storage_path", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_crm_attachments_entity", "crm_attachments", ["tenant_id", "entity_type", "entity_id"])

    op.create_table(
        "crm_activities",
        sa.Column("id", UUIDType, primary_key=True),
        sa.Column("tenant_id", UUIDType, sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("entity_type", sa.String(20), nullable=False),
        sa.Column("entity_id", UUIDType, nullable=False),
        sa.Column("activity_type", sa.String(50), nullable=False),
        sa.Column("title", sa.String(255), nullable=True),
        sa.Column("body", sa.Text(), nullable=True),
        sa.Column("user_id", UUIDType, sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("metadata", JSONBType, nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index(
        "ix_crm_activities_entity_created",
        "crm_activities",
        ["tenant_id", "entity_type", "entity_id", "created_at"],
    )

    op.create_table(
        "crm_saved_filters",
        sa.Column("id", UUIDType, primary_key=True),
        sa.Column("tenant_id", UUIDType, sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", UUIDType, sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("entity_type", sa.String(20), nullable=False),
        sa.Column("rules", JSONBType, nullable=False, server_default="{}"),
        sa.Column("is_default", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )

    op.create_table(
        "crm_score_rules",
        sa.Column("id", UUIDType, primary_key=True),
        sa.Column("tenant_id", UUIDType, sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("priority", sa.Integer(), nullable=False, server_default="100"),
        sa.Column("conditions", JSONBType, nullable=False, server_default="{}"),
        sa.Column("points", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )

    op.create_table(
        "crm_import_jobs",
        sa.Column("id", UUIDType, primary_key=True),
        sa.Column("tenant_id", UUIDType, sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", UUIDType, sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("job_type", sa.String(20), nullable=False),
        sa.Column("entity_type", sa.String(20), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("file_path", sa.Text(), nullable=True),
        sa.Column("row_count", sa.Integer(), nullable=True),
        sa.Column("error_log", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table(
        "crm_duplicate_candidates",
        sa.Column("id", UUIDType, primary_key=True),
        sa.Column("tenant_id", UUIDType, sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("entity_type", sa.String(20), nullable=False),
        sa.Column("primary_id", UUIDType, nullable=False),
        sa.Column("duplicate_id", UUIDType, nullable=False),
        sa.Column("match_score", sa.Numeric(5, 2), nullable=False, server_default="0"),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )

    _apply_rls()
    _backfill_default_pipelines()


def downgrade() -> None:
    _drop_rls()

    op.drop_table("crm_duplicate_candidates")
    op.drop_table("crm_import_jobs")
    op.drop_table("crm_score_rules")
    op.drop_table("crm_saved_filters")
    op.drop_table("crm_activities")
    op.drop_index("ix_crm_attachments_entity", table_name="crm_attachments")
    op.drop_table("crm_attachments")
    op.drop_table("crm_tag_assignments")
    op.drop_table("crm_tags")
    op.drop_index("ix_crm_field_values_entity", table_name="crm_custom_field_values")
    op.drop_table("crm_custom_field_values")
    op.drop_table("crm_custom_field_definitions")
    op.drop_index("ix_crm_assignments_entity", table_name="crm_assignments")
    op.drop_table("crm_assignments")

    op.drop_index("ix_leads_stage_order", table_name="leads")
    op.drop_index("ix_leads_tenant_pipeline_stage", table_name="leads")
    op.drop_index("ix_deals_stage_order", table_name="deals")
    op.drop_index("ix_deals_tenant_pipeline_stage", table_name="deals")
    op.drop_index("ix_customers_assigned_user", table_name="customers")

    with op.batch_alter_table("customer_segments") as batch_op:
        batch_op.drop_column("entity_type")

    with op.batch_alter_table("customers") as batch_op:
        batch_op.drop_constraint("fk_customers_assigned_user", type_="foreignkey")
        batch_op.drop_column("assigned_user_id")

    with op.batch_alter_table("deals") as batch_op:
        batch_op.drop_constraint("fk_deals_stage", type_="foreignkey")
        batch_op.drop_constraint("fk_deals_pipeline", type_="foreignkey")
        batch_op.drop_column("stage_id")
        batch_op.drop_column("pipeline_id")

    with op.batch_alter_table("leads") as batch_op:
        batch_op.drop_constraint("fk_leads_assigned_user", type_="foreignkey")
        batch_op.drop_constraint("fk_leads_stage", type_="foreignkey")
        batch_op.drop_constraint("fk_leads_pipeline", type_="foreignkey")
        batch_op.drop_column("assigned_user_id")
        batch_op.drop_column("stage_order")
        batch_op.drop_column("stage_id")
        batch_op.drop_column("pipeline_id")

    if _is_postgres():
        op.execute("DROP INDEX IF EXISTS uq_crm_pipelines_tenant_default")

    op.drop_index("ix_crm_stages_tenant_id", table_name="crm_stages")
    op.drop_index("ix_crm_stages_pipeline_position", table_name="crm_stages")
    op.drop_table("crm_stages")
    op.drop_index("ix_crm_pipelines_tenant_id", table_name="crm_pipelines")
    op.drop_table("crm_pipelines")
