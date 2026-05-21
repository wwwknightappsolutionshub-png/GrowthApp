"""Enterprise booking: settings, services, resources, packages, queue, analytics.

Revision ID: 026_enterprise_booking
Revises: 025_lead_factory_trial
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

from app.core.db_types import JSONBType, UUIDType

revision = "026_enterprise_booking"
down_revision = "025_lead_factory_trial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── Extend bookings ─────────────────────────────────────────────────────
    op.add_column("bookings", sa.Column("location_id", UUIDType, nullable=True))
    op.add_column("bookings", sa.Column("service_id", UUIDType, nullable=True))
    op.add_column("bookings", sa.Column("resource_id", UUIDType, nullable=True))
    op.add_column("bookings", sa.Column("timezone", sa.String(64), nullable=False, server_default="Europe/London"))
    op.add_column("bookings", sa.Column("duration_minutes", sa.Integer(), nullable=False, server_default="60"))
    op.add_column("bookings", sa.Column("no_show_fee_pence", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("bookings", sa.Column("prepaid_pence", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("bookings", sa.Column("service_fee_pence", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("bookings", sa.Column("refund_pence", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("bookings", sa.Column("refunded_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("bookings", sa.Column("package_id", UUIDType, nullable=True))
    op.add_column("bookings", sa.Column("promo_code", sa.String(40), nullable=True))
    op.add_column("bookings", sa.Column("manage_token", sa.String(64), nullable=True))
    op.add_column("bookings", sa.Column("channel", sa.String(50), nullable=True))
    op.add_column("bookings", sa.Column("utm_source", sa.String(100), nullable=True))
    op.add_column("bookings", sa.Column("utm_medium", sa.String(100), nullable=True))
    op.add_column("bookings", sa.Column("utm_campaign", sa.String(100), nullable=True))
    op.add_column("bookings", sa.Column("lead_status", sa.String(30), nullable=False, server_default="booked"))
    op.add_column("bookings", sa.Column("custom_fields", JSONBType, nullable=False, server_default="{}"))
    op.add_column("bookings", sa.Column("intake_responses", JSONBType, nullable=False, server_default="{}"))
    op.add_column("bookings", sa.Column("stripe_setup_intent_id", sa.String(255), nullable=True))
    op.create_index("ix_bookings_manage_token", "bookings", ["manage_token"], unique=True)
    op.create_index("ix_bookings_tenant_status", "bookings", ["tenant_id", "status"])
    op.create_foreign_key("fk_bookings_location", "bookings", "locations", ["location_id"], ["id"], ondelete="SET NULL")

    # ── Extend staff ────────────────────────────────────────────────────────
    op.add_column("staff", sa.Column("role", sa.String(30), nullable=False, server_default="staff"))
    op.add_column("staff", sa.Column("permissions", sa.JSON(), nullable=False, server_default="{}"))
    op.add_column("staff", sa.Column("location_ids", sa.JSON(), nullable=False, server_default="[]"))

    # ── Extend availability_slots ─────────────────────────────────────────────
    op.add_column("availability_slots", sa.Column("location_id", UUIDType, nullable=True))
    op.add_column("availability_slots", sa.Column("resource_id", UUIDType, nullable=True))
    op.add_column("availability_slots", sa.Column("service_id", UUIDType, nullable=True))
    op.add_column("availability_slots", sa.Column("duration_minutes", sa.Integer(), nullable=False, server_default="60"))
    op.create_index("ix_availability_slots_lookup", "availability_slots", ["tenant_id", "slot_date", "is_booked"])

    # ── booking_settings ────────────────────────────────────────────────────
    op.create_table(
        "booking_settings",
        sa.Column("tenant_id", UUIDType, primary_key=True),
        sa.Column("timezone", sa.String(64), nullable=False, server_default="Europe/London"),
        sa.Column("default_duration_minutes", sa.Integer(), nullable=False, server_default="60"),
        sa.Column("deposit_enabled", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("default_deposit_pence", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("no_show_fee_pence", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("service_fee_percent", sa.Numeric(5, 2), nullable=False, server_default="0"),
        sa.Column("allow_self_reschedule", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("allow_self_cancel", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("min_notice_hours", sa.Integer(), nullable=False, server_default="24"),
        sa.Column("overbooking_allowed", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("business_hours", JSONBType, nullable=False, server_default="{}"),
        sa.Column("automation_config", JSONBType, nullable=False, server_default="{}"),
        sa.Column("google_pixel_id", sa.String(100), nullable=True),
        sa.Column("meta_pixel_id", sa.String(100), nullable=True),
        sa.Column("widget_primary_color", sa.String(20), nullable=True),
        sa.Column("intake_questions", JSONBType, nullable=False, server_default="[]"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
    )

    op.create_table(
        "booking_services",
        sa.Column("id", UUIDType, primary_key=True),
        sa.Column("tenant_id", UUIDType, nullable=False, index=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("duration_minutes", sa.Integer(), nullable=False, server_default="60"),
        sa.Column("price_pence", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("deposit_pence", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("location_id", UUIDType, nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
    )

    op.create_table(
        "booking_resources",
        sa.Column("id", UUIDType, primary_key=True),
        sa.Column("tenant_id", UUIDType, nullable=False, index=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("resource_type", sa.String(30), nullable=False, server_default="room"),
        sa.Column("location_id", UUIDType, nullable=True),
        sa.Column("capacity", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
    )

    op.create_table(
        "staff_shifts",
        sa.Column("id", UUIDType, primary_key=True),
        sa.Column("tenant_id", UUIDType, nullable=False, index=True),
        sa.Column("staff_id", UUIDType, nullable=False, index=True),
        sa.Column("location_id", UUIDType, nullable=True),
        sa.Column("shift_date", sa.Date(), nullable=False),
        sa.Column("start_time", sa.Time(), nullable=False),
        sa.Column("end_time", sa.Time(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["staff_id"], ["staff.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_staff_shifts_date", "staff_shifts", ["tenant_id", "staff_id", "shift_date"])

    op.create_table(
        "staff_blackouts",
        sa.Column("id", UUIDType, primary_key=True),
        sa.Column("tenant_id", UUIDType, nullable=False, index=True),
        sa.Column("staff_id", UUIDType, nullable=True),
        sa.Column("location_id", UUIDType, nullable=True),
        sa.Column("start_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("reason", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
    )

    op.create_table(
        "booking_packages",
        sa.Column("id", UUIDType, primary_key=True),
        sa.Column("tenant_id", UUIDType, nullable=False, index=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("sessions_included", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("price_pence", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("valid_days", sa.Integer(), nullable=False, server_default="365"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
    )

    op.create_table(
        "booking_customer_credits",
        sa.Column("id", UUIDType, primary_key=True),
        sa.Column("tenant_id", UUIDType, nullable=False, index=True),
        sa.Column("customer_id", UUIDType, nullable=True),
        sa.Column("customer_email", sa.String(255), nullable=True),
        sa.Column("package_id", UUIDType, nullable=True),
        sa.Column("sessions_remaining", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["package_id"], ["booking_packages.id"], ondelete="SET NULL"),
    )

    op.create_table(
        "booking_promo_codes",
        sa.Column("id", UUIDType, primary_key=True),
        sa.Column("tenant_id", UUIDType, nullable=False, index=True),
        sa.Column("code", sa.String(40), nullable=False),
        sa.Column("discount_percent", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("discount_pence", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("max_uses", sa.Integer(), nullable=True),
        sa.Column("uses_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_booking_promo_tenant_code", "booking_promo_codes", ["tenant_id", "code"], unique=True)

    op.create_table(
        "booking_calendar_connections",
        sa.Column("id", UUIDType, primary_key=True),
        sa.Column("tenant_id", UUIDType, nullable=False, index=True),
        sa.Column("staff_id", UUIDType, nullable=True),
        sa.Column("provider", sa.String(20), nullable=False),
        sa.Column("external_calendar_id", sa.String(255), nullable=True),
        sa.Column("access_token_enc", sa.Text(), nullable=True),
        sa.Column("refresh_token_enc", sa.Text(), nullable=True),
        sa.Column("sync_enabled", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("last_synced_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
    )

    op.create_table(
        "booking_notification_queue",
        sa.Column("id", UUIDType, primary_key=True),
        sa.Column("tenant_id", UUIDType, nullable=False, index=True),
        sa.Column("booking_id", UUIDType, nullable=True),
        sa.Column("channel", sa.String(20), nullable=False),
        sa.Column("notification_type", sa.String(50), nullable=False),
        sa.Column("recipient", sa.String(255), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("scheduled_for", sa.DateTime(timezone=True), nullable=False, index=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["booking_id"], ["bookings.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_booking_notif_queue_status", "booking_notification_queue", ["status", "scheduled_for"])

    op.create_table(
        "booking_abandoned_sessions",
        sa.Column("id", UUIDType, primary_key=True),
        sa.Column("tenant_id", UUIDType, nullable=False, index=True),
        sa.Column("session_token", sa.String(64), nullable=False),
        sa.Column("customer_email", sa.String(255), nullable=True),
        sa.Column("payload", JSONBType, nullable=False, server_default="{}"),
        sa.Column("recovered_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_booking_abandoned_token", "booking_abandoned_sessions", ["session_token"], unique=True)


def downgrade() -> None:
    op.drop_table("booking_abandoned_sessions")
    op.drop_table("booking_notification_queue")
    op.drop_table("booking_calendar_connections")
    op.drop_table("booking_promo_codes")
    op.drop_table("booking_customer_credits")
    op.drop_table("booking_packages")
    op.drop_table("staff_blackouts")
    op.drop_table("staff_shifts")
    op.drop_table("booking_resources")
    op.drop_table("booking_services")
    op.drop_table("booking_settings")
    op.drop_index("ix_availability_slots_lookup", "availability_slots")
    op.drop_column("availability_slots", "duration_minutes")
    op.drop_column("availability_slots", "service_id")
    op.drop_column("availability_slots", "resource_id")
    op.drop_column("availability_slots", "location_id")
    op.drop_column("staff", "location_ids")
    op.drop_column("staff", "permissions")
    op.drop_column("staff", "role")
    op.drop_constraint("fk_bookings_location", "bookings", type_="foreignkey")
    op.drop_index("ix_bookings_tenant_status", "bookings")
    op.drop_index("ix_bookings_manage_token", "bookings")
    for col in (
        "stripe_setup_intent_id", "intake_responses", "custom_fields", "lead_status",
        "utm_campaign", "utm_medium", "utm_source", "channel", "manage_token",
        "promo_code", "package_id", "refunded_at", "refund_pence", "service_fee_pence",
        "prepaid_pence", "no_show_fee_pence", "duration_minutes", "timezone",
        "resource_id", "service_id", "location_id",
    ):
        op.drop_column("bookings", col)
