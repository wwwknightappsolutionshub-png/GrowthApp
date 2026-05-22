#!/usr/bin/env python3
"""Create or update a super-admin user (run on server with production .env).

Usage:
  cd /www/wwwroot/customerflow/apps/api
  source .venv/bin/activate
  python scripts/ensure_superadmin.py --email you@example.com --password 'YourSecurePass1!'

Or:
  SUPERADMIN_EMAIL=... SUPERADMIN_PASSWORD=... python scripts/ensure_superadmin.py
"""
from __future__ import annotations

import argparse
import asyncio
import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

# Run from apps/api so .env and imports resolve.
API_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(API_ROOT))
os.chdir(API_ROOT)

from sqlalchemy import select, text

# Register ORM relationships before touching User.
from app.modules.auth.models import User  # noqa: F401
from app.modules.tenants.models import Tenant, TenantMember  # noqa: F401

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.core.security import hash_password


async def _verify_row(email: str) -> tuple[bool, bool, str | None]:
    async with AsyncSessionLocal() as db:
        row = (
            await db.execute(
                text(
                    """
                    SELECT is_superadmin, deleted_at IS NULL AS active
                    FROM users WHERE lower(email) = lower(:email)
                    """
                ),
                {"email": email},
            )
        ).mappings().first()
        if not row:
            return False, False, None
        return bool(row["is_superadmin"]), bool(row["active"]), None


async def main(email: str, password: str, full_name: str) -> None:
    email = email.strip().lower()
    if len(password) < 10:
        raise SystemExit("Password must be at least 10 characters.")

    db_url = settings.DATABASE_URL
    if "sqlite" in db_url and os.environ.get("ENVIRONMENT") == "production":
        raise SystemExit(
            "DATABASE_URL points at SQLite but ENVIRONMENT=production. "
            "Run from apps/api with a valid .env (postgresql+asyncpg://...)."
        )

    print(f"Database: {db_url.split('@')[-1] if '@' in db_url else db_url}")

    now = datetime.now(timezone.utc)
    pwd_hash = hash_password(password)

    async with AsyncSessionLocal() as db:
        user = (await db.execute(select(User).where(User.email == email))).scalar_one_or_none()
        if user:
            user.password_hash = pwd_hash
            user.is_superadmin = True
            user.deleted_at = None
            user.email_verified_at = user.email_verified_at or now
            user.onboarding_completed = True
            user.totp_backup_codes = user.totp_backup_codes if user.totp_backup_codes is not None else []
            if full_name:
                user.full_name = full_name
            db.add(user)
            action = "updated"
            user_id = user.id
        else:
            user = User(
                id=uuid.uuid4(),
                email=email,
                full_name=full_name or "Super Admin",
                password_hash=pwd_hash,
                is_superadmin=True,
                user_type="tenant",
                email_verified_at=now,
                onboarding_completed=True,
                totp_backup_codes=[],
            )
            db.add(user)
            await db.flush()
            action = "created"
            user_id = user.id
        await db.commit()

    is_sa, active, _ = await _verify_row(email)
    if not is_sa or not active:
        raise SystemExit(
            f"FAILED: user {email!r} not active super-admin after commit "
            f"(is_superadmin={is_sa}, active={active})."
        )

    print(f"Super admin {action} successfully.")
    print(f"  User id:  {user_id}")
    print(f"  Email:    {email}")
    print(f"  Verified: is_superadmin=True, deleted_at=NULL")
    print("  Login:    https://customerflowai.online/login  →  /admin")
    print("  Password: (the value you passed — not stored in this script)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ensure a super-admin account exists")
    parser.add_argument("--email", default=os.environ.get("SUPERADMIN_EMAIL"))
    parser.add_argument("--password", default=os.environ.get("SUPERADMIN_PASSWORD"))
    parser.add_argument("--name", default=os.environ.get("SUPERADMIN_NAME", "Super Admin"))
    args = parser.parse_args()
    if not args.email or not args.password:
        parser.error("Provide --email and --password (or SUPERADMIN_EMAIL / SUPERADMIN_PASSWORD)")
    try:
        asyncio.run(main(args.email, args.password, args.name))
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
