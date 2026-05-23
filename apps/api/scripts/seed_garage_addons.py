#!/usr/bin/env python3
"""Seed Knight Motors garage demo tenant with all industry add-ons.

Usage (from apps/api):
  .venv\\Scripts\\python.exe scripts/seed_garage_addons.py

Writes to customerflow_garage_demo.db by default (full schema).
To use with the running API, set in .env:
  DATABASE_URL=sqlite+aiosqlite:///./customerflow_garage_demo.db

Idempotent — safe to re-run.
"""
from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

API_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(API_ROOT))
os.chdir(API_ROOT)

# Dedicated demo DB so local dev.sqlite mismatches do not block seeding.
DEMO_DB = API_ROOT / "customerflow_garage_demo.db"
os.environ.setdefault("DATABASE_URL", f"sqlite+aiosqlite:///{DEMO_DB.as_posix()}")

from sqlalchemy import select

from app.core.database import AsyncSessionLocal, Base, engine
from app.main import app as _app  # noqa: F401 — register all models
from app.modules.addons import industry_models  # noqa: F401
from app.modules.addons.common.models import TenantIndustryProfile  # noqa: F401
from app.modules.addons.seed_garage import (
    GARAGE_DEMO_EMAIL,
    GARAGE_DEMO_PASSWORD,
    GARAGE_DEMO_NAME,
    GARAGE_DEMO_SLUG,
    ensure_garage_demo_tenant,
)
from app.modules.billing.models import SubscriptionPlan


async def _ensure_schema() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def main() -> None:
    await _ensure_schema()
    print(f"Database: {DEMO_DB}")

    async with AsyncSessionLocal() as db:
        plans: dict | None = None
        try:
            await db.execute(select(SubscriptionPlan).limit(1))
            plans_rows = (await db.execute(select(SubscriptionPlan))).scalars().all()
            if not plans_rows:
                from scripts.seed_data import seed_plans

                plans = await seed_plans(db)
            else:
                plans = {p.name: p for p in plans_rows}
        except Exception:
            plans = None

        result = await ensure_garage_demo_tenant(db, plans=plans)

    print("\nOK: Garage industry add-ons demo seeded\n")
    print("=" * 62)
    print("  GARAGE DEMO LOGIN")
    print("=" * 62)
    print(f"  Email    : {GARAGE_DEMO_EMAIL}")
    print(f"  Password : {GARAGE_DEMO_PASSWORD}")
    print(f"  Business : {GARAGE_DEMO_NAME}")
    print(f"  Slug     : {GARAGE_DEMO_SLUG}")
    print()
    print("  Industry add-ons: booking + billing + CRM (all active)")
    print("  Vertical: garage (default settings applied)")
    print()
    print(f"  Sample data: {result.get('customers', 0)} customers, "
          f"{result.get('vehicles', 0)} vehicles, {result.get('parts', 0)} parts, "
          f"{result.get('bookings', 0)} bookings")
    print()
    print("  API .env (if not already):")
    print(f"    DATABASE_URL=sqlite+aiosqlite:///./customerflow_garage_demo.db")
    print()
    print("  Preview:")
    print("    http://localhost:3000/login")
    print("    http://localhost:3000/dashboard/addons/booking")
    print("=" * 62)
    print()


if __name__ == "__main__":
    asyncio.run(main())
