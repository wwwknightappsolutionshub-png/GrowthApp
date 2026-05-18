import uuid
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.exceptions import NotFoundException
from app.modules.social.models import SocialAccount, SocialPost
from app.modules.social.schemas import SocialPostUpdate


async def list_posts(db: AsyncSession, tenant_id: uuid.UUID, page: int = 1, page_size: int = 25) -> tuple[list[SocialPost], int]:
    q = select(SocialPost).where(SocialPost.tenant_id == tenant_id)
    total = (await db.execute(select(func.count()).select_from(q.subquery()))).scalar_one()
    items = (await db.execute(q.order_by(SocialPost.created_at.desc()).offset((page-1)*page_size).limit(page_size))).scalars().all()
    return list(items), total


async def get_post(db: AsyncSession, tenant_id: uuid.UUID, post_id: uuid.UUID) -> SocialPost:
    result = await db.execute(select(SocialPost).where(SocialPost.id == post_id, SocialPost.tenant_id == tenant_id))
    p = result.scalar_one_or_none()
    if not p:
        raise NotFoundException("Post")
    return p


async def update_post(db: AsyncSession, tenant_id: uuid.UUID, post_id: uuid.UUID, data: SocialPostUpdate) -> SocialPost:
    p = await get_post(db, tenant_id, post_id)
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(p, field, value)
    db.add(p)
    await db.commit()
    await db.refresh(p)
    return p


async def approve_and_publish(db: AsyncSession, tenant_id: uuid.UUID, post_id: uuid.UUID) -> SocialPost:
    p = await get_post(db, tenant_id, post_id)
    p.status = "scheduled"
    db.add(p)
    await db.commit()
    from app.workers.queue import enqueue
    await enqueue("publish_social_post", post_id=str(p.id), tenant_id=str(tenant_id))
    return p


async def list_accounts(db: AsyncSession, tenant_id: uuid.UUID) -> list[SocialAccount]:
    result = await db.execute(select(SocialAccount).where(SocialAccount.tenant_id == tenant_id))
    return list(result.scalars().all())
