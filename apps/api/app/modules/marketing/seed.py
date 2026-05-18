"""Seed data for the marketing CMS, public review carousel and landing
templates.

Stats deliberately reflect a *new* SaaS (founding cohort numbers), not the
inflated "2,400 businesses / 47k reviews" placeholders from the prototype.
The super-admin can edit any of this from the dashboard.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.marketing.models import LandingPageTemplate, MarketingReview, MarketingSection

# ── Marketing sections ──────────────────────────────────────────────────────

SECTIONS: list[dict] = [
    {
        "key": "hero",
        "title": "Hero panel",
        "description": "The very top of the marketing page — headline, sub-copy, CTAs.",
        "sort_order": 10,
        "data": {
            "eyebrow": "The AI OS for UK businesses",
            "headline_part_1": "The AI operating system",
            "headline_part_2": "for UK businesses",
            "sub": "Capture leads, automate follow-up, collect reviews and see your money "
                   "in one enterprise-grade platform — purpose-built for UK SMBs.",
            "primary_cta": {"label": "Start 14-day free trial", "href": "/register"},
            "secondary_cta": {"label": "Book a demo", "href": "/demo"},
            "live_label": "Now onboarding founding-cohort customers",
            "trust_chips": [
                {"label": "GDPR compliant"},
                {"label": "UK data residency"},
                {"label": "SOC 2 ready"},
                {"label": "Stripe verified"},
            ],
        },
    },
    {
        "key": "stats",
        "title": "Headline metrics",
        "description": "The 4-up KPI strip near the top of the page. Keep these honest "
                       "and updated quarterly — founder credibility matters.",
        "sort_order": 20,
        "data": {
            "items": [
                {
                    "label": "Founding-cohort businesses",
                    "value": 38,
                    "suffix": "+",
                    "tone": "forest",
                    "help": "Live customers across the UK",
                },
                {
                    "label": "Conversations automated",
                    "value": 12_400,
                    "suffix": "",
                    "tone": "teal",
                    "help": "Lead replies, reminders & reviews",
                },
                {
                    "label": "Reviews collected",
                    "value": 1_280,
                    "suffix": "+",
                    "tone": "forest",
                    "help": "Across Google & site widgets",
                },
                {
                    "label": "Avg. response time",
                    "value": 47,
                    "suffix": "s",
                    "tone": "teal",
                    "help": "From lead capture to first reply",
                },
            ]
        },
    },
    {
        "key": "pillars",
        "title": "Platform pillars",
        "description": "The four-by-three grid that explains the product surface.",
        "sort_order": 30,
        "data": {
            "items": [
                {
                    "title": "Lead Engine",
                    "subtitle": "Capture & qualify",
                    "icon": "Target",
                    "tone": "forest",
                    "bullets": [
                        "Embeddable forms & widgets",
                        "AI lead scoring & routing",
                        "Inbox-zero auto-replies",
                    ],
                },
                {
                    "title": "Pipeline",
                    "subtitle": "Quote → invoice",
                    "icon": "Users",
                    "tone": "teal",
                    "bullets": [
                        "Kanban deals & jobs",
                        "Quote / invoice / payments",
                        "Customer 360° history",
                    ],
                },
                {
                    "title": "Automation",
                    "subtitle": "Set-and-forget",
                    "icon": "Zap",
                    "tone": "forest",
                    "bullets": [
                        "Email / SMS / WhatsApp sequences",
                        "Booking reminders",
                        "Smart follow-up nudges",
                    ],
                },
                {
                    "title": "Reputation",
                    "subtitle": "5-star machine",
                    "icon": "Star",
                    "tone": "teal",
                    "bullets": [
                        "Auto review requests post-job",
                        "Google / Trustpilot routing",
                        "Site widget & carousel",
                    ],
                },
                {
                    "title": "Money",
                    "subtitle": "Cash intelligence",
                    "icon": "PoundSterling",
                    "tone": "forest",
                    "bullets": [
                        "Cashflow forecast",
                        "Outstanding invoices",
                        "Per-job profitability",
                    ],
                },
                {
                    "title": "Growth",
                    "subtitle": "Outbound + content",
                    "icon": "Megaphone",
                    "tone": "teal",
                    "bullets": [
                        "Landing-page builder",
                        "Ads & SEO copilot",
                        "Social autopilot",
                    ],
                },
            ]
        },
    },
    {
        "key": "industries",
        "title": "Industries we serve",
        "description": "Quick scroller of vertical tags shown below the hero.",
        "sort_order": 40,
        "data": {
            "items": [
                {"label": "Trades & Services", "icon": "Wrench"},
                {"label": "Hospitality", "icon": "UtensilsCrossed"},
                {"label": "Beauty & Wellness", "icon": "Sparkles"},
                {"label": "Healthcare", "icon": "Stethoscope"},
                {"label": "Real Estate", "icon": "Home"},
                {"label": "Professional Services", "icon": "Briefcase"},
            ]
        },
    },
    {
        "key": "pricing",
        "title": "Pricing tiers",
        "description": "The published pricing plans. Edit prices, features, badges here.",
        "sort_order": 60,
        "data": {
            "currency": "GBP",
            "currency_symbol": "£",
            "period": "month",
            "footnote": "All plans include unlimited team members, GDPR-compliant UK data "
                        "residency and a 14-day free trial. No card required to start.",
            "plans": [
                {
                    "key": "starter",
                    "name": "Starter",
                    "price": 49,
                    "tagline": "For solo operators getting their first 100 customers.",
                    "cta": "Start free trial",
                    "highlighted": False,
                    "features": [
                        "Up to 500 contacts",
                        "Lead capture forms & widget",
                        "Email + SMS automation",
                        "Reviews & reputation",
                        "Stripe payments",
                        "Mobile app",
                    ],
                },
                {
                    "key": "growth",
                    "name": "Growth",
                    "price": 149,
                    "tagline": "For growing teams ready to automate.",
                    "cta": "Start free trial",
                    "highlighted": True,
                    "badge": "Most popular",
                    "features": [
                        "Up to 10,000 contacts",
                        "Everything in Starter",
                        "WhatsApp Business CRM",
                        "AI assistant + auto-replies",
                        "Landing-page builder",
                        "Outreach sequences",
                        "Custom domains",
                    ],
                },
                {
                    "key": "scale",
                    "name": "Scale",
                    "price": 299,
                    "tagline": "For multi-location & enterprise teams.",
                    "cta": "Talk to sales",
                    "highlighted": False,
                    "features": [
                        "Unlimited contacts",
                        "Everything in Growth",
                        "Multi-location management",
                        "RBAC + SSO",
                        "API + webhooks",
                        "Priority support",
                        "Dedicated CSM",
                    ],
                },
            ],
        },
    },
    {
        "key": "faqs",
        "title": "FAQs",
        "description": "The accordion at the bottom of the marketing page.",
        "sort_order": 70,
        "data": {
            "items": [
                {
                    "q": "How long does setup take?",
                    "a": "Most teams are live within 30 minutes. Connect Stripe, your "
                         "Google profile and your inbox, then your first lead form goes "
                         "out the door.",
                },
                {
                    "q": "Do you have a free trial?",
                    "a": "Yes — every plan starts with a 14-day free trial. No card "
                         "required and no automatic conversion at the end.",
                },
                {
                    "q": "Where is my data stored?",
                    "a": "All customer data is stored in UK data centres on encrypted "
                         "Postgres with daily backups. We are GDPR-compliant and SOC 2 ready.",
                },
                {
                    "q": "Can I import my existing contacts?",
                    "a": "Yes — CSV import is built in, and we also have a one-click import "
                         "from HubSpot, Pipedrive and most spreadsheets.",
                },
                {
                    "q": "How does the AI assistant work?",
                    "a": "Our AI is grounded in your own data — leads, jobs, customers, "
                         "invoices, reviews. Ask it 'who didn't pay yet?' or 'draft a "
                         "follow-up to all leads from May' and it just works.",
                },
                {
                    "q": "Is WhatsApp Business included?",
                    "a": "WhatsApp CRM is included on Growth and Scale plans. We handle "
                         "the Twilio integration and message templates so you can focus "
                         "on the conversation.",
                },
            ]
        },
    },
    {
        "key": "footer",
        "title": "Footer",
        "description": "Footer links, address & social.",
        "sort_order": 90,
        "data": {
            "tagline": "The AI operating system for UK businesses.",
            "address": "CustomerFlow AI Ltd · London · UK",
            "links": {
                "Product": [
                    {"label": "Features", "href": "/features"},
                    {"label": "Pricing", "href": "/pricing"},
                    {"label": "Integrations", "href": "/integrations"},
                    {"label": "Changelog", "href": "/changelog"},
                ],
                "Company": [
                    {"label": "About", "href": "/about"},
                    {"label": "Customers", "href": "/customers"},
                    {"label": "Careers", "href": "/careers"},
                    {"label": "Contact", "href": "/contact"},
                ],
                "Resources": [
                    {"label": "Help centre", "href": "/help"},
                    {"label": "Status", "href": "/status"},
                    {"label": "Security", "href": "/security"},
                    {"label": "Privacy", "href": "/privacy"},
                ],
            },
        },
    },
]


# ── Seed testimonials (the carousel content) ────────────────────────────────

SEED_REVIEWS: list[dict] = [
    {
        "author_name": "Mike Thompson",
        "author_role": "Master Plumber",
        "author_location": "Manchester",
        "rating": 5,
        "quote": "Went from three enquiries a week to fourteen. CustomerFlow runs while "
                 "I'm on the tools — the auto-reply has saved my evenings.",
        "metric": "+367% enquiries",
        "is_featured": True,
    },
    {
        "author_name": "Sarah Chen",
        "author_role": "Boutique Salon Owner",
        "author_location": "London",
        "rating": 5,
        "quote": "Booking reminders alone took our no-show rate from 18% to under 3%. "
                 "The reviews flow keeps Google five-stars topped up without me lifting a finger.",
        "metric": "No-shows down 83%",
    },
    {
        "author_name": "James O'Connor",
        "author_role": "Electrical Contractor",
        "author_location": "Bristol",
        "rating": 5,
        "quote": "I treat CustomerFlow like a second business partner. Every quote is "
                 "followed up automatically — my close rate went from a guess to 68%.",
        "metric": "68% quote acceptance",
        "is_featured": True,
    },
    {
        "author_name": "Priya Patel",
        "author_role": "Dental Practice Manager",
        "author_location": "Birmingham",
        "rating": 5,
        "quote": "WhatsApp reminders + the review request loop changed how we feel "
                 "about Mondays. We get more positive feedback in a week than the whole "
                 "of last year combined.",
        "metric": "12× weekly reviews",
    },
    {
        "author_name": "David Roberts",
        "author_role": "Independent Estate Agent",
        "author_location": "Leeds",
        "rating": 5,
        "quote": "The Money dashboard pays for the entire subscription on its own. I "
                 "know which jobs are profitable, which ones are bleeding cash and "
                 "exactly where my pipeline is.",
        "metric": "+£42k recovered receivables",
    },
    {
        "author_name": "Emily Watson",
        "author_role": "Wellness Studio Founder",
        "author_location": "Edinburgh",
        "rating": 5,
        "quote": "The AI assistant feels like a personal Chief of Staff. I ask it "
                 "'who hasn't paid yet?' and three seconds later I have a polite "
                 "follow-up sequence going.",
        "metric": "8 hours/week saved",
    },
]


# ── Landing-page templates (12 total: 6 niches × 2 each) ────────────────────


def _hero(eyebrow: str, headline: str, sub: str, cta: str) -> dict:
    return {
        "type": "hero",
        "props": {"eyebrow": eyebrow, "headline": headline, "sub": sub, "cta": cta},
    }


def _features(title: str, items: list[dict]) -> dict:
    return {"type": "features", "props": {"title": title, "items": items}}


def _testimonials(title: str, items: list[dict]) -> dict:
    return {"type": "testimonials", "props": {"title": title, "items": items}}


def _faq(items: list[dict]) -> dict:
    return {"type": "faq", "props": {"title": "Common questions", "items": items}}


def _cta(headline: str, sub: str, button: str) -> dict:
    return {
        "type": "cta",
        "props": {"headline": headline, "sub": sub, "button": button},
    }


def _trust(items: list[str]) -> dict:
    return {"type": "trust_badges", "props": {"items": [{"label": i} for i in items]}}


def _lead_form(headline: str, sub: str) -> dict:
    return {
        "type": "lead_form",
        "props": {
            "headline": headline,
            "sub": sub,
            "fields": [
                {"name": "first_name", "label": "Your name", "type": "text", "required": True},
                {"name": "phone", "label": "Phone", "type": "tel", "required": True},
                {"name": "email", "label": "Email", "type": "email", "required": False},
                {"name": "message", "label": "Tell us what you need", "type": "textarea"},
            ],
            "submit_label": "Get a quote",
        },
    }


def _theme_forest() -> dict:
    return {"primary": "#025422", "accent": "#20ccce", "style": "enterprise"}


def _theme_warm() -> dict:
    return {"primary": "#7c2d12", "accent": "#f59e0b", "style": "warm"}


TEMPLATES: list[dict] = [
    # ── Trades & Services ───────────────────────────────────────────────────
    {
        "slug": "trades-emergency-callout",
        "name": "Emergency Callout — Trades",
        "niche": "trades",
        "description": "High-urgency lead capture for plumbers, electricians and locksmiths who need calls now.",
        "preview_image_url": None,
        "theme": _theme_forest(),
        "sections": [
            _hero(
                "24/7 emergency",
                "Burst pipe? Power cut? We're on our way.",
                "DBS-checked, fully-insured engineers — typical arrival within 60 minutes across Greater Manchester.",
                "Call now — free quote",
            ),
            _trust(["Gas Safe registered", "NICEIC approved", "DBS-checked", "Fully insured", "1-year guarantee"]),
            _features("Why our customers stay", [
                {"icon": "Zap", "title": "60-minute response", "body": "Average time from call to engineer arrival."},
                {"icon": "Shield", "title": "Up-front pricing", "body": "Quote agreed before any work begins."},
                {"icon": "Star", "title": "5-star average", "body": "Across Google, Checkatrade and Trustpilot."},
            ]),
            _testimonials("What our customers say", [
                {"name": "Janet H.", "role": "Homeowner, Salford", "rating": 5,
                 "quote": "Came out at 2am for a burst pipe. Sorted in an hour, flat rate, no surprises."},
            ]),
            _lead_form("Need help right now?", "Fill in 30 seconds — we'll call you back within 5 minutes."),
            _faq([
                {"q": "Are you 24/7?", "a": "Yes — including weekends and bank holidays."},
                {"q": "Do you charge a call-out fee?", "a": "No, we only charge for the work we do."},
            ]),
            _cta("Save our number", "We're here when things go wrong.", "Save to contacts"),
        ],
    },
    {
        "slug": "trades-domestic-installer",
        "name": "Domestic Installer — Trades",
        "niche": "trades",
        "description": "Considered-purchase template for boiler swaps, EV chargers and full rewires.",
        "preview_image_url": None,
        "theme": _theme_forest(),
        "sections": [
            _hero(
                "Approved local installer",
                "A new boiler, fitted in a day, with a 10-year guarantee.",
                "Free home survey · 0% finance options · Manufacturer-approved engineers.",
                "Book free survey",
            ),
            _features("Three steps, one fitting", [
                {"icon": "Phone", "title": "1. Free survey", "body": "Book online — 20-minute home visit."},
                {"icon": "FileText", "title": "2. Fixed quote", "body": "All-in price agreed in writing."},
                {"icon": "Wrench", "title": "3. Fitted in a day", "body": "Tidy install, full demo, guaranteed."},
            ]),
            _trust(["Worcester Bosch Accredited", "Gas Safe", "Which? Trusted Trader", "10-year guarantee"]),
            _testimonials("Local homeowners love us", [
                {"name": "Tom B.", "role": "Homeowner, Wigan", "rating": 5,
                 "quote": "Quoted on Tuesday, fitted on Friday. Tidy, polite and £400 less than British Gas."},
                {"name": "Priya M.", "role": "Homeowner, Stockport", "rating": 5,
                 "quote": "Genuinely the easiest tradesperson experience I've ever had."},
            ]),
            _lead_form("Book your free survey", "Choose a 20-minute slot — we'll confirm by text."),
            _cta("0% finance available", "Spread the cost over 24 months with no interest.", "See finance options"),
        ],
    },

    # ── Hospitality ─────────────────────────────────────────────────────────
    {
        "slug": "hospitality-restaurant-reservations",
        "name": "Restaurant Reservations",
        "niche": "hospitality",
        "description": "Reservations-driven landing for independent restaurants and bistros.",
        "preview_image_url": None,
        "theme": _theme_warm(),
        "sections": [
            _hero(
                "Reservations",
                "Modern British cooking. Honest portions. A great Tuesday.",
                "Open Tuesday – Sunday from 17:30. Walk-ins welcome, but Friday & Saturday book up fast.",
                "Reserve a table",
            ),
            _features("Why book direct", [
                {"icon": "Calendar", "title": "Same-day tables", "body": "Live availability you can trust."},
                {"icon": "MessageSquare", "title": "Personal greeting", "body": "We'll text you the night before with parking tips."},
                {"icon": "Star", "title": "Birthday on us", "body": "Free dessert for birthdays — just let us know."},
            ]),
            _testimonials("Recent reviews", [
                {"name": "Anna L.", "rating": 5, "quote": "Best meal we've had in the city all year. Service was effortless."},
                {"name": "Mark D.", "rating": 5, "quote": "Booked on a whim. We're going back next week."},
            ]),
            _lead_form("Can't see your slot?", "Drop us your details and we'll text the moment we have a table."),
            _faq([
                {"q": "Do you have a dress code?", "a": "Smart casual — no trainers in the evening."},
                {"q": "Can we book a private dining room?", "a": "Yes — we host parties up to 24."},
            ]),
        ],
    },
    {
        "slug": "hospitality-boutique-hotel",
        "name": "Boutique Hotel — Direct booking",
        "niche": "hospitality",
        "description": "Direct-bookings landing page for boutique hotels avoiding the OTA tax.",
        "preview_image_url": None,
        "theme": _theme_warm(),
        "sections": [
            _hero(
                "Book direct, save 12%",
                "Twelve rooms. One unforgettable garden. Suffolk, slowly.",
                "A Georgian rectory with a wood-fired kitchen, a 4-acre walled garden and the slowest mornings in East Anglia.",
                "Check availability",
            ),
            _trust(["Sunday Times Top 100", "Best Boutique 2026", "Two AA Rosettes"]),
            _features("Why book on our site", [
                {"icon": "BadgePercent", "title": "12% cheaper", "body": "OTAs charge us — and you."},
                {"icon": "Gift", "title": "Welcome gift", "body": "A bottle of local fizz in your room on arrival."},
                {"icon": "Coffee", "title": "Late checkout", "body": "Stay til 12pm on us, every direct booking."},
            ]),
            _testimonials("Recent guests", [
                {"name": "Olivia & Sam", "rating": 5, "quote": "The garden, the breakfast, the bath. We've already rebooked."},
            ]),
            _lead_form("Looking for specific dates?", "Tell us when and we'll check the calendar by hand."),
            _cta("Gift card for a loved one?", "Unforgettable starts here.", "Buy a gift card"),
        ],
    },

    # ── Beauty & Wellness ───────────────────────────────────────────────────
    {
        "slug": "beauty-salon-bookings",
        "name": "Hair Salon — Online bookings",
        "niche": "beauty",
        "description": "Stylist-driven hair salon page with booking and gallery.",
        "preview_image_url": None,
        "theme": {"primary": "#5b21b6", "accent": "#20ccce", "style": "modern"},
        "sections": [
            _hero(
                "Northern Quarter · Manchester",
                "A modern colour salon, not a chair shop.",
                "Balayage, cut & colour, education and the best soundtrack on Tib Street.",
                "Book online",
            ),
            _features("Why we sell out every week", [
                {"icon": "Sparkles", "title": "Specialist colour", "body": "All seniors are L'Oréal Colour Specialists."},
                {"icon": "Calendar", "title": "Easy reschedule", "body": "Move your appointment in two taps."},
                {"icon": "Heart", "title": "5-star service", "body": "Average 4.97 across 2,400+ reviews."},
            ]),
            _testimonials("Loved by", [
                {"name": "Hannah J.", "rating": 5, "quote": "Honestly the best balayage I've had in ten years."},
                {"name": "Mei T.", "rating": 5, "quote": "From the consult to the blow-dry, this place is a vibe."},
            ]),
            _lead_form("New client?", "Tell us about your hair — we'll match you to the right stylist."),
            _faq([
                {"q": "Do you do consultations?", "a": "Yes — 20 minutes, free, no obligation."},
                {"q": "Do you take walk-ins?", "a": "Sometimes, but online booking is more reliable."},
            ]),
        ],
    },
    {
        "slug": "beauty-spa-membership",
        "name": "Day Spa — Memberships",
        "niche": "beauty",
        "description": "Subscription-style landing for day spas selling monthly memberships.",
        "preview_image_url": None,
        "theme": {"primary": "#0f766e", "accent": "#fde68a", "style": "calm"},
        "sections": [
            _hero(
                "Members save 30%",
                "Your monthly hour of quiet.",
                "One massage, one facial, unlimited steam room and pool — every month for £79.",
                "Become a member",
            ),
            _features("What's included", [
                {"icon": "Hand", "title": "1× full massage", "body": "Choose Swedish, sport or deep tissue."},
                {"icon": "Smile", "title": "1× signature facial", "body": "Tailored to your skin, every visit."},
                {"icon": "Waves", "title": "Unlimited pool", "body": "Pool, steam room and rest pods — bring a friend free once a month."},
            ]),
            _testimonials("Member reviews", [
                {"name": "Rachel S.", "rating": 5, "quote": "I treat the membership like therapy. It pays for itself in week one."},
            ]),
            _lead_form("Not ready to commit?", "Book a single visit and try it on for size."),
            _cta("First month half-price", "Use code SLOWDOWN at checkout.", "Start membership"),
        ],
    },

    # ── Healthcare ──────────────────────────────────────────────────────────
    {
        "slug": "healthcare-private-clinic",
        "name": "Private Clinic — Consultations",
        "niche": "healthcare",
        "description": "Private GP and specialist clinic with same-day appointment booking.",
        "preview_image_url": None,
        "theme": {"primary": "#1e3a8a", "accent": "#20ccce", "style": "clinical"},
        "sections": [
            _hero(
                "Private GP, Marylebone",
                "Same-day GP appointments. No queue, no judgement.",
                "30-minute consultations with experienced NHS-trained doctors. CQC registered.",
                "Book a consultation",
            ),
            _trust(["CQC registered", "GMC verified", "Private insurance accepted", "30-min appointments"]),
            _features("Why patients switch", [
                {"icon": "Clock", "title": "Same-day access", "body": "Book in the morning, seen in the afternoon."},
                {"icon": "FileText", "title": "Detailed notes", "body": "Every consultation written up the same day."},
                {"icon": "Heart", "title": "Continuity of care", "body": "See the same GP for ongoing concerns."},
            ]),
            _testimonials("Patients tell us", [
                {"name": "Ms. C, 34", "rating": 5, "quote": "Felt heard for the first time in years. Thirty unhurried minutes."},
            ]),
            _lead_form("Have a question first?", "Send us a confidential message and we'll reply within 2 hours."),
            _faq([
                {"q": "Do you accept private insurance?", "a": "Yes — Bupa, AXA, Vitality, Aviva, Cigna."},
                {"q": "Are prescriptions included?", "a": "Yes — we e-prescribe directly to your pharmacy."},
            ]),
        ],
    },
    {
        "slug": "healthcare-dental-implants",
        "name": "Dental Implants — Specialist",
        "niche": "healthcare",
        "description": "High-value dental implants page driving free consultation bookings.",
        "preview_image_url": None,
        "theme": {"primary": "#0f766e", "accent": "#20ccce", "style": "premium"},
        "sections": [
            _hero(
                "Implant specialist · Surrey",
                "Dental implants you can chew on, smile with, forget about.",
                "Free consultation · 0% finance · 10-year guarantee · Over 4,000 implants placed.",
                "Book free consultation",
            ),
            _features("The Whitfield process", [
                {"icon": "Search", "title": "Free 3D scan", "body": "Your specific bone structure mapped in 20 minutes."},
                {"icon": "Calendar", "title": "Same-day teeth", "body": "Walk in with a gap, walk out with a tooth."},
                {"icon": "Shield", "title": "10-year guarantee", "body": "Industry-leading on implant + crown."},
            ]),
            _testimonials("Real patients, real smiles", [
                {"name": "Geoff (61)", "rating": 5, "quote": "First steak in seven years. I almost cried."},
                {"name": "Maria (49)", "rating": 5, "quote": "Three implants in one morning. Pain-free."},
            ]),
            _lead_form("Book your free 3D scan", "Choose a slot — we'll confirm by text."),
            _cta("0% finance available", "Spread the cost over 36 months.", "See finance"),
        ],
    },

    # ── Real estate ─────────────────────────────────────────────────────────
    {
        "slug": "real-estate-valuation",
        "name": "Property Valuation",
        "niche": "real_estate",
        "description": "Free instant valuation lead capture for residential estate agents.",
        "preview_image_url": None,
        "theme": {"primary": "#1e293b", "accent": "#20ccce", "style": "premium"},
        "sections": [
            _hero(
                "Know your number",
                "What is your home actually worth in 2026?",
                "Free instant valuation + a follow-up in-person viewing if you want it.",
                "Get instant valuation",
            ),
            _features("Three numbers, no obligation", [
                {"icon": "Home", "title": "Instant estimate", "body": "AI valuation from Land Registry + local sold prices."},
                {"icon": "Users", "title": "Local expert", "body": "30-minute home visit from a senior valuer."},
                {"icon": "PoundSterling", "title": "Asking-price strategy", "body": "How to maximise final sale value."},
            ]),
            _testimonials("Recent sellers", [
                {"name": "The Hassan family", "rating": 5,
                 "quote": "Asking price beaten by £18k. They knew exactly which couple to back."},
            ]),
            _lead_form("Get my valuation", "Pop in your postcode — we'll show you a number in 30 seconds."),
            _faq([
                {"q": "Is the valuation actually free?", "a": "Yes — no obligation, no hard sell."},
                {"q": "Do you charge a fee if we sell?", "a": "Standard commission on completion. No fee for the valuation."},
            ]),
        ],
    },
    {
        "slug": "real-estate-letting",
        "name": "Landlord Letting Service",
        "niche": "real_estate",
        "description": "Landlord-focused letting service comparison landing page.",
        "preview_image_url": None,
        "theme": {"primary": "#0c1f12", "accent": "#20ccce", "style": "enterprise"},
        "sections": [
            _hero(
                "Letting & Management",
                "Tenanted in 14 days. Managed for life.",
                "Fixed-fee letting from £499. Full management from 6% — no rent, no fee.",
                "Get a free rental appraisal",
            ),
            _features("Three ways we save you tax & time", [
                {"icon": "Clock", "title": "14-day let or free", "body": "We refund the fee if we miss it."},
                {"icon": "FileText", "title": "Compliance handled", "body": "Gas, EICR, EPC, deposit protection — all managed."},
                {"icon": "Shield", "title": "Rent guarantee", "body": "Optional 12-month rent and legal cover."},
            ]),
            _testimonials("Landlords trust us", [
                {"name": "Robert F., 4 properties", "rating": 5,
                 "quote": "Switched three of my flats over. First quarter was the easiest I can remember."},
            ]),
            _lead_form("Free rental appraisal", "Tell us about your property — we'll respond within 4 hours."),
            _cta("Switch your management", "We handle the transfer paperwork in full.", "See switching offer"),
        ],
    },

    # ── Generic ─────────────────────────────────────────────────────────────
    {
        "slug": "generic-saas-launch",
        "name": "SaaS Product Launch",
        "niche": "generic",
        "description": "Crisp generic launch page for waitlists, beta sign-ups and product launches.",
        "preview_image_url": None,
        "theme": _theme_forest(),
        "sections": [
            _hero(
                "Beta launching this month",
                "Run your operation, not your inbox.",
                "All your customer ops in one place. Built for teams who actually ship.",
                "Join the beta",
            ),
            _features("What's in beta", [
                {"icon": "Inbox", "title": "Unified inbox", "body": "Email, SMS, WhatsApp — all in one thread."},
                {"icon": "Zap", "title": "Workflow engine", "body": "Drag-and-drop automations."},
                {"icon": "Sparkles", "title": "AI assistant", "body": "Asks the boring questions so you don't."},
            ]),
            _lead_form("Get on the list", "We invite 25 teams per week — be one of them."),
            _faq([
                {"q": "When does it launch?", "a": "Public launch later this quarter — beta opens immediately."},
                {"q": "What does beta cost?", "a": "Beta is free. Lifetime 30% off when we go GA."},
            ]),
        ],
    },
    {
        "slug": "generic-event-registration",
        "name": "Event Registration",
        "niche": "generic",
        "description": "Lightweight event-registration landing page with speaker grid and FAQ.",
        "preview_image_url": None,
        "theme": _theme_forest(),
        "sections": [
            _hero(
                "London · Friday 14 June",
                "Growth, AI and the future of UK SMBs.",
                "A single-day, single-track conference for founders, ops leaders and growth marketers. £149 — limited to 200 seats.",
                "Reserve your seat",
            ),
            _features("What you'll leave with", [
                {"icon": "Brain", "title": "An AI playbook", "body": "Templates and prompts you'll use Monday morning."},
                {"icon": "Users", "title": "A new network", "body": "100% UK SMB founders & operators."},
                {"icon": "Coffee", "title": "Genuinely great coffee", "body": "Three roasts. Two espresso bars. No filter coffee."},
            ]),
            _testimonials("From last year", [
                {"name": "Jenny M., founder", "rating": 5,
                 "quote": "Worth ten conferences. The hallway track alone paid for itself."},
            ]),
            _lead_form("Apply for a discounted seat", "We offer 30 scholarship seats every year."),
            _cta("Sponsorship", "Two sponsorships left for 2026.", "Become a sponsor"),
        ],
    },
]


# ── Public entrypoint ────────────────────────────────────────────────────────


async def seed_marketing_data(db: AsyncSession, *, replace: bool = False) -> dict[str, int]:
    """Idempotently seed marketing content.

    `replace=True` will overwrite existing rows on key/slug collisions.
    Returns a count of rows created per table.
    """
    counts = {"sections": 0, "reviews": 0, "templates": 0}

    # Sections
    for spec in SECTIONS:
        existing = (
            await db.execute(select(MarketingSection).where(MarketingSection.key == spec["key"]))
        ).scalar_one_or_none()
        if existing and not replace:
            continue
        if existing and replace:
            existing.title = spec.get("title")
            existing.description = spec.get("description")
            existing.data = spec["data"]
            existing.sort_order = spec.get("sort_order", 0)
            existing.is_published = True
            db.add(existing)
        else:
            db.add(
                MarketingSection(
                    id=uuid.uuid4(),
                    key=spec["key"],
                    title=spec.get("title"),
                    description=spec.get("description"),
                    data=spec["data"],
                    sort_order=spec.get("sort_order", 0),
                    is_published=True,
                )
            )
            counts["sections"] += 1

    # Reviews (seed only when empty)
    existing_count = (
        await db.execute(select(MarketingReview).limit(1))
    ).scalar_one_or_none()
    if existing_count is None or replace:
        for spec in SEED_REVIEWS:
            db.add(
                MarketingReview(
                    id=uuid.uuid4(),
                    author_name=spec["author_name"],
                    author_role=spec.get("author_role"),
                    author_location=spec.get("author_location"),
                    rating=spec["rating"],
                    quote=spec["quote"],
                    quote_raw=spec["quote"],
                    metric=spec.get("metric"),
                    is_featured=spec.get("is_featured", False),
                    is_carousel=True,
                    status="approved",
                    sanitised=False,
                    capture_source="manual",
                    created_at=datetime.now(timezone.utc),
                )
            )
            counts["reviews"] += 1

    # Templates
    for spec in TEMPLATES:
        existing_t = (
            await db.execute(select(LandingPageTemplate).where(LandingPageTemplate.slug == spec["slug"]))
        ).scalar_one_or_none()
        if existing_t and not replace:
            continue
        if existing_t and replace:
            existing_t.name = spec["name"]
            existing_t.niche = spec["niche"]
            existing_t.description = spec.get("description")
            existing_t.theme = spec.get("theme", {})
            existing_t.sections = spec.get("sections", [])
            existing_t.preview_image_url = spec.get("preview_image_url")
            db.add(existing_t)
        else:
            db.add(
                LandingPageTemplate(
                    id=uuid.uuid4(),
                    slug=spec["slug"],
                    name=spec["name"],
                    niche=spec["niche"],
                    description=spec.get("description"),
                    preview_image_url=spec.get("preview_image_url"),
                    theme=spec.get("theme", {}),
                    sections=spec.get("sections", []),
                    is_published=True,
                    sort_order=0,
                )
            )
            counts["templates"] += 1

    await db.commit()
    return counts
