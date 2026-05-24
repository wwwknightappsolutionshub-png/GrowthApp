#!/usr/bin/env python3
"""Create or reset a tenant business-owner account (run on server with production .env).

Usage:
  cd /www/wwwroot/customerflow/apps/api
  source .venv/bin/activate
  python scripts/create_tenant_owner.py \\
    --email owner@example.com \\
    --password 'LivingPrieshood329@' \\
    --name 'Jane Owner' \\
    --business 'Example Plumbing Ltd' \\
    --type plumber \\
    --postcode 'SW1A 1AA'
"""
from __future__ import annotations

import argparse
import asyncio
import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

API_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(API_ROOT))
os.chdir(API_ROOT)

from sqlalchemy import select, text

from app.modules.auth.models import User  # noqa: F401
from app.modules.tenants.models import Tenant, TenantMember  # noqa: F401

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.core.security import hash_password
from app.modules.tenants.service import unique_tenant_slug


async def main(
    email: str,
    password: str,
    full_name: str,
    business_name: str,
    business_type: str,
    postcode: str,
) -> None:
    email = email.strip().lower()
    if len(password) < 8:
        raise SystemExit("Password must be at least 8 characters.")

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
            user.deleted_at = None
            user.email_verified_at = user.email_verified_at or now
            user.full_name = full_name or user.full_name
            user.totp_backup_codes = user.totp_backup_codes if user.totp_backup_codes is not None else []
            db.add(user)
            action = "updated"
        else:
            user = User(
                id=uuid.uuid4(),
                email=email,
                full_name=full_name,
                password_hash=pwd_hash,
                user_type="tenant",
                email_verified_at=now,
                onboarding_completed=False,
                totp_backup_codes=[],
            )
            db.add(user)
            await db.flush()
            action = "created"

        member = (
            await db.execute(
                select(TenantMember)
                .where(TenantMember.user_id == user.id, TenantMember.role == "owner")
                .limit(1)
            )
        ).scalar_one_or_none()

        if member:
            tenant = (await db.execute(select(Tenant).where(Tenant.id == member.tenant_id))).scalar_one()
            tenant.name = business_name
            tenant.business_type = business_type
            tenant.postcode = postcode.upper()
            db.add(tenant)
            tenant_action = "updated"
            slug = tenant.slug
        else:
            slug = await unique_tenant_slug(db, business_name)
            tenant = Tenant(
                id=uuid.uuid4(),
                slug=slug,
                name=business_name,
                business_type=business_type,
                postcode=postcode.upper(),
            )
            db.add(tenant)
            await db.flush()
            db.add(
                TenantMember(
                    id=uuid.uuid4(),
                    tenant_id=tenant.id,
                    user_id=user.id,
                    role="owner",
                    joined_at=now,
                )
            )
            tenant_action = "created"

        await db.commit()

    async with AsyncSessionLocal() as db:
        row = (
            await db.execute(
                text(
                    """
                    SELECT u.email, t.slug, t.name
                    FROM users u
                    JOIN tenant_members tm ON tm.user_id = u.id AND tm.role = 'owner'
                    JOIN tenants t ON t.id = tm.tenant_id
                    WHERE lower(u.email) = lower(:email) AND u.deleted_at IS NULL
                    LIMIT 1
                    """
                ),
                {"email": email},
            )
        ).mappings().first()
        if not row:
            raise SystemExit(f"FAILED: could not verify tenant owner {email!r} after commit.")

    print(f"Tenant owner {action} successfully.")
    print(f"  Email:    {email}")
    print(f"  Business: {row['name']} ({row['slug']})")
    print(f"  Tenant:   {tenant_action}")
    print("  Login:    https://customerflowai.online/login  →  /dashboard")
    print("  Password: (the value you passed — not stored in this script)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create or update a tenant business-owner account")
    parser.add_argument("--email", required=True)
    parser.add_argument("--password", required=True)
    parser.add_argument("--name", required=True, help="Full name")
    parser.add_argument("--business", required=True, help="Business name")
    parser.add_argument("--type", default="other", dest="business_type", help="Business type slug")
    parser.add_argument("--postcode", default="SW1A 1AA")
    args = parser.parse_args()
    try:
        asyncio.run(
            main(
                args.email,
                args.password,
                args.name,
                args.business,
                args.business_type,
                args.postcode,
            )
        )
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
