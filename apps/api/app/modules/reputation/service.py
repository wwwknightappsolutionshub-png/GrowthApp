import uuid
from datetime import datetime, timedelta, timezone
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.exceptions import NotFoundException
from app.modules.reputation.models import ReviewRequest, Review


async def get_review_request_by_token(db: AsyncSession, token: str) -> dict:
    result = await db.execute(select(ReviewRequest).where(ReviewRequest.token == token))
    rr = result.scalar_one_or_none()
    if not rr:
        raise NotFoundException("Review request")
    if not rr.opened_at:
        rr.opened_at = datetime.now(timezone.utc)
        db.add(rr)
        await db.commit()
    # Get tenant info for display
    from app.modules.tenants.models import Tenant
    tenant_result = await db.execute(select(Tenant).where(Tenant.id == rr.tenant_id))
    tenant = tenant_result.scalar_one_or_none()
    return {
        "token": token,
        "business_name": tenant.name if tenant else "",
        "status": rr.status,
    }


async def submit_review_rating(db: AsyncSession, token: str, rating: int, feedback: str | None) -> dict:
    result = await db.execute(select(ReviewRequest).where(ReviewRequest.token == token))
    rr = result.scalar_one_or_none()
    if not rr:
        raise NotFoundException("Review request")

    now = datetime.now(timezone.utc)
    rr.responded_at = now
    rr.status = "responded"
    db.add(rr)

    # Validate rating
    if not isinstance(rating, int) or rating < 1 or rating > 5:
        from app.core.exceptions import BadRequestException
        raise BadRequestException("Rating must be between 1 and 5")

    review = Review(
        id=uuid.uuid4(),
        tenant_id=rr.tenant_id,
        review_request_id=rr.id,
        customer_id=rr.customer_id,
        rating=rating,
        feedback=feedback,
        is_public=rating >= 4,
        routed_to_google=rating >= 4,
    )
    db.add(review)
    await db.commit()

    # Smart routing
    if rating >= 4:
        from app.modules.tenants.models import Tenant
        tenant_result = await db.execute(select(Tenant).where(Tenant.id == rr.tenant_id))
        tenant = tenant_result.scalar_one_or_none()
        google_url = tenant.google_review_url if tenant else None
        return {
            "routed_to_google": True,
            "google_review_url": google_url,
            "message": "Thank you! We'd love it if you left us a Google review.",
        }
    else:
        return {
            "routed_to_google": False,
            "message": "Thank you for your feedback. We're sorry you had a less than perfect experience. Our team will be in touch.",
        }


async def get_dashboard(db: AsyncSession, tenant_id: uuid.UUID) -> dict:
    week_ago = datetime.now(timezone.utc) - timedelta(days=7)

    avg_result = await db.execute(select(func.avg(Review.rating)).where(Review.tenant_id == tenant_id))
    avg = round(float(avg_result.scalar_one() or 0), 1)

    total_result = await db.execute(select(func.count(Review.id)).where(Review.tenant_id == tenant_id))
    total = total_result.scalar_one() or 0

    five_star_result = await db.execute(select(func.count(Review.id)).where(Review.tenant_id == tenant_id, Review.rating == 5))
    five_star = five_star_result.scalar_one() or 0

    google_result = await db.execute(select(func.count(Review.id)).where(Review.tenant_id == tenant_id, Review.routed_to_google == True))
    google_routed = google_result.scalar_one() or 0

    pending_result = await db.execute(select(func.count(ReviewRequest.id)).where(ReviewRequest.tenant_id == tenant_id, ReviewRequest.status == "pending"))
    pending = pending_result.scalar_one() or 0

    week_result = await db.execute(select(func.count(Review.id)).where(Review.tenant_id == tenant_id, Review.created_at >= week_ago))
    week_count = week_result.scalar_one() or 0

    return {"avg_rating": avg, "total_reviews": total, "five_star_count": five_star, "routed_to_google": google_routed, "pending_requests": pending, "this_week_reviews": week_count}


async def get_widget_data(db: AsyncSession, tenant_id: uuid.UUID) -> dict:
    result = await db.execute(
        select(Review).where(Review.tenant_id == tenant_id, Review.is_public == True).order_by(Review.created_at.desc()).limit(10)
    )
    reviews = result.scalars().all()
    avg_result = await db.execute(select(func.avg(Review.rating)).where(Review.tenant_id == tenant_id))
    avg = round(float(avg_result.scalar_one() or 0), 1)
    total_result = await db.execute(select(func.count(Review.id)).where(Review.tenant_id == tenant_id))
    total = total_result.scalar_one() or 0
    return {"reviews": [{"rating": r.rating, "feedback": r.feedback, "date": r.created_at.isoformat()} for r in reviews], "avg_rating": avg, "total": total}


async def list_reviews(db: AsyncSession, tenant_id: uuid.UUID, page: int = 1, page_size: int = 25) -> tuple[list[Review], int]:
    q = select(Review).where(Review.tenant_id == tenant_id)
    total = (await db.execute(select(func.count()).select_from(q.subquery()))).scalar_one()
    items = (await db.execute(q.order_by(Review.created_at.desc()).offset((page-1)*page_size).limit(page_size))).scalars().all()
    return list(items), total
