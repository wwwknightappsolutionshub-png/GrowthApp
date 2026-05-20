from contextlib import asynccontextmanager

import sentry_sdk
from fastapi import FastAPI
from fastapi.responses import ORJSONResponse

from app.core.config import settings
from app.core.middleware import setup_middleware

# Module routers
from app.modules.auth.router import router as auth_router
from app.modules.tenants.router import router as tenants_router
from app.modules.leads.router import router as leads_router
from app.modules.crm.router import router as crm_router
from app.modules.booking.router import router as booking_router
from app.modules.quotes_invoices.router import router as quotes_router
from app.modules.automation.router import router as automation_router
from app.modules.messaging.router import router as messaging_router
from app.modules.reputation.router import router as reputation_router
from app.modules.integrations.router import router as integrations_router
from app.modules.integrations import models as _integrations_models  # noqa: F401
from app.modules.social.router import router as social_router
from app.modules.social.ai_router import ai_router as social_ai_router
from app.modules.marketer.router import router as marketer_router
from app.modules.billing.router import router as billing_router
from app.modules.landing_pages.router import router as landing_pages_router
from app.modules.gdpr.router import router as gdpr_router
from app.modules.public.router import router as public_router
from app.modules.webhooks.router import router as webhooks_router
from app.modules.admin.router import router as admin_router
from app.modules.tasks.router import router as tasks_router
from app.modules.notifications.router import router as notifications_router
from app.modules.api_keys.router import router as api_keys_router
from app.modules.rbac.router import router as rbac_router
from app.modules.search.router import router as search_router
from app.modules.ai.router import router as ai_router
from app.modules.ai_assistant.router import router as ai_assistant_router
from app.modules.segments.router import router as segments_router
from app.modules.money.router import router as money_router
from app.modules.auto_replies.router import router as auto_replies_router
from app.modules.usage.router import router as usage_router
from app.modules.outreach.router import router as outreach_router
from app.modules.whatsapp.router import router as whatsapp_router
from app.modules.marketing.router import (
    admin_router as marketing_admin_router,
    public_router as marketing_public_router,
    tenant_router as marketing_tenant_router,
)
# Force-load AI service so AIUsageEvent is registered with Base.metadata
from app.services import ai as _ai  # noqa: F401
# Force-load ai_assistant + segments models so they're registered with Base.metadata
from app.modules.ai_assistant import models as _ai_assistant_models  # noqa: F401
from app.modules.segments import models as _segments_models  # noqa: F401
from app.modules.auto_replies import models as _auto_replies_models  # noqa: F401
from app.modules.outreach import models as _outreach_models  # noqa: F401
from app.modules.landing_pages import models as _landing_pages_models  # noqa: F401
from app.modules.marketing import models as _marketing_models  # noqa: F401
from app.modules.referrals import models as _referrals_models  # noqa: F401
from app.modules.marketer import models as _marketer_models  # noqa: F401
from app.modules.auth import models as _auth_models  # noqa: F401
from app.modules.auth import otp_models as _auth_otp_models  # noqa: F401
from app.modules.tenants import models as _tenant_models  # noqa: F401
from app.modules.referrals.router import router as referrals_router
from app.modules.ai_scraper import models as _ai_scraper_models  # noqa: F401
from app.modules.ai_scraper.router import router as ai_scraper_router
# Force-load business category config model
from app.modules.admin import tool_config as _tool_config_models  # noqa: F401
# Lead Marketplace
from app.modules.lead_marketplace import models as _lead_marketplace_models  # noqa: F401
from app.modules.lead_marketplace.router import router as lead_marketplace_router
# RBAC + Admin support models
from app.core import rbac as _rbac_models  # noqa: F401
# Super Admin API routers (app/api/admin/ structure)
from app.api.admin.dashboard import router as admin_dash_router
from app.api.admin.tenants import router as admin_tenants_router
from app.api.admin.marketplace import router as admin_marketplace_router
from app.api.admin.scraper_sources import router as admin_scraper_sources_router
from app.api.admin.scraper_tasks import router as admin_scraper_tasks_router
from app.api.admin.scraper_results import router as admin_scraper_results_router
from app.api.admin.ai_engine import router as admin_ai_engine_router
from app.api.admin.referrals import router as admin_referrals_router
from app.api.admin.billing import router as admin_billing_router
from app.api.admin.users import router as admin_users_router
from app.api.admin.communications import router as admin_comms_router
from app.api.admin.operations import router as admin_ops_router
from app.api.admin.settings import router as admin_settings_router
from app.api.admin.support import router as admin_support_router
from app.api.admin.email_templates import router as admin_email_templates_router
# Content management
from app.modules.content import models as _content_models  # noqa: F401
from app.api.admin.content import router as admin_content_router
from app.api.admin.content import public_router as content_public_router
from app.api.admin.social import router as admin_social_router
from app.api.admin.marketer_tools import router as admin_marketer_router
from app.api.admin.freelancer_management import router as admin_freelancer_router
from app.api.admin.billing_inspector import router as admin_billing_inspector_router
from app.modules.billing.freelancer_self_router import router as freelancer_billing_self_router
from app.modules.freelancer.clients_router import router as freelancer_clients_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    if settings.SENTRY_DSN:
        sentry_sdk.init(
            dsn=settings.SENTRY_DSN,
            environment=settings.ENVIRONMENT,
            traces_sample_rate=0.1,
        )
    yield
    # Shutdown (cleanup if needed)


def create_app() -> FastAPI:
    app = FastAPI(
        title="CustomerFlow AI API",
        description="CustomerFlow AI — All-in-one AI platform for UK businesses",
        version="1.0.0",
        default_response_class=ORJSONResponse,
        lifespan=lifespan,
        docs_url="/docs" if not settings.is_production else None,
        redoc_url="/redoc" if not settings.is_production else None,
    )

    setup_middleware(app)

    API_PREFIX = "/api/v1"

    app.include_router(auth_router, prefix=API_PREFIX)
    app.include_router(tenants_router, prefix=API_PREFIX)
    app.include_router(leads_router, prefix=API_PREFIX)
    app.include_router(crm_router, prefix=API_PREFIX)
    app.include_router(booking_router, prefix=API_PREFIX)
    app.include_router(quotes_router, prefix=API_PREFIX)
    app.include_router(automation_router, prefix=API_PREFIX)
    app.include_router(messaging_router, prefix=API_PREFIX)
    app.include_router(reputation_router, prefix=API_PREFIX)
    app.include_router(integrations_router, prefix=API_PREFIX)
    app.include_router(social_router, prefix=API_PREFIX)
    app.include_router(social_ai_router, prefix=API_PREFIX)
    app.include_router(marketer_router, prefix=API_PREFIX)
    app.include_router(billing_router, prefix=API_PREFIX)
    app.include_router(landing_pages_router, prefix=API_PREFIX)
    app.include_router(gdpr_router, prefix=API_PREFIX)
    app.include_router(public_router, prefix=API_PREFIX)
    app.include_router(webhooks_router, prefix=API_PREFIX)
    app.include_router(admin_router, prefix=API_PREFIX)
    app.include_router(tasks_router, prefix=API_PREFIX)
    app.include_router(notifications_router, prefix=API_PREFIX)
    app.include_router(api_keys_router, prefix=API_PREFIX)
    app.include_router(rbac_router, prefix=API_PREFIX)
    app.include_router(search_router, prefix=API_PREFIX)
    app.include_router(ai_router, prefix=API_PREFIX)
    app.include_router(ai_assistant_router, prefix=API_PREFIX)
    app.include_router(segments_router, prefix=API_PREFIX)
    app.include_router(money_router, prefix=API_PREFIX)
    app.include_router(auto_replies_router, prefix=API_PREFIX)
    app.include_router(usage_router, prefix=API_PREFIX)
    app.include_router(outreach_router, prefix=API_PREFIX)
    app.include_router(whatsapp_router, prefix=API_PREFIX)
    app.include_router(marketing_admin_router, prefix=API_PREFIX)
    app.include_router(marketing_tenant_router, prefix=API_PREFIX)
    app.include_router(marketing_public_router, prefix=API_PREFIX)
    app.include_router(referrals_router, prefix="/api")
    app.include_router(ai_scraper_router, prefix="/api")
    app.include_router(lead_marketplace_router, prefix="/api")
    # Super Admin API — /api/admin/
    app.include_router(admin_dash_router)
    app.include_router(admin_tenants_router)
    app.include_router(admin_marketplace_router)
    app.include_router(admin_scraper_sources_router)
    app.include_router(admin_scraper_tasks_router)
    app.include_router(admin_scraper_results_router)
    app.include_router(admin_ai_engine_router)
    app.include_router(admin_referrals_router)
    app.include_router(admin_billing_router)
    app.include_router(admin_users_router)
    app.include_router(admin_comms_router)
    app.include_router(admin_ops_router)
    app.include_router(admin_settings_router)
    app.include_router(admin_support_router)
    app.include_router(admin_email_templates_router)
    app.include_router(admin_content_router)
    app.include_router(content_public_router)
    app.include_router(admin_social_router)
    app.include_router(admin_marketer_router)
    app.include_router(admin_freelancer_router)
    app.include_router(admin_billing_inspector_router)
    app.include_router(freelancer_billing_self_router)
    app.include_router(freelancer_clients_router)

    @app.get("/healthz", include_in_schema=False)
    async def health():
        return {"status": "ok", "version": "1.0.0"}

    return app


app = create_app()
