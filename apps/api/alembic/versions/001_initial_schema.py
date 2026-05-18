"""Initial schema

Revision ID: 001
Revises:
Create Date: 2024-01-01 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Enable UUID extension
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')

    # subscription_plans (no FK deps)
    op.create_table("subscription_plans",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("price_gbp_monthly", sa.Integer(), nullable=False),
        sa.Column("stripe_price_id", sa.String(255)),
        sa.Column("max_locations", sa.Integer(), default=1),
        sa.Column("max_leads_per_month", sa.Integer(), default=500),
        sa.Column("max_sms_per_month", sa.Integer(), default=1000),
        sa.Column("max_users", sa.Integer(), default=1),
        sa.Column("has_social_posting", sa.Boolean(), default=False),
        sa.Column("has_ai_content", sa.Boolean(), default=False),
        sa.Column("has_white_label", sa.Boolean(), default=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # users
    op.create_table("users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("password_hash", sa.Text(), nullable=False),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("phone", sa.String(50)),
        sa.Column("avatar_url", sa.Text()),
        sa.Column("email_verified_at", sa.DateTime(timezone=True)),
        sa.Column("is_superadmin", sa.Boolean(), default=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_users_email", "users", ["email"])

    # tenants
    op.create_table("tenants",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("slug", sa.String(100), nullable=False, unique=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("business_type", sa.String(100), nullable=False),
        sa.Column("logo_url", sa.Text()),
        sa.Column("primary_color", sa.String(20), default="#2563EB"),
        sa.Column("website_url", sa.Text()),
        sa.Column("phone", sa.String(50)),
        sa.Column("email", sa.String(255)),
        sa.Column("address", sa.Text()),
        sa.Column("city", sa.String(100)),
        sa.Column("postcode", sa.String(20), nullable=False),
        sa.Column("country", sa.String(10), default="GB"),
        sa.Column("google_place_id", sa.Text()),
        sa.Column("google_review_url", sa.Text()),
        sa.Column("timezone", sa.String(50), default="Europe/London"),
        sa.Column("plan_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("subscription_plans.id")),
        sa.Column("trial_ends_at", sa.DateTime(timezone=True)),
        sa.Column("is_active", sa.Boolean(), default=True),
        sa.Column("onboarding_completed", sa.Boolean(), default=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_tenants_slug", "tenants", ["slug"])

    # refresh_tokens
    op.create_table("refresh_tokens",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("token_hash", sa.String(128), nullable=False, unique=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_refresh_tokens_user_id", "refresh_tokens", ["user_id"])

    # tenant_members
    op.create_table("tenant_members",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("role", sa.String(20), nullable=False),
        sa.Column("invited_at", sa.DateTime(timezone=True)),
        sa.Column("joined_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_tenant_members_tenant_id", "tenant_members", ["tenant_id"])
    op.create_index("ix_tenant_members_user_id", "tenant_members", ["user_id"])

    # locations
    op.create_table("locations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("slug", sa.String(100), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("address", sa.Text()),
        sa.Column("city", sa.String(100)),
        sa.Column("postcode", sa.String(20)),
        sa.Column("phone", sa.String(50)),
        sa.Column("email", sa.String(255)),
        sa.Column("is_primary", sa.Boolean(), default=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_locations_tenant_id", "locations", ["tenant_id"])

    # subscriptions
    op.create_table("subscriptions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id"), nullable=False, unique=True),
        sa.Column("plan_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("subscription_plans.id"), nullable=False),
        sa.Column("stripe_customer_id", sa.String(255)),
        sa.Column("stripe_subscription_id", sa.String(255)),
        sa.Column("status", sa.String(50), default="trialing"),
        sa.Column("current_period_start", sa.DateTime(timezone=True)),
        sa.Column("current_period_end", sa.DateTime(timezone=True)),
        sa.Column("cancel_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # billing_invoices
    op.create_table("billing_invoices",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("stripe_invoice_id", sa.String(255), unique=True),
        sa.Column("amount_pence", sa.Integer(), nullable=False),
        sa.Column("currency", sa.String(10), default="gbp"),
        sa.Column("status", sa.String(50), nullable=False),
        sa.Column("invoice_pdf_url", sa.Text()),
        sa.Column("period_start", sa.DateTime(timezone=True)),
        sa.Column("period_end", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # audit_logs
    op.create_table("audit_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id")),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("resource", sa.String(100), nullable=False),
        sa.Column("resource_id", sa.String(255)),
        sa.Column("ip_address", sa.String(45)),
        sa.Column("user_agent", sa.Text()),
        sa.Column("metadata", postgresql.JSONB(), default={}),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_audit_logs_tenant_id", "audit_logs", ["tenant_id"])
    op.create_index("ix_audit_logs_created_at", "audit_logs", ["created_at"])

    # lead_sources
    op.create_table("lead_sources",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # leads
    op.create_table("leads",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("location_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("locations.id")),
        sa.Column("first_name", sa.String(100), nullable=False),
        sa.Column("last_name", sa.String(100)),
        sa.Column("email", sa.String(255)),
        sa.Column("phone", sa.String(50)),
        sa.Column("message", sa.Text()),
        sa.Column("service_needed", sa.String(200)),
        sa.Column("postcode", sa.String(20)),
        sa.Column("source", sa.String(100), default="web_form"),
        sa.Column("utm_source", sa.String(100)),
        sa.Column("utm_medium", sa.String(100)),
        sa.Column("utm_campaign", sa.String(100)),
        sa.Column("ip_address", sa.String(45)),
        sa.Column("referrer_url", sa.Text()),
        sa.Column("status", sa.String(30), default="new"),
        sa.Column("is_spam", sa.Boolean(), default=False),
        sa.Column("tags", postgresql.JSONB(), default=[]),
        sa.Column("extra_data", postgresql.JSONB(), default={}),
        sa.Column("converted_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_leads_tenant_id", "leads", ["tenant_id"])
    op.create_index("ix_leads_email", "leads", ["email"])
    op.create_index("ix_leads_created_at", "leads", ["created_at"])

    # customers
    op.create_table("customers",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("first_name", sa.String(100), nullable=False),
        sa.Column("last_name", sa.String(100)),
        sa.Column("email", sa.String(255)),
        sa.Column("phone", sa.String(50)),
        sa.Column("address", sa.Text()),
        sa.Column("postcode", sa.String(20)),
        sa.Column("notes", sa.Text()),
        sa.Column("source", sa.String(100)),
        sa.Column("gdpr_consent", sa.Boolean(), default=False),
        sa.Column("gdpr_consent_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_customers_tenant_id", "customers", ["tenant_id"])
    op.create_index("ix_customers_email", "customers", ["email"])

    # deals
    op.create_table("deals",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("customer_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("customers.id"), nullable=False),
        sa.Column("lead_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("leads.id")),
        sa.Column("location_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("locations.id")),
        sa.Column("assigned_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id")),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("stage", sa.String(50), default="New"),
        sa.Column("stage_order", sa.Integer(), default=0),
        sa.Column("service_type", sa.String(100)),
        sa.Column("description", sa.Text()),
        sa.Column("value_pence", sa.Integer(), default=0),
        sa.Column("source", sa.String(100)),
        sa.Column("lost_reason", sa.Text()),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_deals_tenant_id", "deals", ["tenant_id"])
    op.create_index("ix_deals_stage", "deals", ["stage"])

    # deal_activities
    op.create_table("deal_activities",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("deal_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("deals.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id")),
        sa.Column("type", sa.String(50), nullable=False),
        sa.Column("body", sa.Text()),
        sa.Column("metadata", postgresql.JSONB(), default={}),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_deal_activities_deal_id", "deal_activities", ["deal_id"])

    # staff
    op.create_table("staff",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id")),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("email", sa.String(255)),
        sa.Column("phone", sa.String(50)),
        sa.Column("is_active", sa.Boolean(), default=True),
        sa.Column("working_hours", postgresql.JSONB(), default={}),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # availability_slots
    op.create_table("availability_slots",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("staff_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("staff.id")),
        sa.Column("slot_date", sa.Date(), nullable=False),
        sa.Column("start_time", sa.Time(), nullable=False),
        sa.Column("end_time", sa.Time(), nullable=False),
        sa.Column("is_booked", sa.Boolean(), default=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_slots_tenant_date", "availability_slots", ["tenant_id", "slot_date"])

    # bookings
    op.create_table("bookings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("deal_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("deals.id")),
        sa.Column("customer_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("customers.id")),
        sa.Column("slot_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("availability_slots.id")),
        sa.Column("staff_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("staff.id")),
        sa.Column("customer_name", sa.String(255), nullable=False),
        sa.Column("customer_email", sa.String(255)),
        sa.Column("customer_phone", sa.String(50)),
        sa.Column("service_description", sa.Text()),
        sa.Column("booking_date", sa.Date(), nullable=False),
        sa.Column("start_time", sa.Time(), nullable=False),
        sa.Column("end_time", sa.Time()),
        sa.Column("status", sa.String(30), default="confirmed"),
        sa.Column("deposit_required_pence", sa.Integer(), default=0),
        sa.Column("deposit_paid_pence", sa.Integer(), default=0),
        sa.Column("stripe_payment_intent_id", sa.String(255)),
        sa.Column("notes", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_bookings_tenant_id", "bookings", ["tenant_id"])

    # quote_templates
    op.create_table("quote_templates",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("items", postgresql.JSONB(), default=[]),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # quotes
    op.create_table("quotes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("deal_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("deals.id")),
        sa.Column("customer_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("customers.id"), nullable=False),
        sa.Column("quote_number", sa.String(50), nullable=False),
        sa.Column("public_token", sa.String(100), unique=True, nullable=False),
        sa.Column("status", sa.String(30), default="draft"),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("notes", sa.Text()),
        sa.Column("valid_until", sa.Date()),
        sa.Column("subtotal_pence", sa.Integer(), default=0),
        sa.Column("vat_pence", sa.Integer(), default=0),
        sa.Column("total_pence", sa.Integer(), default=0),
        sa.Column("accepted_at", sa.DateTime(timezone=True)),
        sa.Column("declined_at", sa.DateTime(timezone=True)),
        sa.Column("sent_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_quotes_tenant_id", "quotes", ["tenant_id"])
    op.create_index("ix_quotes_public_token", "quotes", ["public_token"])

    # quote_items
    op.create_table("quote_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("quote_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("quotes.id", ondelete="CASCADE"), nullable=False),
        sa.Column("description", sa.String(500), nullable=False),
        sa.Column("quantity", sa.Integer(), default=1),
        sa.Column("unit_price_pence", sa.Integer(), nullable=False),
        sa.Column("vat_rate", sa.Integer(), default=20),
        sa.Column("line_total_pence", sa.Integer(), nullable=False),
        sa.Column("sort_order", sa.Integer(), default=0),
    )

    # invoices
    op.create_table("invoices",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("quote_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("quotes.id")),
        sa.Column("deal_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("deals.id")),
        sa.Column("customer_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("customers.id"), nullable=False),
        sa.Column("invoice_number", sa.String(50), nullable=False),
        sa.Column("public_token", sa.String(100), unique=True, nullable=False),
        sa.Column("status", sa.String(30), default="draft"),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("notes", sa.Text()),
        sa.Column("due_date", sa.Date()),
        sa.Column("subtotal_pence", sa.Integer(), default=0),
        sa.Column("vat_pence", sa.Integer(), default=0),
        sa.Column("total_pence", sa.Integer(), default=0),
        sa.Column("paid_pence", sa.Integer(), default=0),
        sa.Column("stripe_payment_link", sa.Text()),
        sa.Column("sent_at", sa.DateTime(timezone=True)),
        sa.Column("paid_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_invoices_tenant_id", "invoices", ["tenant_id"])

    # invoice_items
    op.create_table("invoice_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("invoice_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False),
        sa.Column("description", sa.String(500), nullable=False),
        sa.Column("quantity", sa.Integer(), default=1),
        sa.Column("unit_price_pence", sa.Integer(), nullable=False),
        sa.Column("vat_rate", sa.Integer(), default=20),
        sa.Column("line_total_pence", sa.Integer(), nullable=False),
        sa.Column("sort_order", sa.Integer(), default=0),
    )

    # payments
    op.create_table("payments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("invoice_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("invoices.id"), nullable=False),
        sa.Column("amount_pence", sa.Integer(), nullable=False),
        sa.Column("method", sa.String(50), default="stripe"),
        sa.Column("stripe_payment_intent_id", sa.String(255)),
        sa.Column("status", sa.String(30), default="succeeded"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # message_templates
    op.create_table("message_templates",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("channel", sa.String(20), nullable=False),
        sa.Column("subject", sa.String(500)),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # automations
    op.create_table("automations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("trigger_event", sa.String(100), nullable=False),
        sa.Column("trigger_conditions", postgresql.JSONB(), default={}),
        sa.Column("is_active", sa.Boolean(), default=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_automations_tenant_id", "automations", ["tenant_id"])

    # automation_steps
    op.create_table("automation_steps",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("automation_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("automations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("step_order", sa.Integer(), nullable=False),
        sa.Column("action_type", sa.String(50), nullable=False),
        sa.Column("delay_minutes", sa.Integer(), default=0),
        sa.Column("config", postgresql.JSONB(), default={}),
    )

    # automation_runs
    op.create_table("automation_runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("automation_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("automations.id"), nullable=False),
        sa.Column("entity_type", sa.String(50), nullable=False),
        sa.Column("entity_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("status", sa.String(30), default="running"),
        sa.Column("current_step", sa.Integer(), default=0),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # conversations
    op.create_table("conversations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("customer_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("customers.id")),
        sa.Column("deal_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("deals.id")),
        sa.Column("channel", sa.String(20), nullable=False),
        sa.Column("external_id", sa.String(255)),
        sa.Column("customer_phone", sa.String(50)),
        sa.Column("customer_email", sa.String(255)),
        sa.Column("last_message_at", sa.DateTime(timezone=True)),
        sa.Column("is_resolved", sa.Boolean(), default=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_conversations_tenant_id", "conversations", ["tenant_id"])

    # messages
    op.create_table("messages",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("conversation_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("conversations.id"), nullable=False),
        sa.Column("direction", sa.String(10), nullable=False),
        sa.Column("channel", sa.String(20), nullable=False),
        sa.Column("from_address", sa.String(255)),
        sa.Column("to_address", sa.String(255)),
        sa.Column("subject", sa.String(500)),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("status", sa.String(30), default="sent"),
        sa.Column("provider_message_id", sa.String(255)),
        sa.Column("sent_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_messages_conversation_id", "messages", ["conversation_id"])

    # review_requests
    op.create_table("review_requests",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("deal_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("deals.id")),
        sa.Column("customer_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("customers.id")),
        sa.Column("token", sa.String(100), unique=True, nullable=False),
        sa.Column("status", sa.String(30), default="pending"),
        sa.Column("sent_at", sa.DateTime(timezone=True)),
        sa.Column("opened_at", sa.DateTime(timezone=True)),
        sa.Column("responded_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_review_requests_token", "review_requests", ["token"])

    # reviews
    op.create_table("reviews",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("review_request_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("review_requests.id")),
        sa.Column("customer_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("customers.id")),
        sa.Column("rating", sa.Integer(), nullable=False),
        sa.Column("feedback", sa.Text()),
        sa.Column("is_public", sa.Boolean(), default=False),
        sa.Column("routed_to_google", sa.Boolean(), default=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_reviews_tenant_id", "reviews", ["tenant_id"])

    # social_accounts
    op.create_table("social_accounts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("platform", sa.String(30), nullable=False),
        sa.Column("account_id", sa.String(255), nullable=False),
        sa.Column("page_id", sa.String(255)),
        sa.Column("access_token", sa.Text()),
        sa.Column("token_expires_at", sa.DateTime(timezone=True)),
        sa.Column("is_active", sa.Boolean(), default=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # social_posts
    op.create_table("social_posts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("deal_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("deals.id")),
        sa.Column("platform", sa.String(30), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("image_urls", postgresql.JSONB(), default=[]),
        sa.Column("status", sa.String(30), default="pending_approval"),
        sa.Column("scheduled_at", sa.DateTime(timezone=True)),
        sa.Column("published_at", sa.DateTime(timezone=True)),
        sa.Column("platform_post_id", sa.String(255)),
        sa.Column("error", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_social_posts_tenant_id", "social_posts", ["tenant_id"])

    # gdpr_requests
    op.create_table("gdpr_requests",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("customer_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("customers.id")),
        sa.Column("type", sa.String(20), nullable=False),
        sa.Column("status", sa.String(20), default="pending"),
        sa.Column("download_url", sa.Text()),
        sa.Column("expires_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
    )

    # Seed default subscription plans
    op.execute("""
        INSERT INTO subscription_plans (id, name, price_gbp_monthly, max_locations, max_leads_per_month, max_sms_per_month, max_users, has_social_posting, has_ai_content, has_white_label)
        VALUES
          (gen_random_uuid(), 'Starter', 99, 1, 500, 1000, 1, false, false, false),
          (gen_random_uuid(), 'Growth', 149, 3, 2000, 5000, 5, true, false, false),
          (gen_random_uuid(), 'Pro', 199, 100, 10000, 20000, 20, true, true, true)
    """)


def downgrade() -> None:
    for table in [
        "gdpr_requests", "social_posts", "social_accounts", "reviews", "review_requests",
        "messages", "conversations", "automation_runs", "automation_steps", "automations",
        "message_templates", "payments", "invoice_items", "invoices", "quote_items",
        "quotes", "quote_templates", "bookings", "availability_slots", "staff",
        "deal_activities", "deals", "customers", "leads", "lead_sources",
        "billing_invoices", "subscriptions", "audit_logs", "locations",
        "tenant_members", "refresh_tokens", "tenants", "users", "subscription_plans",
    ]:
        op.drop_table(table)
