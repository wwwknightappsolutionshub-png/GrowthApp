"""Salon + Garage industry add-on tables.

Revision ID: 036_industry_salon_garage
Revises: 035_industry_addons_core
"""
from alembic import op
import sqlalchemy as sa

from app.core.db_types import JSONBType, UUIDType

revision = "036_industry_salon_garage"
down_revision = "035_industry_addons_core"
branch_labels = None
depends_on = None


def _tenant_id():
    return sa.Column("tenant_id", UUIDType, sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)


def upgrade() -> None:
    # Shared vehicle registry (garage; optional on bookings)
    op.create_table(
        "vehicles",
        sa.Column("id", UUIDType, primary_key=True),
        _tenant_id(),
        sa.Column("customer_id", UUIDType, sa.ForeignKey("customers.id", ondelete="CASCADE"), nullable=False),
        sa.Column("vin", sa.String(32), nullable=True),
        sa.Column("registration", sa.String(20), nullable=True),
        sa.Column("make", sa.String(80), nullable=True),
        sa.Column("model", sa.String(80), nullable=True),
        sa.Column("model_year", sa.Integer, nullable=True),
        sa.Column("mileage", sa.Integer, nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_vehicles_tenant_id", "vehicles", ["tenant_id"])
    op.create_index("ix_vehicles_customer_id", "vehicles", ["customer_id"])

    op.create_table(
        "parts_inventory",
        sa.Column("id", UUIDType, primary_key=True),
        _tenant_id(),
        sa.Column("sku", sa.String(80), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("category", sa.String(80), nullable=False, server_default="general"),
        sa.Column("qty_on_hand", sa.Integer, nullable=False, server_default="0"),
        sa.Column("unit_cost_pence", sa.Integer, nullable=False, server_default="0"),
        sa.Column("reorder_level", sa.Integer, nullable=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("tenant_id", "sku", name="uq_parts_inventory_tenant_sku"),
    )
    op.create_index("ix_parts_inventory_tenant_id", "parts_inventory", ["tenant_id"])

    op.create_table(
        "booking_product_catalog",
        sa.Column("id", UUIDType, primary_key=True),
        _tenant_id(),
        sa.Column("sku", sa.String(80), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("unit_price_pence", sa.Integer, nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("tenant_id", "sku", name="uq_booking_product_catalog_tenant_sku"),
    )
    op.create_index("ix_booking_product_catalog_tenant_id", "booking_product_catalog", ["tenant_id"])

    op.create_table(
        "staff_skills",
        sa.Column("id", UUIDType, primary_key=True),
        _tenant_id(),
        sa.Column("staff_id", UUIDType, sa.ForeignKey("staff.id", ondelete="CASCADE"), nullable=False),
        sa.Column("skill_code", sa.String(80), nullable=False),
        sa.Column("proficiency_level", sa.Integer, nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("tenant_id", "staff_id", "skill_code", name="uq_staff_skills_tenant_staff_code"),
    )
    op.create_index("ix_staff_skills_tenant_id", "staff_skills", ["tenant_id"])
    op.create_index("ix_staff_skills_staff_id", "staff_skills", ["staff_id"])

    op.create_table(
        "service_required_skills",
        sa.Column("id", UUIDType, primary_key=True),
        _tenant_id(),
        sa.Column("service_id", UUIDType, sa.ForeignKey("booking_services.id", ondelete="CASCADE"), nullable=False),
        sa.Column("skill_code", sa.String(80), nullable=False),
        sa.Column("min_proficiency", sa.Integer, nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("service_id", "skill_code", name="uq_service_required_skills_service_code"),
    )
    op.create_index("ix_service_required_skills_tenant_id", "service_required_skills", ["tenant_id"])
    op.create_index("ix_service_required_skills_service_id", "service_required_skills", ["service_id"])

    op.create_table(
        "mechanic_skills",
        sa.Column("id", UUIDType, primary_key=True),
        _tenant_id(),
        sa.Column("staff_id", UUIDType, sa.ForeignKey("staff.id", ondelete="CASCADE"), nullable=False),
        sa.Column("skill_code", sa.String(80), nullable=False),
        sa.Column("certification_level", sa.String(50), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("tenant_id", "staff_id", "skill_code", name="uq_mechanic_skills_tenant_staff_code"),
    )
    op.create_index("ix_mechanic_skills_tenant_id", "mechanic_skills", ["tenant_id"])
    op.create_index("ix_mechanic_skills_staff_id", "mechanic_skills", ["staff_id"])

    op.create_table(
        "vehicle_service_estimates",
        sa.Column("id", UUIDType, primary_key=True),
        _tenant_id(),
        sa.Column("make", sa.String(80), nullable=False),
        sa.Column("model", sa.String(80), nullable=False),
        sa.Column("model_year", sa.Integer, nullable=True),
        sa.Column("service_id", UUIDType, sa.ForeignKey("booking_services.id", ondelete="SET NULL"), nullable=True),
        sa.Column("service_name", sa.String(255), nullable=True),
        sa.Column("estimated_minutes", sa.Integer, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_vehicle_service_estimates_tenant_id", "vehicle_service_estimates", ["tenant_id"])

    op.create_table(
        "booking_session_services",
        sa.Column("id", UUIDType, primary_key=True),
        _tenant_id(),
        sa.Column("booking_id", UUIDType, sa.ForeignKey("bookings.id", ondelete="CASCADE"), nullable=False),
        sa.Column("service_id", UUIDType, sa.ForeignKey("booking_services.id", ondelete="CASCADE"), nullable=False),
        sa.Column("sort_order", sa.Integer, nullable=False, server_default="0"),
        sa.Column("duration_minutes", sa.Integer, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("booking_id", "service_id", name="uq_booking_session_services_booking_service"),
    )
    op.create_index("ix_booking_session_services_tenant_id", "booking_session_services", ["tenant_id"])
    op.create_index("ix_booking_session_services_booking_id", "booking_session_services", ["booking_id"])

    op.create_table(
        "booking_resource_allocations",
        sa.Column("id", UUIDType, primary_key=True),
        _tenant_id(),
        sa.Column("booking_id", UUIDType, sa.ForeignKey("bookings.id", ondelete="CASCADE"), nullable=False),
        sa.Column("resource_id", UUIDType, sa.ForeignKey("booking_resources.id", ondelete="CASCADE"), nullable=False),
        sa.Column("allocated_from", sa.DateTime(timezone=True), nullable=True),
        sa.Column("allocated_to", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_booking_resource_allocations_tenant_id", "booking_resource_allocations", ["tenant_id"])
    op.create_index("ix_booking_resource_allocations_booking_id", "booking_resource_allocations", ["booking_id"])

    op.create_table(
        "booking_upsell_lines",
        sa.Column("id", UUIDType, primary_key=True),
        _tenant_id(),
        sa.Column("booking_id", UUIDType, sa.ForeignKey("bookings.id", ondelete="CASCADE"), nullable=False),
        sa.Column(
            "product_id",
            UUIDType,
            sa.ForeignKey("booking_product_catalog.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("quantity", sa.Integer, nullable=False, server_default="1"),
        sa.Column("unit_price_pence", sa.Integer, nullable=False),
        sa.Column("line_total_pence", sa.Integer, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_booking_upsell_lines_tenant_id", "booking_upsell_lines", ["tenant_id"])
    op.create_index("ix_booking_upsell_lines_booking_id", "booking_upsell_lines", ["booking_id"])

    op.create_table(
        "booking_parts_reservations",
        sa.Column("id", UUIDType, primary_key=True),
        _tenant_id(),
        sa.Column("booking_id", UUIDType, sa.ForeignKey("bookings.id", ondelete="CASCADE"), nullable=False),
        sa.Column("part_id", UUIDType, sa.ForeignKey("parts_inventory.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("quantity_reserved", sa.Integer, nullable=False, server_default="1"),
        sa.Column("status", sa.String(30), nullable=False, server_default="reserved"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_booking_parts_reservations_tenant_id", "booking_parts_reservations", ["tenant_id"])
    op.create_index("ix_booking_parts_reservations_booking_id", "booking_parts_reservations", ["booking_id"])

    op.create_table(
        "invoice_tips",
        sa.Column("id", UUIDType, primary_key=True),
        _tenant_id(),
        sa.Column("invoice_id", UUIDType, sa.ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False),
        sa.Column("staff_id", UUIDType, sa.ForeignKey("staff.id", ondelete="SET NULL"), nullable=True),
        sa.Column("amount_pence", sa.Integer, nullable=False),
        sa.Column("method", sa.String(50), nullable=False, server_default="card"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_invoice_tips_tenant_id", "invoice_tips", ["tenant_id"])
    op.create_index("ix_invoice_tips_invoice_id", "invoice_tips", ["invoice_id"])

    op.create_table(
        "memberships",
        sa.Column("id", UUIDType, primary_key=True),
        _tenant_id(),
        sa.Column("customer_id", UUIDType, sa.ForeignKey("customers.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("status", sa.String(30), nullable=False, server_default="active"),
        sa.Column("price_pence", sa.Integer, nullable=False, server_default="0"),
        sa.Column("billing_interval", sa.String(20), nullable=False, server_default="monthly"),
        sa.Column("stripe_subscription_id", sa.String(255), nullable=True),
        sa.Column("started_at", sa.Date, nullable=True),
        sa.Column("ends_at", sa.Date, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_memberships_tenant_id", "memberships", ["tenant_id"])
    op.create_index("ix_memberships_customer_id", "memberships", ["customer_id"])

    op.create_table(
        "membership_benefits",
        sa.Column("id", UUIDType, primary_key=True),
        sa.Column("membership_id", UUIDType, sa.ForeignKey("memberships.id", ondelete="CASCADE"), nullable=False),
        sa.Column("benefit_type", sa.String(50), nullable=False),
        sa.Column("config", JSONBType, nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_membership_benefits_membership_id", "membership_benefits", ["membership_id"])

    op.create_table(
        "industry_service_packages",
        sa.Column("id", UUIDType, primary_key=True),
        _tenant_id(),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("sessions_included", sa.Integer, nullable=False, server_default="1"),
        sa.Column("price_pence", sa.Integer, nullable=False, server_default="0"),
        sa.Column("valid_days", sa.Integer, nullable=False, server_default="365"),
        sa.Column("service_ids", JSONBType, nullable=False, server_default="[]"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_industry_service_packages_tenant_id", "industry_service_packages", ["tenant_id"])

    op.create_table(
        "package_redemptions",
        sa.Column("id", UUIDType, primary_key=True),
        _tenant_id(),
        sa.Column(
            "package_id",
            UUIDType,
            sa.ForeignKey("industry_service_packages.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("customer_id", UUIDType, sa.ForeignKey("customers.id", ondelete="CASCADE"), nullable=False),
        sa.Column("booking_id", UUIDType, sa.ForeignKey("bookings.id", ondelete="SET NULL"), nullable=True),
        sa.Column("invoice_id", UUIDType, sa.ForeignKey("invoices.id", ondelete="SET NULL"), nullable=True),
        sa.Column("redeemed_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_package_redemptions_tenant_id", "package_redemptions", ["tenant_id"])
    op.create_index("ix_package_redemptions_customer_id", "package_redemptions", ["customer_id"])

    op.create_table(
        "industry_invoice_templates",
        sa.Column("id", UUIDType, primary_key=True),
        _tenant_id(),
        sa.Column("vertical", sa.String(30), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("template_body", JSONBType, nullable=False, server_default="{}"),
        sa.Column("is_default", sa.Boolean, nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_industry_invoice_templates_tenant_id", "industry_invoice_templates", ["tenant_id"])

    op.create_table(
        "parts_markup_rules",
        sa.Column("id", UUIDType, primary_key=True),
        _tenant_id(),
        sa.Column("category", sa.String(80), nullable=False),
        sa.Column("markup_percent", sa.Integer, nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("tenant_id", "category", name="uq_parts_markup_rules_tenant_category"),
    )
    op.create_index("ix_parts_markup_rules_tenant_id", "parts_markup_rules", ["tenant_id"])

    op.create_table(
        "invoice_warranties",
        sa.Column("id", UUIDType, primary_key=True),
        _tenant_id(),
        sa.Column("invoice_id", UUIDType, sa.ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False),
        sa.Column("warranty_months", sa.Integer, nullable=False, server_default="12"),
        sa.Column("terms", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_invoice_warranties_tenant_id", "invoice_warranties", ["tenant_id"])
    op.create_index("ix_invoice_warranties_invoice_id", "invoice_warranties", ["invoice_id"])

    op.create_table(
        "vehicle_service_records",
        sa.Column("id", UUIDType, primary_key=True),
        _tenant_id(),
        sa.Column("vehicle_id", UUIDType, sa.ForeignKey("vehicles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("booking_id", UUIDType, sa.ForeignKey("bookings.id", ondelete="SET NULL"), nullable=True),
        sa.Column("service_date", sa.Date, nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("mileage_at_service", sa.Integer, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_vehicle_service_records_tenant_id", "vehicle_service_records", ["tenant_id"])
    op.create_index("ix_vehicle_service_records_vehicle_id", "vehicle_service_records", ["vehicle_id"])

    op.create_table(
        "customer_salon_profiles",
        sa.Column("customer_id", UUIDType, sa.ForeignKey("customers.id", ondelete="CASCADE"), primary_key=True),
        _tenant_id(),
        sa.Column("formula", JSONBType, nullable=False, server_default="{}"),
        sa.Column("allergies", sa.Text, nullable=True),
        sa.Column("preferences", JSONBType, nullable=False, server_default="{}"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_customer_salon_profiles_tenant_id", "customer_salon_profiles", ["tenant_id"])

    op.create_table(
        "customer_media_timeline",
        sa.Column("id", UUIDType, primary_key=True),
        _tenant_id(),
        sa.Column("customer_id", UUIDType, sa.ForeignKey("customers.id", ondelete="CASCADE"), nullable=False),
        sa.Column("media_url", sa.Text, nullable=False),
        sa.Column("caption", sa.Text, nullable=True),
        sa.Column("taken_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_customer_media_timeline_tenant_id", "customer_media_timeline", ["tenant_id"])
    op.create_index("ix_customer_media_timeline_customer_id", "customer_media_timeline", ["customer_id"])

    op.create_table(
        "industry_rebook_reminders",
        sa.Column("id", UUIDType, primary_key=True),
        _tenant_id(),
        sa.Column("customer_id", UUIDType, sa.ForeignKey("customers.id", ondelete="CASCADE"), nullable=False),
        sa.Column("service_id", UUIDType, sa.ForeignKey("booking_services.id", ondelete="SET NULL"), nullable=True),
        sa.Column("due_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(30), nullable=False, server_default="pending"),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_industry_rebook_reminders_tenant_id", "industry_rebook_reminders", ["tenant_id"])
    op.create_index("ix_industry_rebook_reminders_customer_id", "industry_rebook_reminders", ["customer_id"])

    op.create_table(
        "vehicle_parts_usage",
        sa.Column("id", UUIDType, primary_key=True),
        _tenant_id(),
        sa.Column("vehicle_id", UUIDType, sa.ForeignKey("vehicles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("part_id", UUIDType, sa.ForeignKey("parts_inventory.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("booking_id", UUIDType, sa.ForeignKey("bookings.id", ondelete="SET NULL"), nullable=True),
        sa.Column("quantity", sa.Integer, nullable=False, server_default="1"),
        sa.Column("used_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_vehicle_parts_usage_tenant_id", "vehicle_parts_usage", ["tenant_id"])
    op.create_index("ix_vehicle_parts_usage_vehicle_id", "vehicle_parts_usage", ["vehicle_id"])

    op.create_table(
        "maintenance_predictions",
        sa.Column("id", UUIDType, primary_key=True),
        _tenant_id(),
        sa.Column("vehicle_id", UUIDType, sa.ForeignKey("vehicles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("prediction_type", sa.String(80), nullable=False),
        sa.Column("due_date", sa.Date, nullable=True),
        sa.Column("confidence", sa.Integer, nullable=False, server_default="50"),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_maintenance_predictions_tenant_id", "maintenance_predictions", ["tenant_id"])
    op.create_index("ix_maintenance_predictions_vehicle_id", "maintenance_predictions", ["vehicle_id"])

    op.create_table(
        "customer_garage_scores",
        sa.Column("customer_id", UUIDType, sa.ForeignKey("customers.id", ondelete="CASCADE"), primary_key=True),
        _tenant_id(),
        sa.Column("clv_score", sa.Integer, nullable=False, server_default="0"),
        sa.Column("reliability_score", sa.Integer, nullable=False, server_default="0"),
        sa.Column("score_metadata", JSONBType, nullable=False, server_default="{}"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_customer_garage_scores_tenant_id", "customer_garage_scores", ["tenant_id"])

    op.add_column(
        "invoice_items",
        sa.Column("line_kind", sa.String(20), nullable=False, server_default="service"),
    )
    op.add_column(
        "bookings",
        sa.Column("vehicle_id", UUIDType, sa.ForeignKey("vehicles.id", ondelete="SET NULL"), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("bookings", "vehicle_id")
    op.drop_column("invoice_items", "line_kind")

    op.drop_table("customer_garage_scores")
    op.drop_table("maintenance_predictions")
    op.drop_table("vehicle_parts_usage")
    op.drop_table("industry_rebook_reminders")
    op.drop_table("customer_media_timeline")
    op.drop_table("customer_salon_profiles")
    op.drop_table("vehicle_service_records")
    op.drop_table("invoice_warranties")
    op.drop_table("parts_markup_rules")
    op.drop_table("industry_invoice_templates")
    op.drop_table("package_redemptions")
    op.drop_table("industry_service_packages")
    op.drop_table("membership_benefits")
    op.drop_table("memberships")
    op.drop_table("invoice_tips")
    op.drop_table("booking_parts_reservations")
    op.drop_table("booking_upsell_lines")
    op.drop_table("booking_resource_allocations")
    op.drop_table("booking_session_services")
    op.drop_table("vehicle_service_estimates")
    op.drop_table("mechanic_skills")
    op.drop_table("service_required_skills")
    op.drop_table("staff_skills")
    op.drop_table("booking_product_catalog")
    op.drop_table("parts_inventory")
    op.drop_table("vehicles")
