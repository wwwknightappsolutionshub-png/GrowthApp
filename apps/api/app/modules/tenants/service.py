import re
import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import log_action
from app.core.exceptions import ConflictException, NotFoundException
from app.core.security import hash_password, create_short_lived_token
from app.modules.auth.models import User
from app.modules.tenants.models import Location, Tenant, TenantMember
from app.modules.tenants.schemas import LocationCreate, LocationUpdate, TenantUpdate


def _slugify(name: str) -> str:
    """Convert a business name to a URL-safe slug."""
    slug = name.lower().strip()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[-\s]+", "-", slug)
    return slug[:100]


async def resolve_primary_tenant_membership(
    db: AsyncSession,
    user_id: uuid.UUID,
    *,
    prefer_freelancer_clients: bool = False,
) -> tuple[TenantMember, Tenant] | None:
    """Pick the user's primary active tenant membership for JWT / RLS context."""
    order = [TenantMember.created_at]
    if prefer_freelancer_clients:
        order = [Tenant.is_managed_client.desc(), TenantMember.created_at]
    row = (
        await db.execute(
            select(TenantMember, Tenant)
            .join(Tenant, TenantMember.tenant_id == Tenant.id)
            .where(
                TenantMember.user_id == user_id,
                Tenant.is_active == True,  # noqa: E712
            )
            .order_by(*order)
            .limit(1)
        )
    ).first()
    if not row:
        return None
    return row[0], row[1]


async def update_tenant(
    db: AsyncSession,
    tenant: Tenant,
    data: TenantUpdate,
    *,
    actor_user_id: uuid.UUID | None = None,
) -> Tenant:
    changed = data.model_dump(exclude_none=True)
    for field, value in changed.items():
        setattr(tenant, field, value)
    db.add(tenant)
    await log_action(
        db,
        action="tenant.updated",
        resource="tenant",
        resource_id=tenant.id,
        tenant_id=tenant.id,
        user_id=actor_user_id,
        metadata={"fields": sorted(changed.keys())},
    )
    await db.commit()
    await db.refresh(tenant)
    return tenant


async def list_members(db: AsyncSession, tenant_id: uuid.UUID) -> list[TenantMember]:
    result = await db.execute(
        select(TenantMember).where(TenantMember.tenant_id == tenant_id)
    )
    return list(result.scalars().all())


async def invite_member(
    db: AsyncSession,
    tenant: Tenant,
    email: str,
    full_name: str,
    role: str,
    *,
    actor_user_id: uuid.UUID | None = None,
) -> User:
    existing_user = await db.execute(select(User).where(User.email == email))
    user = existing_user.scalar_one_or_none()
    if not user:
        user = User(
            id=uuid.uuid4(),
            email=email,
            full_name=full_name,
            password_hash=hash_password(uuid.uuid4().hex),
        )
        db.add(user)
        await db.flush()

    existing_member = await db.execute(
        select(TenantMember).where(
            TenantMember.tenant_id == tenant.id,
            TenantMember.user_id == user.id,
        )
    )
    if existing_member.scalar_one_or_none():
        raise ConflictException("User is already a member of this tenant")

    member = TenantMember(
        id=uuid.uuid4(),
        tenant_id=tenant.id,
        user_id=user.id,
        role=role,
        invited_at=datetime.now(timezone.utc),
    )
    db.add(member)
    await log_action(
        db,
        action="member.invited",
        resource="tenant_member",
        resource_id=member.id,
        tenant_id=tenant.id,
        user_id=actor_user_id,
        metadata={"invited_email": email, "role": role},
    )
    await db.commit()
    return user


async def remove_member(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
    *,
    actor_user_id: uuid.UUID | None = None,
) -> None:
    result = await db.execute(
        select(TenantMember).where(
            TenantMember.tenant_id == tenant_id,
            TenantMember.user_id == user_id,
        )
    )
    member = result.scalar_one_or_none()
    if not member:
        raise NotFoundException("Member")
    await log_action(
        db,
        action="member.removed",
        resource="tenant_member",
        resource_id=member.id,
        tenant_id=tenant_id,
        user_id=actor_user_id,
        metadata={"removed_user_id": str(user_id), "role": member.role},
    )
    await db.delete(member)
    await db.commit()


async def list_locations(db: AsyncSession, tenant_id: uuid.UUID) -> list[Location]:
    result = await db.execute(
        select(Location).where(Location.tenant_id == tenant_id)
    )
    return list(result.scalars().all())


async def create_location(
    db: AsyncSession,
    tenant: Tenant,
    data: LocationCreate,
    *,
    actor_user_id: uuid.UUID | None = None,
) -> Location:
    existing = await db.execute(
        select(Location).where(Location.tenant_id == tenant.id, Location.slug == data.slug)
    )
    if existing.scalar_one_or_none():
        raise ConflictException("A location with this slug already exists")

    loc = Location(id=uuid.uuid4(), tenant_id=tenant.id, **data.model_dump())
    db.add(loc)
    await log_action(
        db,
        action="location.created",
        resource="location",
        resource_id=loc.id,
        tenant_id=tenant.id,
        user_id=actor_user_id,
        metadata={"name": data.name, "slug": data.slug},
    )
    await db.commit()
    await db.refresh(loc)
    return loc


async def update_location(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    loc_id: uuid.UUID,
    data: LocationUpdate,
    *,
    actor_user_id: uuid.UUID | None = None,
) -> Location:
    result = await db.execute(
        select(Location).where(Location.id == loc_id, Location.tenant_id == tenant_id)
    )
    loc = result.scalar_one_or_none()
    if not loc:
        raise NotFoundException("Location")
    changed = data.model_dump(exclude_none=True)
    for field, value in changed.items():
        setattr(loc, field, value)
    db.add(loc)
    await log_action(
        db,
        action="location.updated",
        resource="location",
        resource_id=loc.id,
        tenant_id=tenant_id,
        user_id=actor_user_id,
        metadata={"fields": sorted(changed.keys())},
    )
    await db.commit()
    await db.refresh(loc)
    return loc


async def delete_location(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    loc_id: uuid.UUID,
    *,
    actor_user_id: uuid.UUID | None = None,
) -> None:
    result = await db.execute(
        select(Location).where(Location.id == loc_id, Location.tenant_id == tenant_id)
    )
    loc = result.scalar_one_or_none()
    if not loc:
        raise NotFoundException("Location")
    await log_action(
        db,
        action="location.deleted",
        resource="location",
        resource_id=loc.id,
        tenant_id=tenant_id,
        user_id=actor_user_id,
        metadata={"name": loc.name},
    )
    await db.delete(loc)
    await db.commit()
