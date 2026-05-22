#!/usr/bin/env python3
"""Create or update a super-admin user (run on server with production .env).

Usage:
  cd apps/api && source .venv/bin/activate
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

# Allow running from apps/api
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select

# Register ORM relationships (User → TenantMember, etc.) before querying.
from app.modules.auth.models import User  # noqa: F401
from app.modules.tenants.models import Tenant, TenantMember  # noqa: F401

from app.core.database import AsyncSessionLocal
from app.core.security import hash_password


async def main(email: str, password: str, full_name: str) -> None:
    email = email.strip().lower()
    if len(password) < 10:
        raise SystemExit("Password must be at least 10 characters.")

    async with AsyncSessionLocal() as db:
        user = (await db.execute(select(User).where(User.email == email))).scalar_one_or_none()
        if user:
            user.password_hash = hash_password(password)
            user.is_superadmin = True
            user.deleted_at = None
            if full_name:
                user.full_name = full_name
            db.add(user)
            action = "updated"
        else:
            user = User(
                id=uuid.uuid4(),
                email=email,
                full_name=full_name or "Super Admin",
                password_hash=hash_password(password),
                is_superadmin=True,
                user_type="tenant",
            )
            db.add(user)
            action = "created"
        await db.commit()

    print(f"Super admin {action} successfully.")
    print(f"  Email:    {email}")
    print(f"  Login:    /login  (then /admin)")
    print("  Password: (the value you passed — not stored in this script)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ensure a super-admin account exists")
    parser.add_argument("--email", default=os.environ.get("SUPERADMIN_EMAIL"))
    parser.add_argument("--password", default=os.environ.get("SUPERADMIN_PASSWORD"))
    parser.add_argument("--name", default=os.environ.get("SUPERADMIN_NAME", "Super Admin"))
    args = parser.parse_args()
    if not args.email or not args.password:
        parser.error("Provide --email and --password (or SUPERADMIN_EMAIL / SUPERADMIN_PASSWORD)")
    asyncio.run(main(args.email, args.password, args.name))
