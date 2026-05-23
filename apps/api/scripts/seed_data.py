"""
CustomerFlow AI — Full seed script for local development and testing.
Creates super admin, business owners, staff, customers, leads, deals,
quotes, invoices, bookings, reviews, and subscriptions.

Run:
    cd apps/api
    $env:PYTHONPATH="."
    uv run python scripts/seed_data.py

WARNING: Drops and recreates all tables on each run.
"""

import asyncio
import random
import uuid
from datetime import datetime, timezone, timedelta

from sqlalchemy import text

# ── Import all models to populate Base.metadata ──────────────────────────────
from app.modules.auth.models import User, RefreshToken
from app.modules.tenants.models import Tenant, TenantMember, Location
from app.modules.billing.models import SubscriptionPlan, Subscription, BillingInvoice
from app.modules.leads.models import Lead
from app.modules.crm.models import Customer, Deal, DealActivity
from app.modules.booking.models import Staff, AvailabilitySlot, Booking
from app.modules.quotes_invoices.models import Quote, QuoteItem, Invoice, InvoiceItem, Payment
from app.modules.automation.models import Automation, AutomationStep, AutomationRun, MessageTemplate
from app.modules.messaging.models import Conversation, Message
from app.modules.reputation.models import ReviewRequest, Review
from app.modules.social.models import SocialAccount, SocialPost
from app.modules.audit.models import AuditLog
from app.modules.gdpr.models import GdprRequest

from app.core.database import engine, Base, AsyncSessionLocal
from app.core.security import hash_password

# Force-load every SQLAlchemy model onto Base.metadata (marketing, landing pages,
# tasks, rbac, …). Without this, preview/seed would recreate only the subset of
# tables imported above — public routes such as `/public/marketing/bundle` then
# hit missing tables and return 500.
from app.main import app as _app_for_full_schema  # noqa: F401
from app.modules.addons import industry_models  # noqa: F401 — industry add-on tables

# ── Helpers ───────────────────────────────────────────────────────────────────
def now() -> datetime:
    return datetime.now(timezone.utc)

def days_ago(n: int) -> datetime:
    return now() - timedelta(days=n)

def days_from_now(n: int) -> datetime:
    return now() + timedelta(days=n)

def pence(gbp: float) -> int:
    return int(gbp * 100)

# ── User / tenant blueprints ──────────────────────────────────────────────────
USERS = [
    {
        "tag": "superadmin",
        "full_name": "Super Admin",
        "email": "admin@customerflow.ai",
        "password": "Admin@CustomerFlow1",
        "is_superadmin": True,
    },
    {
        "tag": "plumber_owner",
        "full_name": "Mike Thompson",
        "email": "mike@smithsplumbing.co.uk",
        "password": "Plumber@Test1",
        "is_superadmin": False,
        "tenant": {
            "name": "Smith's Plumbing Ltd",
            "slug": "smiths-plumbing",
            "business_type": "plumber",
            "phone": "07700 100 001",
            "email": "info@smithsplumbing.co.uk",
            "city": "Manchester",
            "postcode": "M1 1AA",
            "google_review_url": "https://g.page/r/smithsplumbing/review",
            "plan": "Growth",
        },
    },
    {
        "tag": "electrician_owner",
        "full_name": "Sarah Chen",
        "email": "sarah@brightspark.co.uk",
        "password": "Electric@Test1",
        "is_superadmin": False,
        "tenant": {
            "name": "Bright Spark Electrical",
            "slug": "bright-spark-electrical",
            "business_type": "electrician",
            "phone": "07700 100 002",
            "email": "hello@brightspark.co.uk",
            "city": "London",
            "postcode": "E1 6RF",
            "google_review_url": "https://g.page/r/brightspark/review",
            "plan": "Pro",
        },
    },
    {
        "tag": "cleaner_owner",
        "full_name": "Priya Patel",
        "email": "priya@sparkclean.co.uk",
        "password": "Cleaner@Test1",
        "is_superadmin": False,
        "tenant": {
            "name": "SparkClean Services",
            "slug": "sparkclean",
            "business_type": "cleaner",
            "phone": "07700 100 003",
            "email": "info@sparkclean.co.uk",
            "city": "Birmingham",
            "postcode": "B1 1BB",
            "google_review_url": "https://g.page/r/sparkclean/review",
            "plan": "Starter",
        },
    },
    {
        "tag": "salon_owner",
        "full_name": "Amira Hassan",
        "email": "amira@luxesalon.co.uk",
        "password": "Salon@Test12",
        "is_superadmin": False,
        "tenant": {
            "name": "Luxe Hair & Beauty",
            "slug": "luxe-hair-beauty",
            "business_type": "salon",
            "phone": "07700 100 004",
            "email": "bookings@luxesalon.co.uk",
            "city": "Leeds",
            "postcode": "LS1 5AA",
            "google_review_url": "https://g.page/r/luxesalon/review",
            "plan": "Growth",
        },
    },
]

STAFF_MEMBERS = [
    # Smith's Plumbing staff
    {"tenant_tag": "plumber_owner", "full_name": "Dave Wilson", "email": "dave@smithsplumbing.co.uk", "password": "Staff@Test123", "role": "staff"},
    {"tenant_tag": "plumber_owner", "full_name": "Jake Morris", "email": "jake@smithsplumbing.co.uk", "password": "Staff@Test123", "role": "staff"},
    # Bright Spark staff
    {"tenant_tag": "electrician_owner", "full_name": "Tom Baker", "email": "tom@brightspark.co.uk", "password": "Staff@Test123", "role": "staff"},
]

# ── Realistic customer data ───────────────────────────────────────────────────
CUSTOMER_DATA = [
    ("James", "Harrison", "james.harrison@gmail.com", "07811 222 001", "14 Oak Street", "M2 4LT", "google"),
    ("Emma", "Clarke", "emma.c@hotmail.com", "07811 222 002", "7 Maple Ave", "M3 1PQ", "website"),
    ("Oliver", "Brown", "oliver.brown@outlook.com", "07811 222 003", "55 Pine Road", "M4 7RS", "referral"),
    ("Sophia", "Taylor", "sophia.t@yahoo.co.uk", "07811 222 004", "3 Elm Close", "M5 2XY", "facebook"),
    ("Liam", "Johnson", "liam.j@gmail.com", "07811 222 005", "21 Cedar Lane", "M6 5AB", "google"),
    ("Charlotte", "Williams", "charlotte.w@gmail.com", "07811 222 006", "8 Birch Way", "M7 3CD", "website"),
    ("Noah", "Davies", "noah.d@icloud.com", "07811 222 007", "16 Walnut Drive", "M8 6EF", "missed_call"),
    ("Isla", "Evans", "isla.e@gmail.com", "07811 222 008", "33 Ash Court", "M9 1GH", "referral"),
    ("Harry", "Wilson", "harry.w@btinternet.com", "07811 222 009", "9 Hazel Road", "M10 4IJ", "google"),
    ("Grace", "Anderson", "grace.a@gmail.com", "07811 222 010", "41 Chestnut St", "M11 7KL", "instagram"),
    ("George", "Thomas", "george.t@outlook.com", "07811 222 011", "6 Beech Ave", "M12 2MN", "website"),
    ("Lily", "Roberts", "lily.r@gmail.com", "07811 222 012", "19 Sycamore Dr", "M13 5OP", "google"),
]

# ── Seeder functions ──────────────────────────────────────────────────────────

async def reset_tables(db):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    print("✓ Tables reset and recreated")


async def seed_plans(db) -> dict:
    plans = {}
    rows = [
        SubscriptionPlan(id=uuid.uuid4(), name="Starter", price_gbp_monthly=99,
                         max_locations=1, max_leads_per_month=500, max_sms_per_month=1000, max_users=1,
                         has_social_posting=False, has_ai_content=False, has_white_label=False),
        SubscriptionPlan(id=uuid.uuid4(), name="Growth", price_gbp_monthly=149,
                         max_locations=3, max_leads_per_month=2000, max_sms_per_month=5000, max_users=5,
                         has_social_posting=True, has_ai_content=False, has_white_label=False),
        SubscriptionPlan(id=uuid.uuid4(), name="Pro", price_gbp_monthly=199,
                         max_locations=100, max_leads_per_month=10000, max_sms_per_month=20000, max_users=20,
                         has_social_posting=True, has_ai_content=True, has_white_label=True),
    ]
    for p in rows:
        db.add(p)
        plans[p.name] = p
    await db.flush()
    print(f"✓ Seeded {len(rows)} subscription plans")
    return plans


async def seed_users_and_tenants(db, plans: dict) -> dict:
    created = {}

    for u in USERS:
        user = User(
            id=uuid.uuid4(),
            email=u["email"],
            password_hash=hash_password(u["password"]),
            full_name=u["full_name"],
            is_superadmin=u["is_superadmin"],
            email_verified_at=now(),
            totp_backup_codes=[],
        )
        db.add(user)
        await db.flush()
        created[u["tag"]] = {"user": user, "tenant": None}

        if "tenant" in u:
            td = u["tenant"]
            plan = plans[td["plan"]]
            tenant = Tenant(
                id=uuid.uuid4(),
                slug=td["slug"],
                name=td["name"],
                business_type=td["business_type"],
                phone=td["phone"],
                email=td["email"],
                city=td["city"],
                postcode=td["postcode"],
                google_review_url=td["google_review_url"],
                plan_id=plan.id,
                trial_ends_at=days_from_now(14),
                is_active=True,
                onboarding_completed=True,
            )
            db.add(tenant)
            await db.flush()

            member = TenantMember(
                id=uuid.uuid4(),
                tenant_id=tenant.id,
                user_id=user.id,
                role="owner",
                joined_at=now(),
            )
            db.add(member)

            location = Location(
                id=uuid.uuid4(),
                tenant_id=tenant.id,
                slug=f"{td['slug']}-main",
                name=f"{td['name']} — Main",
                address="1 High Street",
                city=td["city"],
                postcode=td["postcode"],
                phone=td["phone"],
                email=td["email"],
                is_primary=True,
            )
            db.add(location)

            sub = Subscription(
                id=uuid.uuid4(),
                tenant_id=tenant.id,
                plan_id=plan.id,
                status="active",
                current_period_start=days_ago(15),
                current_period_end=days_from_now(15),
            )
            db.add(sub)

            for i in range(1, 3):
                billing_inv = BillingInvoice(
                    id=uuid.uuid4(),
                    tenant_id=tenant.id,
                    amount_pence=pence(plan.price_gbp_monthly),
                    currency="gbp",
                    status="paid",
                    period_start=days_ago(15 + 30 * (i - 1)),
                    period_end=days_ago(15 + 30 * (i - 1) - 30),
                )
                db.add(billing_inv)

            await db.flush()
            created[u["tag"]]["tenant"] = tenant

    print(f"✓ Seeded {len(USERS)} users + {len(USERS)-1} tenants")
    return created


async def seed_staff(db, created: dict) -> None:
    for s in STAFF_MEMBERS:
        user = User(
            id=uuid.uuid4(),
            email=s["email"],
            password_hash=hash_password(s["password"]),
            full_name=s["full_name"],
            email_verified_at=now(),
            totp_backup_codes=[],
        )
        db.add(user)
        await db.flush()

        tenant = created[s["tenant_tag"]]["tenant"]
        member = TenantMember(
            id=uuid.uuid4(),
            tenant_id=tenant.id,
            user_id=user.id,
            role=s["role"],
            joined_at=now(),
        )
        db.add(member)

        staff_row = Staff(
            id=uuid.uuid4(),
            tenant_id=tenant.id,
            user_id=user.id,
            name=s["full_name"],
            email=s["email"],
        )
        db.add(staff_row)

    await db.flush()
    print(f"✓ Seeded {len(STAFF_MEMBERS)} staff members")


async def seed_customers_and_deals(db, created: dict) -> None:
    """Seed customers, leads, deals, activities, quotes, invoices, bookings, reviews for the plumber tenant."""

    tenant_entry = created["plumber_owner"]
    tenant = tenant_entry["tenant"]
    owner_user = tenant_entry["user"]

    total_customers = 0
    total_deals = 0
    total_leads = 0
    total_quotes = 0
    total_invoices = 0
    total_bookings = 0
    total_reviews = 0

    # ── Customers ──────────────────────────────────────────────────────
    customers = []
    for fn, ln, email, phone, addr, pc, src in CUSTOMER_DATA:
        c = Customer(
            id=uuid.uuid4(),
            tenant_id=tenant.id,
            first_name=fn,
            last_name=ln,
            email=email,
            phone=phone,
            address=addr,
            postcode=pc,
            source=src,
            gdpr_consent=True,
            gdpr_consent_at=days_ago(random.randint(10, 60)),
        )
        db.add(c)
        customers.append(c)
    await db.flush()
    total_customers = len(customers)

    # ── Leads ──────────────────────────────────────────────────────────
    lead_messages = [
        "Boiler not working, need urgent repair",
        "Leaking pipe under kitchen sink",
        "Bathroom tap needs replacing",
        "Annual boiler service required",
        "New radiator installation",
        "Emergency leak in bathroom",
        "Central heating not working",
    ]
    for i, c in enumerate(customers[:7]):
        status = random.choice(["new", "new", "contacted", "converted"])
        lead = Lead(
            id=uuid.uuid4(),
            tenant_id=tenant.id,
            first_name=c.first_name,
            last_name=c.last_name,
            email=c.email,
            phone=c.phone,
            source=c.source,
            message=lead_messages[i % len(lead_messages)],
            postcode=c.postcode,
            status=status,
        )
        db.add(lead)
    await db.flush()
    total_leads = 7

    # ── Deal templates ─────────────────────────────────────────────────
    deals_data = [
        # (customer_idx, title, stage, service_type, value_gbp, days_old)
        (0,  "Emergency boiler repair",          "Completed", "Boiler Repair",        320,  45),
        (1,  "Kitchen pipe leak repair",          "Completed", "Pipe Repair",          185,  32),
        (2,  "Bathroom tap replacement",          "Booked",    "Tap Replacement",      140,  10),
        (3,  "Annual boiler service",             "Booked",    "Boiler Service",       120,   5),
        (4,  "New radiator install x3",           "Quoted",    "Radiator Install",     650,   8),
        (5,  "Central heating repair",            "Quoted",    "Heating Repair",       280,   3),
        (6,  "Emergency bathroom leak",           "Contacted", "Emergency Plumbing",   500,   2),
        (7,  "Full bathroom refurb quote",        "Contacted", "Bathroom Refurbishment", 3200, 1),
        (8,  "Outdoor tap fitting",               "New",       "Outdoor Tap",           95,   0),
        (9,  "Boiler replacement quote",          "New",       "Boiler Replacement",  2800,   0),
        (10, "Shower fitting",                    "Lost",      "Shower Install",        420,  20),
        (11, "Power flush — went with another",   "Lost",      "Power Flush",           380,  15),
    ]

    quote_num = 1001
    inv_num   = 2001
    booking_num = 1

    for (cidx, title, stage, svc, val_gbp, days_old) in deals_data:
        c = customers[cidx % len(customers)]
        deal = Deal(
            id=uuid.uuid4(),
            tenant_id=tenant.id,
            customer_id=c.id,
            title=title,
            stage=stage,
            service_type=svc,
            value_pence=pence(val_gbp),
            source=c.source,
            lost_reason="Went with a cheaper competitor" if stage == "Lost" else None,
            completed_at=days_ago(days_old) if stage == "Completed" else None,
            created_at=days_ago(days_old + random.randint(2, 5)),
        )
        db.add(deal)
        await db.flush()
        total_deals += 1

        # ── Activities ────────────────────────────────────────────────
        activity_sets = {
            "New": [
                ("lead_created", f"Lead captured via {c.source}"),
            ],
            "Contacted": [
                ("lead_created", f"Lead captured via {c.source}"),
                ("call", f"Called {c.first_name} — left voicemail"),
                ("sms", "Auto-SMS sent: 'Hi, we received your enquiry...'"),
            ],
            "Quoted": [
                ("lead_created", f"New lead from {c.source}"),
                ("call", f"Spoke with {c.first_name}, confirmed requirements"),
                ("quote_sent", f"Quote #{quote_num} sent for £{val_gbp}"),
                ("sms", "Quote follow-up SMS sent after 48 hours"),
            ],
            "Booked": [
                ("lead_created", f"Enquiry from {c.source}"),
                ("call", f"Spoke with {c.first_name}, agreed on scope"),
                ("quote_sent", f"Quote #{quote_num} sent for £{val_gbp}"),
                ("quote_accepted", f"{c.first_name} accepted the quote online"),
                ("booking_created", f"Job booked for {(now() + timedelta(days=2)).strftime('%d %b %Y')}"),
            ],
            "Completed": [
                ("lead_created", f"Lead via {c.source}"),
                ("call", f"Called {c.first_name}, discussed requirements"),
                ("quote_sent", f"Quote #{quote_num} sent"),
                ("quote_accepted", "Quote accepted"),
                ("booking_created", "Job scheduled"),
                ("job_completed", f"Job completed. Took {random.choice([2,3,4])} hours."),
                ("review_requested", "Review request SMS sent automatically"),
            ],
            "Lost": [
                ("lead_created", f"Lead from {c.source}"),
                ("call", f"Called {c.first_name}, sent quote"),
                ("quote_sent", f"Quote #{quote_num} sent for £{val_gbp}"),
                ("note", "Customer went with a cheaper competitor. No response after 3 follow-ups."),
            ],
        }
        for act_type, body in activity_sets.get(stage, []):
            db.add(DealActivity(
                id=uuid.uuid4(),
                tenant_id=tenant.id,
                deal_id=deal.id,
                user_id=owner_user.id,
                type=act_type,
                body=body,
                created_at=days_ago(max(0, days_old - random.randint(0, days_old))),
            ))

        # ── Quotes ────────────────────────────────────────────────────
        if stage in ("Quoted", "Booked", "Completed", "Lost"):
            subtotal = pence(val_gbp)
            vat = pence(val_gbp * 0.20)
            total = subtotal + vat
            q_status = {
                "Quoted": "sent", "Booked": "accepted",
                "Completed": "accepted", "Lost": "declined",
            }[stage]
            quote = Quote(
                id=uuid.uuid4(),
                tenant_id=tenant.id,
                customer_id=c.id,
                deal_id=deal.id,
                quote_number=f"Q{quote_num}",
                public_token=str(uuid.uuid4()),
                title=title,
                subtotal_pence=subtotal,
                vat_pence=vat,
                total_pence=total,
                status=q_status,
                valid_until=days_from_now(14).date() if q_status == "sent" else days_ago(10).date(),
                notes="All parts and labour included. VAT at 20%.",
                created_at=days_ago(days_old),
            )
            db.add(quote)
            await db.flush()
            db.add(QuoteItem(
                id=uuid.uuid4(),
                quote_id=quote.id,
                description=svc,
                quantity=1,
                unit_price_pence=subtotal,
                line_total_pence=subtotal,
            ))
            quote_num += 1
            total_quotes += 1

        # ── Invoices + Payments ───────────────────────────────────────
        if stage == "Completed":
            subtotal = pence(val_gbp)
            vat = pence(val_gbp * 0.20)
            total = subtotal + vat
            inv = Invoice(
                id=uuid.uuid4(),
                tenant_id=tenant.id,
                customer_id=c.id,
                deal_id=deal.id,
                invoice_number=f"INV{inv_num}",
                public_token=str(uuid.uuid4()),
                title=title,
                subtotal_pence=subtotal,
                vat_pence=vat,
                total_pence=total,
                paid_pence=total,
                status="paid",
                due_date=days_ago(days_old - 14).date(),
                notes="Thank you for your business.",
                created_at=days_ago(days_old),
            )
            db.add(inv)
            await db.flush()
            db.add(InvoiceItem(
                id=uuid.uuid4(),
                invoice_id=inv.id,
                description=svc,
                quantity=1,
                unit_price_pence=subtotal,
                line_total_pence=subtotal,
            ))
            db.add(Payment(
                id=uuid.uuid4(),
                tenant_id=tenant.id,
                invoice_id=inv.id,
                amount_pence=total,
                method="card",
                status="succeeded",
            ))
            inv_num += 1
            total_invoices += 1

        # ── Bookings ──────────────────────────────────────────────────
        if stage in ("Booked", "Completed"):
            bk_status = "completed" if stage == "Completed" else "confirmed"
            bk_start  = days_ago(days_old) if stage == "Completed" else days_from_now(2 + booking_num)
            booking = Booking(
                id=uuid.uuid4(),
                tenant_id=tenant.id,
                customer_id=c.id,
                deal_id=deal.id,
                customer_name=f"{c.first_name} {c.last_name}",
                customer_email=c.email,
                customer_phone=c.phone,
                service_description=svc,
                status=bk_status,
                booking_date=bk_start.date(),
                start_time=bk_start.time(),
                end_time=(bk_start + timedelta(hours=random.choice([2, 3, 4]))).time(),
                deposit_required_pence=pence(val_gbp * 0.25),
                deposit_paid_pence=pence(val_gbp * 0.25),
                notes="Customer prefers morning appointments.",
            )
            db.add(booking)
            booking_num += 1
            total_bookings += 1

        # ── Reviews ───────────────────────────────────────────────────
        if stage == "Completed":
            ratings = [5, 5, 5, 5, 4, 5]
            reviews_text = [
                "Absolutely brilliant service! Mike arrived on time, fixed the problem quickly and left everything spotless. Will definitely use again.",
                "Great work, very professional. Sorted my boiler out same day. Highly recommend to anyone in Manchester.",
                "Excellent job — explained everything clearly before starting, no hidden costs, very fair price. 5 stars.",
                "Really impressed. Friendly, tidy, and fixed the leak properly. Other plumbers just patched it temporarily.",
            ]
            rating = random.choice(ratings)
            rr = ReviewRequest(
                id=uuid.uuid4(),
                tenant_id=tenant.id,
                deal_id=deal.id,
                customer_id=c.id,
                status="clicked",
                sent_at=days_ago(days_old - 1),
                opened_at=days_ago(days_old - 1),
                responded_at=days_ago(days_old - 1),
            )
            db.add(rr)
            await db.flush()

            if random.random() > 0.25:
                rev = Review(
                    id=uuid.uuid4(),
                    tenant_id=tenant.id,
                    review_request_id=rr.id,
                    customer_id=c.id,
                    rating=rating,
                    feedback=random.choice(reviews_text) if rating >= 4 else "Service was okay but a bit slow.",
                    routed_to_google=rating >= 4,
                    is_public=rating >= 4,
                )
                db.add(rev)
                total_reviews += 1

    await db.flush()

    print(f"✓ Seeded {total_customers} customers | {total_leads} leads | {total_deals} deals")
    print(f"  └─ {total_quotes} quotes | {total_invoices} invoices | {total_bookings} bookings | {total_reviews} reviews")


async def seed_electrician_data(db, created: dict) -> None:
    """Lighter data set for the electrician tenant."""
    tenant = created["electrician_owner"]["tenant"]
    owner  = created["electrician_owner"]["user"]

    elec_customers = [
        ("Paul", "Green",  "paul.green@gmail.com",   "07822 300 001", "EC1A 2AB", "google"),
        ("Zara", "Khan",   "zara.k@outlook.com",     "07822 300 002", "E2 8DP",   "referral"),
        ("Ben",  "Foster", "ben.foster@yahoo.co.uk", "07822 300 003", "E3 3BB",   "website"),
        ("Nina", "Moore",  "nina.m@gmail.com",       "07822 300 004", "E4 6CC",   "google"),
        ("Ethan","Price",  "ethan.p@gmail.com",      "07822 300 005", "E5 9DD",   "facebook"),
    ]
    cs = []
    for fn, ln, email, phone, pc, src in elec_customers:
        c = Customer(
            id=uuid.uuid4(), tenant_id=tenant.id,
            first_name=fn, last_name=ln, email=email, phone=phone,
            postcode=pc, source=src, gdpr_consent=True, gdpr_consent_at=days_ago(20),
        )
        db.add(c); cs.append(c)
    await db.flush()

    elec_deals = [
        (0, "Consumer unit upgrade",    "Completed", 680,  30),
        (1, "EV charger installation",  "Booked",    950,   4),
        (2, "Fault finding & repair",   "Quoted",    220,   2),
        (3, "Office rewire quote",      "New",       4500,  0),
        (4, "External lighting fit",    "Contacted", 380,   1),
    ]
    for cidx, title, stage, val, days_old in elec_deals:
        c = cs[cidx]
        deal = Deal(
            id=uuid.uuid4(), tenant_id=tenant.id, customer_id=c.id,
            title=title, stage=stage, service_type=title,
            value_pence=pence(val), source=c.source,
            completed_at=days_ago(days_old) if stage == "Completed" else None,
            created_at=days_ago(days_old + 3),
        )
        db.add(deal)
    await db.flush()
    print(f"✓ Electrician tenant: {len(cs)} customers, {len(elec_deals)} deals")


async def seed_cleaner_data(db, created: dict) -> None:
    """Light data for the cleaner tenant."""
    tenant = created["cleaner_owner"]["tenant"]
    cs = []
    for fn, ln, email, phone, pc, src in [
        ("Rachel","Hill",  "rachel.h@gmail.com",  "07833 400 001", "B2 4DD", "google"),
        ("Sam",   "Walsh", "sam.w@outlook.com",   "07833 400 002", "B3 1EE", "website"),
        ("Fiona", "Long",  "fiona.l@gmail.com",   "07833 400 003", "B4 7FF", "referral"),
    ]:
        c = Customer(
            id=uuid.uuid4(), tenant_id=tenant.id,
            first_name=fn, last_name=ln, email=email, phone=phone,
            postcode=pc, source=src, gdpr_consent=True, gdpr_consent_at=days_ago(15),
        )
        db.add(c); cs.append(c)
    await db.flush()

    for i, (title, stage, val) in enumerate([
        ("Weekly office clean", "Completed", 280),
        ("End-of-tenancy clean", "Booked", 350),
        ("Deep clean quote", "Quoted", 180),
    ]):
        deal = Deal(
            id=uuid.uuid4(), tenant_id=tenant.id, customer_id=cs[i].id,
            title=title, stage=stage, service_type=title,
            value_pence=pence(val), source=cs[i].source,
            completed_at=days_ago(7) if stage == "Completed" else None,
            created_at=days_ago(14),
        )
        db.add(deal)
    await db.flush()
    print(f"✓ Cleaner tenant: {len(cs)} customers, 3 deals")


# ── Main ──────────────────────────────────────────────────────────────────────

async def main():
    print("\n🌱 CustomerFlow AI seed script starting...\n")

    async with AsyncSessionLocal() as db:
        await reset_tables(db)
        plans   = await seed_plans(db)
        created = await seed_users_and_tenants(db, plans)
        await seed_staff(db, created)
        await seed_customers_and_deals(db, created)
        await seed_electrician_data(db, created)
        await seed_cleaner_data(db, created)
        from app.modules.addons.seed_garage import ensure_garage_demo_tenant

        garage_info = await ensure_garage_demo_tenant(db, plans=plans)
        from app.modules.marketing.seed import seed_marketing_data

        counts = await seed_marketing_data(db, replace=True)
        print(
            f"✓ Marketing CMS seeded: {counts['sections']} sections, "
            f"{counts['reviews']} reviews, {counts['templates']} landing templates"
        )
        await db.commit()

    print("\n✅ Seed complete!\n")
    print("=" * 62)
    print("  CREDENTIALS")
    print("=" * 62)
    print()
    print("  SUPER ADMIN")
    print("  ─────────────────────────────────────────────────────")
    print("  Email   : admin@customerflow.ai")
    print("  Password: Admin@CustomerFlow1")
    print("  Role    : Super admin (platform-wide access)")
    print()
    print("  BUSINESS OWNERS")
    print("  ─────────────────────────────────────────────────────")
    print("  Mike Thompson  (Plumber — Manchester)")
    print("  Email   : mike@smithsplumbing.co.uk")
    print("  Password: Plumber@Test1")
    print("  Plan    : Growth (£149/month)")
    print()
    print("  Sarah Chen  (Electrician — London)")
    print("  Email   : sarah@brightspark.co.uk")
    print("  Password: Electric@Test1")
    print("  Plan    : Pro (£199/month)")
    print()
    print("  Priya Patel  (Cleaner — Birmingham)")
    print("  Email   : priya@sparkclean.co.uk")
    print("  Password: Cleaner@Test1")
    print("  Plan    : Starter (£99/month)")
    print()
    print("  Amira Hassan  (Salon — Leeds)")
    print("  Email   : amira@luxesalon.co.uk")
    print("  Password: Salon@Test12")
    print("  Plan    : Growth (£149/month)")
    print()
    print("  Alex Knight  (Garage — Leeds, all industry add-ons)")
    print("  Email   : garage@knightmotors.co.uk")
    print("  Password: Garage@Test1")
    print("  Slug    : knight-motors-garage")
    print("  Add-ons : industry_booking, industry_billing, industry_crm")
    print()
    print("  STAFF MEMBERS")
    print("  ─────────────────────────────────────────────────────")
    print("  Dave Wilson  (Plumber staff)")
    print("  Email   : dave@smithsplumbing.co.uk")
    print("  Password: Staff@Test123")
    print()
    print("  Jake Morris  (Plumber staff)")
    print("  Email   : jake@smithsplumbing.co.uk")
    print("  Password: Staff@Test123")
    print()
    print("  Tom Baker  (Electrician staff)")
    print("  Email   : tom@brightspark.co.uk")
    print("  Password: Staff@Test123")
    print()
    print("  SAMPLE DATA (Smith's Plumbing)")
    print("  ─────────────────────────────────────────────────────")
    print("  12 customers | 7 leads | 12 deals across all stages")
    print("  Quotes, invoices, payments, bookings, reviews seeded")
    print("  Pipeline stages: New, Contacted, Quoted, Booked, Completed, Lost")
    print("=" * 62)
    print()


if __name__ == "__main__":
    asyncio.run(main())
