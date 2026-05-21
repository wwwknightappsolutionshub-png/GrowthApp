import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

from app.core.config import settings
from app.core.database import Base  # noqa: F401 — ensures all models are registered

# Import all models so Alembic can detect them
from app.modules.auth.models import User, RefreshToken  # noqa: F401
from app.modules.tenants.models import Tenant, TenantMember, Location  # noqa: F401
from app.modules.billing.models import SubscriptionPlan, Subscription, BillingInvoice  # noqa: F401
from app.modules.leads.models import Lead, LeadSource  # noqa: F401
from app.modules.crm.models import Customer, Deal, DealActivity  # noqa: F401
from app.modules.booking.models import Staff, AvailabilitySlot, Booking  # noqa: F401
from app.modules.booking.enterprise_models import (  # noqa: F401
    BookingAbandonedSession,
    BookingCalendarConnection,
    BookingCustomerCredit,
    BookingNotificationQueue,
    BookingPackage,
    BookingPromoCode,
    BookingResource,
    BookingService,
    BookingSettings,
    StaffBlackout,
    StaffShift,
)
from app.modules.quotes_invoices.models import (  # noqa: F401
    QuoteTemplate, Quote, QuoteItem, Invoice, InvoiceItem, Payment
)
from app.modules.automation.models import (  # noqa: F401
    Automation, AutomationStep, AutomationRun, MessageTemplate
)
from app.modules.messaging.models import Conversation, Message  # noqa: F401
from app.modules.reputation.models import ReviewRequest, Review  # noqa: F401
from app.modules.social.models import (  # noqa: F401
    SocialAccount, SocialPost,
    SocialBrandIdentity, SocialSampleUploads, SocialPostingPreferences,
    SocialContentDraft, SocialApprovalQueue, SocialScheduleQueue,
)
from app.modules.marketer.models import (  # noqa: F401
    MarketerFunnelBlueprint, AudienceResearchReport,
    CompetitorIntelligenceReport, MarketerQuota,
)
from app.modules.audit.models import AuditLog  # noqa: F401
from app.modules.gdpr.models import GdprRequest  # noqa: F401
from app.modules.integrations.models import TenantGoogleConnection, GoogleBusinessReview  # noqa: F401
from app.modules.lead_marketplace.trial_models import TrialLeadDelivery  # noqa: F401

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def get_url() -> str:
    return settings.DATABASE_URL


def run_migrations_offline() -> None:
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    configuration = config.get_section(config.config_ini_section, {})
    configuration["sqlalchemy.url"] = get_url()
    connectable = async_engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
