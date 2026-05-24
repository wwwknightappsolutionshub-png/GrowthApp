import asyncio
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.core.config import settings
from app.core.database import Base, get_db
from app.core.middleware import limiter
from app.main import app
from app.modules.crm import pipeline_models as _crm_pipeline_models  # noqa: F401 — CRM enterprise tables
from app.modules.accounting import models as _accounting_models  # noqa: F401
from app.modules.integrations import models as _integrations_models  # noqa: F401


def _derive_test_db_url() -> str:
    """Produce a test DB URL distinct from the dev one."""
    url = settings.DATABASE_URL
    if url.startswith("sqlite"):
        return "sqlite+aiosqlite:///./customerflow_test.db"
    # If DATABASE_URL already points at a *_test database (CI sets this), use
    # it directly. Otherwise append `_test` to the DB name so we never write
    # to the real database.
    db_part = url.rsplit("/", 1)[-1]
    if "_test" in db_part:
        return url
    # Insert `_test` before any query string so postgres-style URLs work too.
    base, sep, query = url.rpartition("?") if "?" in url else (url, "", "")
    target = base or url
    return f"{target}_test{sep}{query}" if base else f"{target}_test"


TEST_DATABASE_URL = _derive_test_db_url()
IS_POSTGRES = TEST_DATABASE_URL.startswith("postgresql")


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def test_engine():
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

        # Recreate the production hardening in this fresh schema:
        if IS_POSTGRES:
            from sqlalchemy import text as sa_text

            # Apply RLS policies on the metadata-created schema so tests see
            # the production behaviour. We replicate migration 003 here in
            # the simplest possible form because we use create_all instead of
            # alembic for speed.
            tenant_tables = [
                "tenants", "tenant_members", "locations", "subscriptions",
                "billing_invoices", "audit_logs", "lead_sources", "leads",
                "customers", "deals", "deal_activities", "staff",
                "availability_slots", "bookings", "quote_templates",
                "quotes", "invoices", "payments", "message_templates",
                "automations", "automation_runs", "conversations", "messages",
                "review_requests", "reviews", "social_accounts", "social_posts",
                "gdpr_requests",
                # Phase 1 additions
                "tasks", "notifications", "api_keys", "tenant_permission_overrides",
                "ai_usage_events",
                # Phase 2 additions
                "ai_assistant_threads", "ai_assistant_messages",
                "customer_segments", "auto_replies",
            ]
            tenant_column_overrides = {"tenants": "id"}
            for table in tenant_tables:
                col = tenant_column_overrides.get(table, "tenant_id")
                await conn.execute(sa_text(f'ALTER TABLE "{table}" ENABLE ROW LEVEL SECURITY'))
                await conn.execute(sa_text(f'ALTER TABLE "{table}" FORCE ROW LEVEL SECURITY'))
                await conn.execute(sa_text(f'DROP POLICY IF EXISTS tenant_isolation ON "{table}"'))
                await conn.execute(sa_text(f"""
                    CREATE POLICY tenant_isolation ON "{table}"
                    USING (
                        current_setting('app.current_tenant', true) = ''
                        OR current_setting('app.current_tenant', true) IS NULL
                        OR "{col}"::text = current_setting('app.current_tenant', true)
                    )
                    WITH CHECK (
                        current_setting('app.current_tenant', true) = ''
                        OR current_setting('app.current_tenant', true) IS NULL
                        OR "{col}"::text = current_setting('app.current_tenant', true)
                    )
                """))

            # Install the next_tenant_number function so the service layer
            # can exercise the production code path.
            await conn.execute(sa_text("""
                CREATE OR REPLACE FUNCTION next_tenant_number(p_tenant_id uuid, p_kind text)
                RETURNS integer LANGUAGE plpgsql AS $$
                DECLARE v_next integer;
                BEGIN
                    IF p_kind = 'quote' THEN
                        UPDATE tenants SET last_quote_number = last_quote_number + 1
                        WHERE id = p_tenant_id RETURNING last_quote_number INTO v_next;
                    ELSIF p_kind = 'invoice' THEN
                        UPDATE tenants SET last_invoice_number = last_invoice_number + 1
                        WHERE id = p_tenant_id RETURNING last_invoice_number INTO v_next;
                    ELSE
                        RAISE EXCEPTION 'unknown numbering kind: %', p_kind;
                    END IF;
                    RETURN v_next;
                END; $$
            """))

    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(test_engine):
    TestSession = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)
    async with TestSession() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def client(db_session, request):
    """
    HTTP client. By default rate limiting is disabled so unrelated tests aren't
    affected by per-IP counters bleeding across them. Tests that specifically
    want to exercise the limiter mark themselves with @pytest.mark.ratelimited
    and the fixture re-enables it.
    """
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    wants_ratelimit = "ratelimited" in request.keywords
    prev_enabled = limiter.enabled
    limiter.enabled = wants_ratelimit
    _reset_limiter()

    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            yield c
    finally:
        limiter.enabled = prev_enabled
        app.dependency_overrides.clear()


def _reset_limiter() -> None:
    """Best-effort wipe of the slowapi limiter's storage between tests."""
    for path in (
        ("reset",),
        ("limiter", "reset"),
        ("limiter", "storage", "reset"),
        ("_storage", "reset"),
        ("_storage", "clear"),
    ):
        target = limiter
        try:
            for attr in path[:-1]:
                target = getattr(target, attr)
            fn = getattr(target, path[-1])
            if callable(fn):
                fn()
                return
        except Exception:
            continue


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "ratelimited: enable the slowapi rate limiter for this test",
    )


@pytest.fixture
def is_postgres() -> bool:
    """Tests that require PostgreSQL features should skip when this is False."""
    return IS_POSTGRES


postgres_only = pytest.mark.skipif(
    not IS_POSTGRES,
    reason="Test requires PostgreSQL (RLS / SQL functions / etc.)",
)
