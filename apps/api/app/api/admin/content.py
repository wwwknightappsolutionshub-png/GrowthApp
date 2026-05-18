"""Admin CRUD endpoints for content management: FAQ, Blog, Static Pages."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import SuperAdmin
from app.modules.content.models import BlogPost, FaqItem, StaticPage

router = APIRouter(prefix="/api/admin/content", tags=["Admin – Content"])


def _now() -> datetime:
    return datetime.now(timezone.utc)


# ── FAQ ────────────────────────────────────────────────────────────────────────

class FaqIn(BaseModel):
    question: str
    answer: str
    sort_order: int = 0
    is_active: bool = True


DEFAULT_FAQS: list[dict[str, Any]] = [
    {
        "question": "Which UK businesses does CustomerFlow AI work for?",
        "answer": "CustomerFlow AI is built for any UK business with customers — trades, hospitality, beauty and wellness, healthcare, real estate, automotive, B2B consultants, fitness and local services. The platform is vertical-agnostic and configurable to your specific workflows, products and pricing.",
    },
    {
        "question": "How does the AI engine work — and what if OpenAI is down?",
        "answer": "CustomerFlow AI uses a hybrid AI router. OpenAI is the primary provider for content generation, lead scoring, review replies and the AI sales assistant. If OpenAI is unavailable or quota-limited, the router automatically falls back to a self-hosted local LLM so your automations keep running.",
    },
    {
        "question": "Is CustomerFlow AI GDPR compliant?",
        "answer": "Yes. All customer data is hosted on UK servers. The platform includes explicit consent capture on every lead form, automated right-to-erasure workflows, a full data-processing audit log, and configurable retention policies. We provide a DPA for all customers.",
    },
    {
        "question": "Do I need any technical knowledge to use CustomerFlow AI?",
        "answer": "None at all. The onboarding wizard guides you through setup in under 20 minutes. The AI onboarding tutor answers questions in plain English and configures your follow-up sequences, review flows and automations for you.",
    },
    {
        "question": "How does the review automation work?",
        "answer": "When you mark a job complete, the platform automatically sends a review request. Customers who select 4–5 stars are sent to your Google Business page. Customers who select 3 stars or fewer are taken to a private feedback form, protecting your public rating.",
    },
    {
        "question": "Can I try CustomerFlow AI before I pay?",
        "answer": "Yes. Every new account gets a full 14-day free trial with access to all features on the Growth plan. No credit card required.",
    },
    {
        "question": "What happens if I want to cancel?",
        "answer": "You can cancel at any time with a single click from your account settings. No cancellation fees, no minimum contract terms, no awkward phone calls. Your data is exportable for 30 days.",
    },
    {
        "question": "Can I integrate CustomerFlow AI with my existing tools?",
        "answer": "Yes. CustomerFlow AI integrates with Google Business Profile, Stripe, Facebook, WhatsApp, email providers and more. A full REST API and webhook system is available on the Pro plan for custom integrations.",
    },
    {
        "question": "How many team members can I add?",
        "answer": "Starter includes 3 seats, Growth includes 10 seats, and Pro includes unlimited seats with granular role-based access control so each team member sees only what they need.",
    },
    {
        "question": "Can I white-label CustomerFlow AI for my clients?",
        "answer": "White-labelling is available on the Pro plan. Apply your own logo, colours and custom domain and offer the platform under your agency or consultancy brand.",
    },
    {
        "question": "How does missed-call SMS recovery work?",
        "answer": "If a customer calls your number and you cannot answer, CustomerFlow AI instantly sends an automated SMS response within 60 seconds. This recaptures prospects who would otherwise call a competitor.",
    },
    {
        "question": "How secure is my customer data?",
        "answer": "Your data is encrypted in transit (TLS 1.3) and at rest (AES-256). We are SOC 2 Type II ready, ISO 27001 aligned, and all data is hosted exclusively on UK-based servers. 2FA is available for all accounts.",
    },
    {
        "question": "Can CustomerFlow AI replace my existing CRM?",
        "answer": "For most UK SMBs, yes. CustomerFlow AI includes a full kanban CRM with contact management, deal pipelines, notes, activity logs and AI scoring. Enterprise CRM sync via webhooks is available on Pro.",
    },
    {
        "question": "How does pricing work after the free trial?",
        "answer": "After your 14-day free trial, you choose any plan and are billed monthly. No setup fees. Change plan at any time. Your first invoice is issued at the end of your trial period.",
    },
]


DEFAULT_BLOG_POSTS: list[dict[str, Any]] = [
    {
        "title": "How UK Tradesmen Are Winning More Jobs with AI-Powered Follow-Ups",
        "slug": "ai-follow-ups-uk-tradesmen",
        "excerpt": "Discover how plumbers, electricians and builders across the UK are using CustomerFlow AI to automate follow-ups and convert 40% more enquiries into booked jobs.",
        "content": "<h1>How UK Tradesmen Are Winning More Jobs with AI-Powered Follow-Ups</h1><p>For most UK tradespeople, the day ends on the job — not at a desk replying to enquiries. CustomerFlow AI solves this with instant, personalised follow-up sequences that run automatically the moment a new enquiry lands.</p>",
        "category": "Trades",
        "image_url": "https://images.pexels.com/photos/1216589/pexels-photo-1216589.jpeg?auto=compress&cs=tinysrgb&w=800&q=80",
        "read_minutes": 6,
    },
    {
        "title": "5 Signs Your UK Small Business Needs a Customer Retention Strategy",
        "slug": "customer-retention-strategy-uk-small-business",
        "excerpt": "If you are spending more on acquiring new customers than keeping existing ones, you are leaving serious money on the table.",
        "content": "<h1>5 Signs Your UK Small Business Needs a Customer Retention Strategy</h1><p>Acquiring a new customer costs 5–7× more than retaining an existing one. CustomerFlow AI automates win-back, review collection and repeat-business journeys.</p>",
        "category": "Strategy",
        "image_url": "https://images.pexels.com/photos/3184418/pexels-photo-3184418.jpeg?auto=compress&cs=tinysrgb&w=800&q=80",
        "read_minutes": 5,
    },
    {
        "title": "The Complete Guide to Google Review Automation for UK Businesses",
        "slug": "google-review-automation-uk-businesses",
        "excerpt": "More Google reviews mean higher rankings, more trust and more bookings. This guide shows exactly how UK businesses automate review collection.",
        "content": "<h1>The Complete Guide to Google Review Automation for UK Businesses</h1><p>Google reviews are the single most powerful trust signal for UK local businesses. CustomerFlow AI requests, routes and helps reply to reviews automatically.</p>",
        "category": "Reviews",
        "image_url": "https://images.pexels.com/photos/6476255/pexels-photo-6476255.jpeg?auto=compress&cs=tinysrgb&w=800&q=80",
        "read_minutes": 7,
    },
    {
        "title": "How to Reduce No-Shows by 80% with Automated Booking Reminders",
        "slug": "reduce-no-shows-automated-booking-reminders",
        "excerpt": "No-shows cost UK service businesses thousands of pounds every year. Automated reminders bring no-show rates below 5%.",
        "content": "<h1>How to Reduce No-Shows by 80% with Automated Booking Reminders</h1><p>CustomerFlow AI sends confirmations, 48-hour reminders, morning-of reminders and follow-ups so customers do not forget their bookings.</p>",
        "category": "Bookings",
        "image_url": "https://images.pexels.com/photos/1181406/pexels-photo-1181406.jpeg?auto=compress&cs=tinysrgb&w=800&q=80",
        "read_minutes": 4,
    },
    {
        "title": "AI Lead Scoring: Stop Chasing Cold Leads and Close More Business",
        "slug": "ai-lead-scoring-uk-business-close-more",
        "excerpt": "Not all leads are equal. CustomerFlow AI scores every inbound lead in real time so your team focuses on prospects most likely to convert.",
        "content": "<h1>AI Lead Scoring: Stop Chasing Cold Leads and Close More Business</h1><p>CustomerFlow AI analyses contact quality, intent, urgency and service fit, then sorts your pipeline by the leads most likely to convert.</p>",
        "category": "Lead Generation",
        "image_url": "https://images.pexels.com/photos/7376/startup-photos.jpg?auto=compress&cs=tinysrgb&w=800&q=80",
        "read_minutes": 6,
    },
    {
        "title": "Why UK Restaurants Are Switching to Automated Customer Win-Back Campaigns",
        "slug": "automated-win-back-campaigns-uk-restaurants",
        "excerpt": "A customer who visited 6 months ago and never returned is not lost — they just need the right message at the right time.",
        "content": "<h1>Why UK Restaurants Are Switching to Automated Customer Win-Back Campaigns</h1><p>CustomerFlow AI triggers personalised win-back journeys for lapsed customers, helping restaurants recover repeat visits automatically.</p>",
        "category": "Hospitality",
        "image_url": "https://images.pexels.com/photos/262978/pexels-photo-262978.jpeg?auto=compress&cs=tinysrgb&w=800&q=80",
        "read_minutes": 5,
    },
    {
        "title": "The ROI of Missed-Call SMS Recovery for UK Trades Businesses",
        "slug": "missed-call-sms-recovery-roi-uk-trades",
        "excerpt": "Every missed call is a missed job. CustomerFlow AI's 60-second SMS recovery feature recaptures prospects before they dial your competitor.",
        "content": "<h1>The ROI of Missed-Call SMS Recovery for UK Trades Businesses</h1><p>Within 60 seconds of a missed call, CustomerFlow AI can send a personalised SMS that keeps the prospect engaged until you can respond.</p>",
        "category": "Trades",
        "image_url": "https://images.pexels.com/photos/3807517/pexels-photo-3807517.jpeg?auto=compress&cs=tinysrgb&w=800&q=80",
        "read_minutes": 4,
    },
    {
        "title": "GDPR-Compliant Customer Marketing: What Every UK Business Must Know in 2026",
        "slug": "gdpr-compliant-customer-marketing-uk-2026",
        "excerpt": "GDPR fines reached £1.1bn in 2025. CustomerFlow AI is built from the ground up for UK and EU compliance.",
        "content": "<h1>GDPR-Compliant Customer Marketing: What Every UK Business Must Know in 2026</h1><p>CustomerFlow AI helps capture consent, honour erasure requests, control retention windows and keep an audit trail for customer marketing.</p>",
        "category": "Compliance",
        "image_url": "https://images.pexels.com/photos/5668859/pexels-photo-5668859.jpeg?auto=compress&cs=tinysrgb&w=800&q=80",
        "read_minutes": 8,
    },
]


DEFAULT_STATIC_PAGES: list[dict[str, Any]] = [
    {
        "slug": "about",
        "title": "About CustomerFlow AI",
        "content": "<h2>About CustomerFlow AI</h2><p>CustomerFlow AI is an all-in-one growth platform for UK businesses, combining CRM, lead generation, automation, reviews, bookings and money intelligence.</p>",
    },
    {
        "slug": "contact",
        "title": "Contact CustomerFlow AI",
        "content": "<h2>Contact CustomerFlow AI</h2><p>Use this page to publish contact details, support links and sales enquiry information for visitors and customers.</p>",
    },
    {
        "slug": "partners",
        "title": "Partner with CustomerFlow AI",
        "content": "<h2>Partner with CustomerFlow AI</h2><p>Describe the partner programme, agency opportunities and referral routes for businesses that want to work with CustomerFlow AI.</p>",
    },
    {"slug": "careers", "title": "Careers at CustomerFlow AI", "content": "<h2>Careers</h2><p>Careers content can be edited here when roles are open.</p>"},
    {"slug": "privacy", "title": "Privacy Policy", "content": "<h2>Privacy Policy</h2><p>Add your full privacy policy content here.</p>"},
    {"slug": "terms", "title": "Terms of Service", "content": "<h2>Terms of Service</h2><p>Add your platform terms of service here.</p>"},
    {"slug": "gdpr-dpa", "title": "GDPR & Data Processing Agreement", "content": "<h2>GDPR & DPA</h2><p>Add your GDPR and data processing terms here.</p>"},
    {"slug": "cookies", "title": "Cookie Policy", "content": "<h2>Cookie Policy</h2><p>Add your cookie policy content here.</p>"},
]


async def _ensure_default_faqs(db: AsyncSession) -> None:
    total = (await db.execute(select(func.count()).select_from(FaqItem))).scalar_one()
    if total:
        return
    now = _now()
    for index, item in enumerate(DEFAULT_FAQS, start=1):
        db.add(FaqItem(id=uuid.uuid4(), sort_order=index, is_active=True, created_at=now, updated_at=now, **item))
    await db.commit()


async def _ensure_default_blog_posts(db: AsyncSession) -> None:
    total = (await db.execute(select(func.count()).select_from(BlogPost))).scalar_one()
    if total:
        return
    now = _now()
    for post in DEFAULT_BLOG_POSTS:
        db.add(
            BlogPost(
                id=uuid.uuid4(),
                seo_title=f"{post['title']} | CustomerFlow AI",
                seo_description=post["excerpt"],
                author_name="CustomerFlow Team",
                is_published=True,
                published_at=now,
                created_at=now,
                updated_at=now,
                **post,
            )
        )
    await db.commit()


async def _ensure_default_static_pages(db: AsyncSession) -> None:
    total = (await db.execute(select(func.count()).select_from(StaticPage))).scalar_one()
    if total:
        return
    now = _now()
    for page in DEFAULT_STATIC_PAGES:
        db.add(StaticPage(id=uuid.uuid4(), is_active=True, created_at=now, updated_at=now, **page))
    await db.commit()


@router.get("/faq")
async def list_faq(_: SuperAdmin, db: AsyncSession = Depends(get_db)):
    await _ensure_default_faqs(db)
    rows = (await db.execute(select(FaqItem).order_by(FaqItem.sort_order))).scalars().all()
    return [_faq_out(r) for r in rows]


@router.post("/faq", status_code=201)
async def create_faq(body: FaqIn, _: SuperAdmin, db: AsyncSession = Depends(get_db)):
    item = FaqItem(id=uuid.uuid4(), **body.model_dump(), created_at=_now(), updated_at=_now())
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return _faq_out(item)


@router.put("/faq/{item_id}")
async def update_faq(item_id: uuid.UUID, body: FaqIn, _: SuperAdmin, db: AsyncSession = Depends(get_db)):
    item = await _get_or_404(db, FaqItem, item_id)
    for k, v in body.model_dump().items():
        setattr(item, k, v)
    item.updated_at = _now()
    await db.commit()
    await db.refresh(item)
    return _faq_out(item)


@router.delete("/faq/{item_id}", status_code=204)
async def delete_faq(item_id: uuid.UUID, _: SuperAdmin, db: AsyncSession = Depends(get_db)):
    item = await _get_or_404(db, FaqItem, item_id)
    await db.delete(item)
    await db.commit()


# ── Blog Posts ─────────────────────────────────────────────────────────────────

class BlogIn(BaseModel):
    title: str
    slug: str
    excerpt: str | None = None
    content: str | None = None
    category: str = "Guide"
    image_url: str | None = None
    seo_title: str | None = None
    seo_description: str | None = None
    author_name: str = "CustomerFlow Team"
    read_minutes: int = 5
    is_published: bool = False
    published_at: datetime | None = None


@router.get("/blog")
async def list_blog(
    _: SuperAdmin,
    db: AsyncSession = Depends(get_db),
    page: int = 1,
    per_page: int = 20,
):
    await _ensure_default_blog_posts(db)
    offset = (page - 1) * per_page
    total = (await db.execute(select(func.count()).select_from(BlogPost))).scalar_one()
    rows = (
        await db.execute(
            select(BlogPost).order_by(BlogPost.published_at.desc().nullslast()).offset(offset).limit(per_page)
        )
    ).scalars().all()
    return {"total": total, "page": page, "per_page": per_page, "items": [_blog_out(r) for r in rows]}


@router.post("/blog", status_code=201)
async def create_blog(body: BlogIn, _: SuperAdmin, db: AsyncSession = Depends(get_db)):
    data = body.model_dump()
    now = _now()
    if data.get("is_published") and not data.get("published_at"):
        data["published_at"] = now
    post = BlogPost(id=uuid.uuid4(), **data, created_at=now, updated_at=now)
    db.add(post)
    await db.commit()
    await db.refresh(post)
    return _blog_out(post)


@router.put("/blog/{post_id}")
async def update_blog(post_id: uuid.UUID, body: BlogIn, _: SuperAdmin, db: AsyncSession = Depends(get_db)):
    post = await _get_or_404(db, BlogPost, post_id)
    data = body.model_dump()
    if data.get("is_published") and not data.get("published_at") and not post.published_at:
        data["published_at"] = _now()
    for k, v in data.items():
        setattr(post, k, v)
    post.updated_at = _now()
    await db.commit()
    await db.refresh(post)
    return _blog_out(post)


@router.delete("/blog/{post_id}", status_code=204)
async def delete_blog(post_id: uuid.UUID, _: SuperAdmin, db: AsyncSession = Depends(get_db)):
    post = await _get_or_404(db, BlogPost, post_id)
    await db.delete(post)
    await db.commit()


# ── Static Pages ───────────────────────────────────────────────────────────────

class PageIn(BaseModel):
    title: str
    content: str | None = None
    meta_title: str | None = None
    meta_description: str | None = None
    is_active: bool = True


class PageCreate(PageIn):
    slug: str


@router.get("/pages")
async def list_pages(_: SuperAdmin, db: AsyncSession = Depends(get_db)):
    await _ensure_default_static_pages(db)
    rows = (await db.execute(select(StaticPage).order_by(StaticPage.slug))).scalars().all()
    return [_page_out(r) for r in rows]


@router.get("/pages/{slug}")
async def get_page_by_slug(slug: str, db: AsyncSession = Depends(get_db)):
    await _ensure_default_static_pages(db)
    row = (await db.execute(select(StaticPage).where(StaticPage.slug == slug))).scalar_one_or_none()
    if not row:
        raise HTTPException(404, "Page not found")
    return _page_out(row)


@router.post("/pages", status_code=201)
async def create_page(body: PageCreate, _: SuperAdmin, db: AsyncSession = Depends(get_db)):
    existing = (await db.execute(select(StaticPage).where(StaticPage.slug == body.slug))).scalar_one_or_none()
    if existing:
        raise HTTPException(409, "Page slug already exists")
    data = body.model_dump()
    page = StaticPage(id=uuid.uuid4(), **data, created_at=_now(), updated_at=_now())
    db.add(page)
    await db.commit()
    await db.refresh(page)
    return _page_out(page)


@router.put("/pages/{page_id}")
async def update_page(page_id: uuid.UUID, body: PageIn, _: SuperAdmin, db: AsyncSession = Depends(get_db)):
    page = await _get_or_404(db, StaticPage, page_id)
    for k, v in body.model_dump().items():
        setattr(page, k, v)
    page.updated_at = _now()
    await db.commit()
    await db.refresh(page)
    return _page_out(page)


@router.delete("/pages/{page_id}", status_code=204)
async def delete_page(page_id: uuid.UUID, _: SuperAdmin, db: AsyncSession = Depends(get_db)):
    page = await _get_or_404(db, StaticPage, page_id)
    await db.delete(page)
    await db.commit()


# ── Public endpoints (no auth) ─────────────────────────────────────────────────

public_router = APIRouter(prefix="/api/v1/public", tags=["Public – Content"])


@public_router.get("/faq")
async def public_faq(db: AsyncSession = Depends(get_db)):
    await _ensure_default_faqs(db)
    rows = (
        await db.execute(
            select(FaqItem).where(FaqItem.is_active == True).order_by(FaqItem.sort_order)
        )
    ).scalars().all()
    return [_faq_out(r) for r in rows]


@public_router.get("/blog")
async def public_blog(db: AsyncSession = Depends(get_db), page: int = 1, per_page: int = 8):
    await _ensure_default_blog_posts(db)
    offset = (page - 1) * per_page
    total = (
        await db.execute(select(func.count()).select_from(BlogPost).where(BlogPost.is_published == True))
    ).scalar_one()
    rows = (
        await db.execute(
            select(BlogPost)
            .where(BlogPost.is_published == True)
            .order_by(BlogPost.published_at.desc().nullslast())
            .offset(offset)
            .limit(per_page)
        )
    ).scalars().all()
    return {"total": total, "page": page, "per_page": per_page, "items": [_blog_out(r) for r in rows]}


@public_router.get("/blog/{slug}")
async def public_blog_post(slug: str, db: AsyncSession = Depends(get_db)):
    await _ensure_default_blog_posts(db)
    post = (
        await db.execute(
            select(BlogPost).where(BlogPost.slug == slug, BlogPost.is_published == True)
        )
    ).scalar_one_or_none()
    if not post:
        raise HTTPException(404, "Post not found")
    return _blog_out(post)


@public_router.get("/pages/{slug}")
async def public_page(slug: str, db: AsyncSession = Depends(get_db)):
    await _ensure_default_static_pages(db)
    page = (
        await db.execute(
            select(StaticPage).where(StaticPage.slug == slug, StaticPage.is_active == True)
        )
    ).scalar_one_or_none()
    if not page:
        raise HTTPException(404, "Page not found")
    return _page_out(page)


# ── Helpers ────────────────────────────────────────────────────────────────────

async def _get_or_404(db: AsyncSession, model: Any, pk: uuid.UUID) -> Any:
    row = (await db.execute(select(model).where(model.id == pk))).scalar_one_or_none()
    if not row:
        raise HTTPException(404, f"{model.__name__} not found")
    return row


def _faq_out(r: FaqItem) -> dict:
    return {
        "id": str(r.id), "question": r.question, "answer": r.answer,
        "sort_order": r.sort_order, "is_active": r.is_active,
        "created_at": r.created_at.isoformat() if r.created_at else None,
        "updated_at": r.updated_at.isoformat() if r.updated_at else None,
    }


def _blog_out(r: BlogPost) -> dict:
    return {
        "id": str(r.id), "title": r.title, "slug": r.slug,
        "excerpt": r.excerpt, "content": r.content, "category": r.category,
        "image_url": r.image_url, "seo_title": r.seo_title, "seo_description": r.seo_description,
        "author_name": r.author_name, "read_minutes": r.read_minutes,
        "is_published": r.is_published,
        "published_at": r.published_at.isoformat() if r.published_at else None,
        "created_at": r.created_at.isoformat() if r.created_at else None,
        "updated_at": r.updated_at.isoformat() if r.updated_at else None,
    }


def _page_out(r: StaticPage) -> dict:
    return {
        "id": str(r.id), "slug": r.slug, "title": r.title,
        "content": r.content, "meta_title": r.meta_title, "meta_description": r.meta_description,
        "is_active": r.is_active,
        "updated_at": r.updated_at.isoformat() if r.updated_at else None,
    }
