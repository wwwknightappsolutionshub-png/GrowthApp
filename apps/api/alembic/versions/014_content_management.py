"""014 – Content management tables: faq_items, blog_posts, static_pages.

Revision ID: 014
Revises: 013
Create Date: 2026-05-12
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import uuid
from datetime import datetime, timezone

revision = "014"
down_revision = "013"
branch_labels = None
depends_on = None


def _now():
    return datetime.now(timezone.utc)


def upgrade() -> None:
    # ── faq_items ──────────────────────────────────────────────────────────────
    op.create_table(
        "faq_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("question", sa.Text, nullable=False),
        sa.Column("answer", sa.Text, nullable=False),
        sa.Column("sort_order", sa.Integer, nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    # ── blog_posts ─────────────────────────────────────────────────────────────
    op.create_table(
        "blog_posts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("title", sa.String(300), nullable=False),
        sa.Column("slug", sa.String(300), nullable=False, unique=True),
        sa.Column("excerpt", sa.Text),
        sa.Column("content", sa.Text),
        sa.Column("category", sa.String(100), server_default="Guide"),
        sa.Column("image_url", sa.Text),
        sa.Column("seo_title", sa.String(300)),
        sa.Column("seo_description", sa.Text),
        sa.Column("author_name", sa.String(100), server_default="CustomerFlow Team"),
        sa.Column("read_minutes", sa.Integer, server_default="5"),
        sa.Column("is_published", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("published_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_blog_posts_slug", "blog_posts", ["slug"])

    # ── static_pages ───────────────────────────────────────────────────────────
    op.create_table(
        "static_pages",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("slug", sa.String(100), nullable=False, unique=True),
        sa.Column("title", sa.String(300), nullable=False),
        sa.Column("content", sa.Text),
        sa.Column("meta_title", sa.String(300)),
        sa.Column("meta_description", sa.Text),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_static_pages_slug", "static_pages", ["slug"])

    # ── Seed FAQ ───────────────────────────────────────────────────────────────
    faq_conn = op.get_bind()
    now = _now()
    faqs = [
        ("Which UK businesses does CustomerFlow AI work for?",
         "CustomerFlow AI is built for any UK business with customers — trades, hospitality, beauty and wellness, healthcare, real estate, automotive, B2B consultants, fitness and local services.", 1),
        ("How does the AI engine work — and what if OpenAI is down?",
         "CustomerFlow AI uses a hybrid AI router. OpenAI is the primary provider. If unavailable, the router automatically falls back to a self-hosted local LLM so your automations keep running.", 2),
        ("Is CustomerFlow AI GDPR compliant?",
         "Yes. All customer data is hosted on UK servers, with explicit consent capture, automated right-to-erasure workflows, a full data-processing audit log, and configurable retention policies.", 3),
        ("Do I need any technical knowledge to use CustomerFlow AI?",
         "None at all. The onboarding wizard guides you through setup in under 20 minutes.", 4),
        ("How does the review automation work?",
         "When you mark a job complete, the platform auto-sends a review request. Happy customers go to Google; unhappy customers go to a private feedback form.", 5),
        ("Can I try CustomerFlow AI before I pay?",
         "Yes. Every new account gets a full 14-day free trial with access to all Growth plan features. No credit card required.", 6),
        ("What happens if I want to cancel?",
         "You can cancel at any time with a single click. No cancellation fees, no minimum contracts, no phone calls. Data is exportable for 30 days.", 7),
        ("Can I integrate CustomerFlow AI with my existing tools?",
         "Yes. CustomerFlow AI integrates with Google Business Profile, Stripe, Facebook, WhatsApp, email providers and more. A full REST API and webhook system is available on the Pro plan for custom integrations.", 8),
        ("How many team members can I add to my account?",
         "All plans support multiple team members. The Starter plan includes 3 seats, Growth includes 10 seats, and Pro includes unlimited seats with granular role-based access control.", 9),
        ("Does CustomerFlow AI work for franchise or multi-location businesses?",
         "Absolutely. The Growth plan covers 3 locations and Pro offers unlimited locations. Each location gets its own CRM, booking calendar, review funnel and reporting dashboard — all managed from one parent account.", 10),
        ("What SMS sending limits apply?",
         "Starter includes 1,000 SMS credits/month, Growth includes 5,000 and Pro includes 20,000. Additional credits can be purchased in bundles. All SMS is sent via Tier-1 UK carriers for maximum deliverability.", 11),
        ("Can I white-label CustomerFlow AI for my clients?",
         "White-labelling is available on the Pro plan. You can apply your own branding — logo, colours, custom domain — and offer the platform under your agency or consultancy brand.", 12),
        ("How does the missed-call SMS recovery feature work?",
         "If a customer calls your number and you cannot answer, CustomerFlow AI instantly sends an automated SMS response within 60 seconds. This recaptures prospects who would otherwise call a competitor.", 13),
        ("Is there a mobile app?",
         "CustomerFlow AI is a fully responsive web application that works on any device and browser. Dedicated iOS and Android apps are on the product roadmap and expected in Q3 2026.", 14),
        ("How secure is my customer data?",
         "Your data is encrypted in transit (TLS 1.3) and at rest (AES-256). We are SOC 2 Type II ready, ISO 27001 aligned, and all data is hosted exclusively on UK-based servers. Role-based access control and 2FA are available for all accounts.", 15),
        ("Can CustomerFlow AI replace my existing CRM?",
         "For most UK SMBs, yes. CustomerFlow AI includes a full kanban CRM with contact management, deal pipelines, notes, activity logs and AI scoring. If you use enterprise CRMs like Salesforce, we offer bidirectional sync via webhooks and API.", 16),
        ("How does pricing work after the free trial?",
         "After your 14-day free trial, you choose any plan and are billed monthly. There are no setup fees and you can change plan at any time. Your first invoice is issued at the end of your trial period.", 17),
    ]
    for q, a, order in faqs:
        faq_conn.execute(
            sa.text(
                "INSERT INTO faq_items (id, question, answer, sort_order, is_active, created_at, updated_at) "
                "VALUES (:id, :q, :a, :o, true, :n, :n)"
            ),
            {"id": str(uuid.uuid4()), "q": q, "a": a, "o": order, "n": now},
        )

    # ── Seed Blog Posts ────────────────────────────────────────────────────────
    posts = [
        {
            "title": "How UK Tradesmen Are Winning More Jobs with AI-Powered Follow-Ups",
            "slug": "ai-follow-ups-uk-tradesmen",
            "category": "Trades",
            "excerpt": "Discover how plumbers, electricians and builders across the UK are using CustomerFlow AI to automate follow-ups and convert 40% more enquiries into booked jobs.",
            "image_url": "https://images.pexels.com/photos/1216589/pexels-photo-1216589.jpeg?auto=compress&cs=tinysrgb&w=800&q=80",
            "seo_title": "AI Follow-Up Automation for UK Tradesmen | CustomerFlow AI",
            "seo_description": "Learn how UK plumbers, electricians and builders use CustomerFlow AI to automate lead follow-ups and win more jobs without extra admin.",
            "read_minutes": 6,
            "content": """<h1>How UK Tradesmen Are Winning More Jobs with AI-Powered Follow-Ups</h1>
<p>For most UK tradespeople, the day ends on the job — not at a desk replying to enquiries. By the time you respond, the customer has already booked someone else. CustomerFlow AI solves this with instant, personalised follow-up sequences that run automatically the moment a new enquiry lands.</p>
<h2>The Problem: Slow Response Kills Conversions</h2>
<p>Research shows that leads contacted within 5 minutes are 21× more likely to convert. Yet the average UK tradesman responds in 4+ hours. That gap is where business is lost.</p>
<h2>How CustomerFlow AI Fixes This</h2>
<ul>
<li><strong>Instant SMS acknowledgement</strong> sent within 60 seconds of every enquiry</li>
<li><strong>5-touch automated sequence</strong> over 7 days — SMS, email and WhatsApp</li>
<li><strong>AI reply drafts</strong> you can review and send in one tap</li>
</ul>
<h2>Real Results from UK Trades</h2>
<p>A Manchester-based plumber using CustomerFlow AI saw enquiry-to-booking conversion rise from 22% to 61% in 90 days, purely from automating follow-ups. The system runs while he is on-site.</p>
<h3>Getting Started</h3>
<p>Setup takes under 20 minutes. No technical knowledge required. Start your 14-day free trial today and watch your pipeline fill itself.</p>""",
        },
        {
            "title": "5 Signs Your UK Small Business Needs a Customer Retention Strategy",
            "slug": "customer-retention-strategy-uk-small-business",
            "category": "Strategy",
            "excerpt": "If you are spending more on acquiring new customers than keeping existing ones, you are leaving serious money on the table. Here are 5 warning signs — and what to do about them.",
            "image_url": "https://images.pexels.com/photos/3184418/pexels-photo-3184418.jpeg?auto=compress&cs=tinysrgb&w=800&q=80",
            "seo_title": "Customer Retention Strategy for UK Small Businesses | CustomerFlow AI",
            "seo_description": "5 warning signs your UK SMB needs a customer retention strategy — and how CustomerFlow AI automates win-back, reviews and repeat business.",
            "read_minutes": 5,
            "content": """<h1>5 Signs Your UK Small Business Needs a Customer Retention Strategy</h1>
<p>Acquiring a new customer costs 5–7× more than retaining an existing one. Yet most UK small businesses pour their entire marketing budget into acquisition and ignore the goldmine sitting in their existing customer list. Here are the five warning signs you need a retention strategy — and how to fix them.</p>
<h2>1. Your Repeat Business Rate Is Below 30%</h2>
<p>If fewer than 3 in 10 customers return for a second booking or purchase, your retention is broken. CustomerFlow AI's automated win-back journeys re-engage dormant customers with personalised offers and reminders.</p>
<h2>2. You Have Fewer Than 50 Google Reviews</h2>
<p>Reviews are your most powerful retention and acquisition tool. CustomerFlow AI auto-requests reviews after every completed job, routing happy customers to Google and protecting your rating from negative feedback.</p>
<h2>3. You Do Not Know Who Your Most Valuable Customers Are</h2>
<p>CustomerFlow AI's CRM scores every customer by lifetime value, visit frequency and payment reliability — so you always know who to prioritise.</p>
<h2>4. You Are Not Following Up After Quotes</h2>
<p>73% of lost quotes are never followed up. An automated 5-touch sequence closes those deals without any manual effort.</p>
<h2>5. You Have No Referral System</h2>
<p>Word of mouth is the UK's number-one source of new business for trades and local services. CustomerFlow AI's referral engine tracks, rewards and amplifies every recommendation your customers make.</p>""",
        },
        {
            "title": "The Complete Guide to Google Review Automation for UK Businesses",
            "slug": "google-review-automation-uk-businesses",
            "category": "Reviews",
            "excerpt": "More Google reviews mean higher rankings, more trust and more bookings. This guide shows exactly how UK businesses automate review collection without lifting a finger.",
            "image_url": "https://images.pexels.com/photos/6476255/pexels-photo-6476255.jpeg?auto=compress&cs=tinysrgb&w=800&q=80",
            "seo_title": "Google Review Automation for UK Businesses | CustomerFlow AI",
            "seo_description": "Step-by-step guide to automating Google reviews for UK SMBs — using CustomerFlow AI to collect 4× more reviews on autopilot.",
            "read_minutes": 7,
            "content": """<h1>The Complete Guide to Google Review Automation for UK Businesses</h1>
<p>Google reviews are the single most powerful trust signal for UK local businesses. Businesses with 50+ reviews rank significantly higher in local search. Yet most businesses never ask — and the few that do ask manually get a poor response rate. CustomerFlow AI changes this entirely.</p>
<h2>How Smart Review Routing Works</h2>
<p>Not every customer should be sent to Google. CustomerFlow AI asks customers to rate their experience first:</p>
<ul>
<li><strong>4–5 stars:</strong> Redirected to your Google Business review page</li>
<li><strong>1–3 stars:</strong> Sent to a private feedback form, protecting your public rating</li>
</ul>
<h2>Timing Is Everything</h2>
<p>The optimal time to request a review is 2–4 hours after job completion, while the experience is fresh. CustomerFlow AI automates this with a configurable delay — no manual reminders needed.</p>
<h2>AI-Drafted Replies</h2>
<p>Replying to reviews improves your local SEO ranking. CustomerFlow AI drafts personalised replies in your tone of voice, ready for one-click approval.</p>
<h2>Results You Can Expect</h2>
<p>CustomerFlow AI customers typically see a 4× increase in review volume within 60 days. More reviews → higher Google ranking → more enquiries → more revenue.</p>""",
        },
        {
            "title": "How to Reduce No-Shows by 80% with Automated Booking Reminders",
            "slug": "reduce-no-shows-automated-booking-reminders",
            "category": "Bookings",
            "excerpt": "No-shows cost UK service businesses thousands of pounds every year. CustomerFlow AI's automated reminder system brings no-show rates down to below 5% without any manual effort.",
            "image_url": "https://images.pexels.com/photos/1181406/pexels-photo-1181406.jpeg?auto=compress&cs=tinysrgb&w=800&q=80",
            "seo_title": "Reduce No-Shows with Automated Booking Reminders | CustomerFlow AI",
            "seo_description": "Discover how UK service businesses use CustomerFlow AI to cut no-shows by 80% with automated SMS and email booking reminders.",
            "read_minutes": 4,
            "content": """<h1>How to Reduce No-Shows by 80% with Automated Booking Reminders</h1>
<p>A no-show costs you the job, the time slot and the opportunity cost of a booked customer. For trades and service businesses across the UK, no-shows account for an average £6,200 in lost revenue per year per business.</p>
<h2>The CustomerFlow AI Reminder Sequence</h2>
<ol>
<li><strong>Confirmation SMS</strong> — sent immediately when booking is created</li>
<li><strong>48-hour reminder</strong> — SMS + email with job details and a reschedule link</li>
<li><strong>Morning-of reminder</strong> — SMS at 8am on the day of the appointment</li>
<li><strong>30-minute heads-up</strong> — SMS when you are en route</li>
</ol>
<h2>Deposit Collection Stops Casual Cancellations</h2>
<p>CustomerFlow AI integrates with Stripe to collect a configurable deposit at the time of booking. Customers with skin in the game cancel 73% less frequently than those with free cancellation.</p>
<h2>What Our Customers Say</h2>
<p>"Our no-show rate went from 18% to under 3% in the first month. That alone paid for the subscription ten times over." — Sarah K., Beauty Salon Owner, Bristol.</p>""",
        },
        {
            "title": "AI Lead Scoring: Stop Chasing Cold Leads and Close More Business",
            "slug": "ai-lead-scoring-uk-business-close-more",
            "category": "Lead Generation",
            "excerpt": "Not all leads are equal. CustomerFlow AI scores every inbound lead in real time so your team spends time on prospects most likely to convert — and ignores the tyre-kickers.",
            "image_url": "https://images.pexels.com/photos/7376/startup-photos.jpg?auto=compress&cs=tinysrgb&w=800&q=80",
            "seo_title": "AI Lead Scoring for UK Businesses | CustomerFlow AI",
            "seo_description": "CustomerFlow AI scores inbound leads in real time so UK businesses focus on high-value prospects and close more business with less effort.",
            "read_minutes": 6,
            "content": """<h1>AI Lead Scoring: Stop Chasing Cold Leads and Close More Business</h1>
<p>Time is your most valuable resource. CustomerFlow AI's lead scoring engine analyses every inbound enquiry across 8 dimensions — contact quality, intent signals, location match, urgency, service need specificity, business type, name validity and overall completeness — and produces a 0–100 quality score in real time.</p>
<h2>How the Scoring Works</h2>
<ul>
<li><strong>Phone number provided:</strong> +25 points</li>
<li><strong>Email provided:</strong> +20 points</li>
<li><strong>Service need specified:</strong> +20 points</li>
<li><strong>Location within your area:</strong> +15 points</li>
<li><strong>Urgency signal detected:</strong> +10 points</li>
</ul>
<h2>Prioritised Pipeline View</h2>
<p>In the CustomerFlow CRM, leads are automatically sorted by score. Your team always works the hottest leads first — dramatically improving conversion rates without working harder.</p>
<h2>Fraud and Spam Filtering</h2>
<p>The AI engine also filters out disposable email addresses, known spam patterns and incomplete submissions, keeping your pipeline clean and your team focused.</p>""",
        },
        {
            "title": "Why UK Restaurants Are Switching to Automated Customer Win-Back Campaigns",
            "slug": "automated-win-back-campaigns-uk-restaurants",
            "category": "Hospitality",
            "excerpt": "A customer who visited 6 months ago and never returned is not lost — they just need the right message at the right time. Here is how UK restaurants are winning them back automatically.",
            "image_url": "https://images.pexels.com/photos/262978/pexels-photo-262978.jpeg?auto=compress&cs=tinysrgb&w=800&q=80",
            "seo_title": "Automated Win-Back Campaigns for UK Restaurants | CustomerFlow AI",
            "seo_description": "How UK restaurants use CustomerFlow AI's automated win-back campaigns to re-engage lapsed customers and drive repeat bookings.",
            "read_minutes": 5,
            "content": """<h1>Why UK Restaurants Are Switching to Automated Customer Win-Back Campaigns</h1>
<p>The typical UK restaurant loses 30–40% of its customer base each year through simple inactivity — not because customers had a bad experience, but because life got busy and they forgot to return. Win-back campaigns change this.</p>
<h2>The CustomerFlow Win-Back Sequence</h2>
<p>When a customer has not visited in a configurable number of days (typically 60–90), CustomerFlow AI triggers a personalised win-back journey:</p>
<ol>
<li>Day 0: Personalised "We miss you" email with a special offer</li>
<li>Day 3: Follow-up SMS if email unopened</li>
<li>Day 7: Final reminder with increased incentive</li>
</ol>
<h2>Personalisation at Scale</h2>
<p>Win-back messages include the customer's first name, their last visit date and their most-ordered items — all pulled automatically from the CustomerFlow CRM. Personalised campaigns convert 6× better than generic blasts.</p>
<h2>GDPR Compliance Built In</h2>
<p>All win-back campaigns respect consent preferences captured at the point of original data collection, with automatic suppression of opted-out contacts and a one-click unsubscribe on every message.</p>""",
        },
        {
            "title": "The ROI of Missed-Call SMS Recovery for UK Trades Businesses",
            "slug": "missed-call-sms-recovery-roi-uk-trades",
            "category": "Trades",
            "excerpt": "Every missed call is a missed job. CustomerFlow AI's 60-second SMS recovery feature recaptures prospects before they dial your competitor — and the numbers are extraordinary.",
            "image_url": "https://images.pexels.com/photos/3807517/pexels-photo-3807517.jpeg?auto=compress&cs=tinysrgb&w=800&q=80",
            "seo_title": "Missed-Call SMS Recovery ROI for UK Trades | CustomerFlow AI",
            "seo_description": "Calculate the ROI of CustomerFlow AI's missed-call SMS recovery for UK tradespeople. Recapture leads before they call your competition.",
            "read_minutes": 4,
            "content": """<h1>The ROI of Missed-Call SMS Recovery for UK Trades Businesses</h1>
<p>The average UK tradesperson misses 7 calls per week during jobs, travel or evenings. At an average job value of £280, that is £1,960 in potential weekly revenue silently walking out of the door.</p>
<h2>How Missed-Call SMS Recovery Works</h2>
<p>Within 60 seconds of a missed call, CustomerFlow AI automatically sends the caller a personalised SMS:</p>
<blockquote>"Hi, this is [Business Name]. Sorry I missed your call — I'm on a job right now. I'll call you back within the hour. If it's urgent, reply to this message. — [Owner Name]"</blockquote>
<h2>The Numbers</h2>
<ul>
<li>73% of missed-call SMS recipients respond within 10 minutes</li>
<li>61% convert to a booked job (vs 12% for unreplied missed calls)</li>
<li>Average recovered revenue per month: £2,400+ per tradesperson</li>
</ul>
<h2>ROI Calculation</h2>
<p>If CustomerFlow AI recovers just 4 additional jobs per month at £280 each, that is £1,120 recovered revenue against a £99–199/month subscription — an ROI of 5–10× in the first month alone.</p>""",
        },
        {
            "title": "GDPR-Compliant Customer Marketing: What Every UK Business Must Know in 2026",
            "slug": "gdpr-compliant-customer-marketing-uk-2026",
            "category": "Compliance",
            "excerpt": "GDPR fines reached £1.1bn in 2025. CustomerFlow AI is built from the ground up for UK and EU compliance — here is what you need to know to stay safe and keep marketing.",
            "image_url": "https://images.pexels.com/photos/5668859/pexels-photo-5668859.jpeg?auto=compress&cs=tinysrgb&w=800&q=80",
            "seo_title": "GDPR Compliant Customer Marketing UK 2026 | CustomerFlow AI",
            "seo_description": "Everything UK businesses need to know about GDPR-compliant marketing in 2026 — and how CustomerFlow AI makes compliance automatic.",
            "read_minutes": 8,
            "content": """<h1>GDPR-Compliant Customer Marketing: What Every UK Business Must Know in 2026</h1>
<p>Since leaving the EU, the UK has maintained its own equivalent of GDPR through the UK GDPR and the Data Protection Act 2018. ICO enforcement is increasing — fines for UK organisations reached record levels in 2025. Every business that holds or uses customer data must be compliant.</p>
<h2>The 5 Pillars of GDPR-Compliant Marketing</h2>
<h3>1. Lawful Basis for Processing</h3>
<p>You must have a documented lawful basis for every marketing activity. For most SMBs, this is consent (opted in) or legitimate interests (existing customers). CustomerFlow AI captures and stores consent at the point of lead entry or booking, with a timestamp and source.</p>
<h3>2. Right to Erasure</h3>
<p>When a customer requests deletion, you must comply within 30 days. CustomerFlow AI automates this with a one-click GDPR erasure workflow that removes data across all modules and creates an audit log.</p>
<h3>3. Data Minimisation</h3>
<p>Only collect data you actually need. CustomerFlow AI's lead forms are configurable — you decide which fields are required.</p>
<h3>4. Retention Policies</h3>
<p>Data should not be kept longer than necessary. CustomerFlow AI supports configurable retention windows with automatic archiving.</p>
<h3>5. Breach Notification</h3>
<p>If a data breach occurs, you have 72 hours to notify the ICO. CustomerFlow AI's audit log and access controls significantly reduce breach risk.</p>
<h2>Marketing You Can Do Legally</h2>
<p>CustomerFlow AI's win-back, review request and follow-up features are all designed to be triggered only for contacts with appropriate consent or legitimate interests, keeping you on the right side of UK GDPR.</p>""",
        },
    ]
    blog_conn = op.get_bind()
    for p in posts:
        blog_conn.execute(
            sa.text(
                "INSERT INTO blog_posts (id, title, slug, excerpt, content, category, image_url, "
                "seo_title, seo_description, author_name, read_minutes, is_published, published_at, created_at, updated_at) "
                "VALUES (:id, :title, :slug, :excerpt, :content, :category, :image_url, "
                ":seo_title, :seo_desc, 'CustomerFlow Team', :read_minutes, true, :n, :n, :n)"
            ),
            {
                "id": str(uuid.uuid4()),
                "title": p["title"], "slug": p["slug"],
                "excerpt": p["excerpt"], "content": p["content"],
                "category": p["category"], "image_url": p["image_url"],
                "seo_title": p["seo_title"], "seo_desc": p["seo_description"],
                "read_minutes": p["read_minutes"], "n": now,
            },
        )

    # ── Seed Static Pages ──────────────────────────────────────────────────────
    pages = [
        ("about", "About CustomerFlow AI"),
        ("contact", "Contact CustomerFlow AI"),
        ("partners", "Partner with CustomerFlow AI"),
        ("careers", "Careers at CustomerFlow AI"),
        ("privacy", "Privacy Policy"),
        ("terms", "Terms of Service"),
        ("gdpr-dpa", "GDPR & Data Processing Agreement"),
        ("cookies", "Cookie Policy"),
    ]
    page_conn = op.get_bind()
    for slug, title in pages:
        page_conn.execute(
            sa.text(
                "INSERT INTO static_pages (id, slug, title, is_active, created_at, updated_at) "
                "VALUES (:id, :slug, :title, true, :n, :n)"
            ),
            {"id": str(uuid.uuid4()), "slug": slug, "title": title, "n": now},
        )


def downgrade() -> None:
    op.drop_index("ix_static_pages_slug", "static_pages")
    op.drop_table("static_pages")
    op.drop_index("ix_blog_posts_slug", "blog_posts")
    op.drop_table("blog_posts")
    op.drop_table("faq_items")
