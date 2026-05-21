"""RBAC: permission templates and per-tenant overrides.

Model:

* Every TenantMember has a `role` (e.g. `owner`, `manager`, `staff`,
  `customer_support`, `viewer`). Roles are free-form strings — there's no
  enum table — but we ship a default `PermissionTemplate` per built-in role.
* `PermissionTemplate` rows store `{role -> [permission strings]}` at the
  PLATFORM level. They are seeded on first boot and managed by super-admins.
* `TenantPermissionOverride` rows store tenant-scoped tweaks: a tenant can
  GRANT or REVOKE a specific permission for a specific role without forking
  the global template. This is the "hybrid RBAC" model.

Permission resolution at runtime (see `service.can`):

    perms = set(template.permissions for tenant's role)
    perms |= set(overrides where role=... and effect='grant')
    perms -= set(overrides where role=... and effect='revoke')

This is intentionally simple and is checked in-memory after a single DB read.
For deeply-nested resources you would also call `has_resource_access(user,
resource_id)` — but that's left to the resource module since it depends on
ownership rules.
"""
import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.db_types import JSONBType, UUIDType


# Built-in roles. Custom roles are allowed but these are the defaults we seed.
BUILT_IN_ROLES = ("owner", "manager", "staff", "customer_support", "viewer")


# Catalogue of every permission the app supports. Used by the settings UI to
# render the matrix of toggles. Format: "<resource>:<action>".
PERMISSION_CATALOGUE = [
    # CRM
    "crm.read", "crm.write", "crm.delete",
    "crm.import", "crm.export", "crm.merge", "crm.bulk", "crm.settings", "crm.assign",
    # Leads
    "leads.read", "leads.write", "leads.delete", "leads.score",
    # Tasks
    "tasks.read", "tasks.write", "tasks.delete", "tasks.assign",
    # Quotes & invoices
    "quotes.read", "quotes.write", "quotes.send", "quotes.delete",
    "invoices.read", "invoices.write", "invoices.send", "invoices.delete",
    "payments.read", "payments.refund",
    # Bookings / appointments
    "bookings.read", "bookings.write", "bookings.delete",
    # Reviews / reputation
    "reviews.read", "reviews.reply", "reviews.flag",
    # Social
    "social.read", "social.write", "social.publish",
    # Automations
    "automations.read", "automations.write", "automations.run",
    # Messaging
    "messaging.read", "messaging.send",
    # Customers (data subjects)
    "customers.read", "customers.write", "customers.delete", "customers.export",
    # Billing (the SaaS subscription, not invoices to customers)
    "billing.read", "billing.write",
    # AI
    "ai.use", "ai.assistant", "ai.lead_score", "ai.compose",
    # Team & settings
    "team.read", "team.invite", "team.remove", "team.set_role",
    "settings.read", "settings.write",
    "api_keys.read", "api_keys.write",
    # Analytics & reporting
    "analytics.read", "analytics.export",
    # Audit log
    "audit.read",
    # GDPR
    "gdpr.read", "gdpr.export", "gdpr.erase",
]


class PermissionTemplate(Base):
    """Default permission set for a role, platform-wide.

    Edited by super-admins; read by every tenant unless overridden.
    """

    __tablename__ = "permission_templates"

    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)
    role: Mapped[str] = mapped_column(String(50), nullable=False, unique=True, index=True)
    permissions: Mapped[list] = mapped_column(JSONBType, nullable=False, default=list)
    description: Mapped[str | None] = mapped_column(String(255))
    is_system: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class TenantPermissionOverride(Base):
    """A tenant-specific grant or revoke on top of the role template."""

    __tablename__ = "tenant_permission_overrides"
    __table_args__ = (
        UniqueConstraint("tenant_id", "role", "permission", "effect", name="uq_tpo_unique"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True
    )
    role: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    permission: Mapped[str] = mapped_column(String(80), nullable=False)
    effect: Mapped[str] = mapped_column(String(10), nullable=False)  # 'grant' | 'revoke'
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


# ── Seed: default permission set per built-in role ──────────────────────────
# Used by the migration and by /admin to reset to defaults.
DEFAULT_TEMPLATES: dict[str, list[str]] = {
    "owner": list(PERMISSION_CATALOGUE),  # everything
    "manager": [p for p in PERMISSION_CATALOGUE if not p.startswith(("billing.write", "team.remove", "gdpr.erase"))],
    "staff": [
        "crm.read", "crm.write", "crm.bulk", "crm.assign",
        "leads.read", "leads.write",
        "tasks.read", "tasks.write", "tasks.assign",
        "quotes.read", "quotes.write", "quotes.send",
        "invoices.read", "invoices.write", "invoices.send",
        "payments.read",
        "bookings.read", "bookings.write",
        "reviews.read", "reviews.reply",
        "social.read", "social.write",
        "automations.read",
        "messaging.read", "messaging.send",
        "customers.read", "customers.write",
        "ai.use", "ai.assistant", "ai.compose",
        "analytics.read",
    ],
    "customer_support": [
        "crm.read",
        "leads.read",
        "tasks.read", "tasks.write",
        "quotes.read",
        "invoices.read",
        "payments.read",
        "bookings.read",
        "reviews.read", "reviews.reply",
        "messaging.read", "messaging.send",
        "customers.read",
        "ai.use", "ai.compose",
    ],
    "viewer": [
        "crm.read", "leads.read", "tasks.read",
        "quotes.read", "invoices.read", "payments.read",
        "bookings.read", "reviews.read", "social.read",
        "automations.read", "messaging.read",
        "customers.read", "analytics.read", "audit.read",
    ],
}
