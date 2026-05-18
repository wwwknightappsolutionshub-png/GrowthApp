"""
Local development database setup — SQLite compatible.
Run: uv run python scripts/init_db.py
"""
import asyncio
import uuid
from datetime import datetime, timezone

from sqlalchemy import text

# Import the FastAPI app first — that single import force-loads every model
# module via main.py's noqa-imports, so Base.metadata sees the full schema
# (Phase 0 ↦ Phase 6, including tasks, notifications, api_keys, rbac, ai
# assistant, segments, auto-replies, outreach, landing pages, etc).
from app.main import app  # noqa: F401

# Phase 0 models we directly reference for seeding.
from app.modules.auth.models import User
from app.modules.billing.models import SubscriptionPlan

from app.core.database import engine, Base, AsyncSessionLocal
from app.core.security import hash_password


async def init_db():
    """Create all tables and seed initial data."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    print(f"Tables created: {list(Base.metadata.tables.keys())}")

    async with AsyncSessionLocal() as db:
        await seed_subscription_plans(db)
        await seed_demo_user(db)
        await db.commit()

        # Seed marketing CMS, public reviews and landing-page templates.
        from app.modules.marketing.seed import seed_marketing_data
        counts = await seed_marketing_data(db, replace=True)
        print(
            f"Marketing CMS seeded: {counts['sections']} sections, "
            f"{counts['reviews']} reviews, {counts['templates']} landing templates."
        )

        print("Database initialized and seeded successfully!")


async def seed_subscription_plans(db):
    result = await db.execute(text("SELECT COUNT(*) FROM subscription_plans"))
    count = result.scalar()
    if count > 0:
        print("Subscription plans already seeded.")
        return

    plans = [
        SubscriptionPlan(
            id=uuid.uuid4(),
            name="Starter",
            price_gbp_monthly=99,
            max_locations=1,
            max_leads_per_month=500,
            max_sms_per_month=1000,
            max_users=1,
            has_social_posting=False,
            has_ai_content=False,
            has_white_label=False,
        ),
        SubscriptionPlan(
            id=uuid.uuid4(),
            name="Growth",
            price_gbp_monthly=149,
            max_locations=3,
            max_leads_per_month=2000,
            max_sms_per_month=5000,
            max_users=5,
            has_social_posting=True,
            has_ai_content=False,
            has_white_label=False,
        ),
        SubscriptionPlan(
            id=uuid.uuid4(),
            name="Pro",
            price_gbp_monthly=199,
            max_locations=100,
            max_leads_per_month=10000,
            max_sms_per_month=20000,
            max_users=20,
            has_social_posting=True,
            has_ai_content=True,
            has_white_label=True,
        ),
    ]
    for plan in plans:
        db.add(plan)
    print("Seeded 3 subscription plans.")


async def seed_demo_user(db):
    result = await db.execute(text("SELECT COUNT(*) FROM users"))
    count = result.scalar()
    if count > 0:
        print("Users already exist.")
        return

    demo_user = User(
        id=uuid.uuid4(),
        email="demo@customerflow.ai",
        password_hash=hash_password("demo123"),
        full_name="Demo User",
        email_verified_at=datetime.now(timezone.utc),
    )
    db.add(demo_user)
    print("Created demo user: demo@customerflow.ai / demo123")


if __name__ == "__main__":
    asyncio.run(init_db())
