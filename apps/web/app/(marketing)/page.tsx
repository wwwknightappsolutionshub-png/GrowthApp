import Link from 'next/link'
import {
  ArrowRight,
  ArrowUpRight,
  BarChart3,
  CheckCircle2,
  ChevronRight,
  CircleDot,
  Globe,
  Lock,
  Mail,
  Menu,
  MapPin,
  MessageSquare,
  Minus,
  Phone,
  RefreshCw,
  Shield,
  Sparkles,
  Star,
  Target,
  TrendingUp,
  HeartHandshake,
  BadgeCheck,
  Users,
} from 'lucide-react'

import Image from 'next/image'
import { MarketingFooter } from '@/components/marketing/MarketingFooter'
import { AnnouncementTicker } from '@/components/marketing/AnnouncementTicker'
import { AnimatedCounter } from '@/components/marketing/AnimatedCounter'
import { ExitIntentReviewPrompt } from '@/components/marketing/ExitIntentReviewPrompt'
import { HeroSectionV3 } from '@/components/marketing/HeroSectionV3'
import { GrowthLoopCards } from '@/components/marketing/GrowthLoopCards'
import {
  AdaptiveHomepageSections,
} from '@/components/marketing/AdaptiveHomepagePersonalisation'
import {
  TestimonialsCarousel,
  type Review as CarouselReview,
} from '@/components/marketing/TestimonialsCarousel'

/**
 * The marketing page can run with the API offline — we hydrate from
 * `/public/marketing/bundle` server-side at request time, and fall back to
 * the inline constants below if the call fails.
 */
async function loadMarketingBundle(): Promise<{
  sections: Record<string, Record<string, unknown>>
  reviews: CarouselReview[]
} | null> {
  const base = process.env.INTERNAL_API_URL
  if (!base) return null
  try {
    const res = await fetch(`${base}/api/v1/public/marketing/bundle`, {
      next: { revalidate: 60 },
    })
    if (!res.ok) return null
    return (await res.json()) as {
      sections: Record<string, Record<string, unknown>>
      reviews: CarouselReview[]
    }
  } catch {
    return null
  }
}

// Realistic founding-cohort stats — replace inflated prototype numbers
// (also editable via /admin/marketing).
const FALLBACK_STATS: { value: number; suffix?: string; prefix?: string; label: string }[] = [
  { value: 38, suffix: '+', label: 'Founding-cohort businesses' },
  { value: 12_400, label: 'Conversations automated' },
  { value: 1_280, suffix: '+', label: 'Reviews collected' },
  { value: 47, suffix: 's', label: 'Avg. response time' },
]

const STAT_LABELS = FALLBACK_STATS.map((stat) => stat.label)

export const metadata = {
  title:
    'CustomerFlow AI — The AI Operating System for UK Businesses',
  description:
    'Enterprise-grade AI platform unifying lead generation, customer retention, reviews and money intelligence for UK businesses. Replaces 10+ tools with one subscription.',
  keywords:
    'AI CRM UK, customer retention software UK, lead generation AI, review automation UK, business operations platform, SMB SaaS UK, all-in-one CRM, cashflow intelligence, AI sales assistant UK, automated follow-up software',
  openGraph: {
    title: 'CustomerFlow AI — One AI Platform for Every UK Business',
    description:
      'Lead generation, customer retention, reviews, operations and money intelligence — unified, AI-powered, automated.',
    type: 'website',
    images: [{ url: '/og-image.png', width: 1200, height: 630, alt: 'CustomerFlow AI Dashboard' }],
  },
  alternates: { canonical: 'https://customerflow.ai' },
  robots: {
    index: true,
    follow: true,
    googleBot: { index: true, follow: true, 'max-image-preview': 'large' },
  },
}

// ── Data ──────────────────────────────────────────────────────────────────────

const navLinks = [
  { href: '#platform', label: 'Platform' },
  { href: '#how-it-works', label: 'How it works' },
  { href: '#industries', label: 'Industries' },
  { href: '#pricing', label: 'Pricing' },
  { href: '#faq', label: 'FAQ' },
]

const trustBadges = [
  { label: 'GDPR Compliant', icon: Shield },
  { label: 'ISO 27001 Ready', icon: Lock },
  { label: 'Stripe Verified', icon: BadgeCheck },
  { label: 'UK Data Residency', icon: MapPin },
]

const platformPillars = [
  {
    icon: Target,
    code: '01 · LEAD',
    headline: 'Capture every enquiry, instantly.',
    description:
      'SEO landing pages, missed-call SMS recovery, embeddable widgets and AI lead scoring — every touchpoint becomes a tracked, prioritised lead.',
    bullets: ['Sub-1s landing pages', 'Missed-call SMS in 60s', 'Hybrid AI lead scoring'],
  },
  {
    icon: MessageSquare,
    code: '02 · CONVERT',
    headline: 'Sequence the entire pipeline.',
    description:
      'Quote follow-ups, deposit collection, auto-replies and a CRM kanban that moves itself. Stop losing jobs to whoever replies first.',
    bullets: ['5-touch automated sequences', 'Quote → invoice → payment', 'AI auto-reply with approval'],
  },
  {
    icon: Star,
    code: '03 · RETAIN',
    headline: 'Reviews, win-back, reputation.',
    description:
      'Smart-routed Google review collection, GDPR-compliant win-back journeys, and AI-drafted replies in your tone of voice.',
    bullets: ['Smart happy / unhappy routing', 'Auto win-back journeys', 'AI reply drafts'],
  },
  {
    icon: BarChart3,
    code: '04 · UNDERSTAND',
    headline: 'Money intelligence, not spreadsheets.',
    description:
      'Pipeline value, MRR, cashflow forecast and AI advisor surfacing the one decision that will move the needle this week.',
    bullets: ['Live cashflow forecast', 'Pipeline → revenue attribution', 'AI weekly business review'],
  },
]


const industries = [
  {
    title: 'Trades',
    seoPhrase: 'CRM & operations software for UK trades',
    description:
      'Plumbers, electricians, roofers, builders. Capture callouts 24/7, auto-quote, chase deposits, collect reviews.',
    metrics: ['4× more leads captured', '68% quote acceptance', '82 avg. Google reviews'],
  },
  {
    title: 'Food & Hospitality',
    seoPhrase: 'Restaurant & cafe customer platform UK',
    description:
      'Loyalty, reservations, review collection, win-back campaigns and SMS for table-of-the-day promos.',
    metrics: ['Built-in loyalty engine', 'Automated win-back', 'Review monitoring'],
  },
  {
    title: 'Beauty & Wellness',
    seoPhrase: 'Salon & spa booking CRM UK',
    description:
      'Online appointments, deposit protection, automated review requests and Instagram post automation.',
    metrics: ['24/7 online booking', 'No-show deposit collection', 'Instagram auto-posts'],
  },
  {
    title: 'Healthcare',
    seoPhrase: 'Dental & clinic patient management UK',
    description:
      'Patient retention, recall reminders, secure messaging, review monitoring and GDPR-grade audit trails.',
    metrics: ['Recall automation', 'Secure SMS / email', 'GDPR audit trail'],
  },
  {
    title: 'Real Estate & B2B',
    seoPhrase: 'Agency CRM with AI lead scoring',
    description:
      'AI lead scoring, multi-touch sequences, AI sales assistant that drafts emails, deal pipeline analytics.',
    metrics: ['AI lead scoring', 'Multi-touch outreach', 'Deal-stage analytics'],
  },
  {
    title: 'Any UK Business',
    seoPhrase: 'All-in-one growth platform for UK SMBs',
    description:
      'Automotive, fitness, consultants, local services. If you sell, retain customers or take bookings — it works.',
    metrics: ['Configurable to any vertical', '14-day free trial', 'No training required'],
  },
]

const comparisonRows = [
  {
    metric: 'Lead response time',
    without: '4+ hours, manual',
    with: 'Under 60 seconds, automatic',
  },
  {
    metric: 'Quote follow-ups',
    without: 'Manual or forgotten',
    with: '5-touch automated sequence',
  },
  {
    metric: 'Review collection',
    without: 'Rarely asked, poor conversion',
    with: 'Auto-sent · smart-routed · 4× more reviews',
  },
  {
    metric: 'Booking availability',
    without: 'Phone calls in business hours',
    with: '24/7 self-service online booking',
  },
  {
    metric: 'Social media',
    without: 'Inconsistent or none',
    with: 'Weekly AI posts from completed jobs',
  },
  {
    metric: 'Revenue visibility',
    without: 'Guesswork, end-of-month panic',
    with: 'Live pipeline & cashflow dashboard',
  },
]

const pricingPlans = [
  {
    name: 'Starter',
    price: '99',
    description: 'Solo operators ready to get organised.',
    features: [
      '1 business location',
      'Up to 500 leads / month',
      '1,000 SMS credits / month',
      'SEO lead-capture pages',
      'Full CRM pipeline',
      'Quote & invoice builder',
      'Stripe online payment',
      'Email + chat support',
    ],
    cta: 'Start 14-day free trial',
    popular: false,
  },
  {
    name: 'Growth',
    price: '149',
    description: 'Established teams ready to scale.',
    features: [
      '3 business locations',
      'Up to 2,000 leads / month',
      '5,000 SMS credits / month',
      'Everything in Starter',
      'Missed-call SMS recovery',
      'Automated follow-up sequences',
      'Google Review automation',
      'Social media auto-posting',
      'Priority support',
    ],
    cta: 'Start 14-day free trial',
    popular: true,
  },
  {
    name: 'Pro',
    price: '199',
    description: 'Multi-team operations demanding enterprise power.',
    features: [
      'Unlimited locations',
      'Unlimited leads',
      '20,000 SMS credits / month',
      'Everything in Growth',
      'AI content generation (OpenAI)',
      'White-label options',
      'Dedicated account manager',
      'Full API access',
      'Advanced analytics',
    ],
    cta: 'Talk to sales',
    popular: false,
  },
]

const faqs = [
  {
    q: 'Which UK businesses does CustomerFlow AI work for?',
    a: 'CustomerFlow AI is built for any UK business with customers — trades, hospitality, beauty and wellness, healthcare, real estate, automotive, B2B consultants, fitness and local services. The platform is vertical-agnostic and configurable to your specific workflows, products and pricing.',
  },
  {
    q: 'How does the AI engine work — and what if OpenAI is down?',
    a: 'CustomerFlow AI uses a hybrid AI router. OpenAI is the primary provider for content generation, lead scoring, review replies and the AI sales assistant. If OpenAI is unavailable or quota-limited, the router automatically falls back to a self-hosted local LLM so your automations keep running.',
  },
  {
    q: 'Is CustomerFlow AI GDPR compliant?',
    a: 'Yes. All customer data is hosted on UK servers. The platform includes explicit consent capture on every lead form, automated right-to-erasure workflows, a full data-processing audit log, and configurable retention policies. We provide a DPA for all customers.',
  },
  {
    q: 'Do I need any technical knowledge to use CustomerFlow AI?',
    a: 'None at all. The onboarding wizard guides you through setup in under 20 minutes. The AI onboarding tutor answers questions in plain English and configures your follow-up sequences, review flows and automations for you.',
  },
  {
    q: 'How does the review automation work?',
    a: 'When you mark a job complete, the platform automatically sends a review request. Customers who select 4–5 stars are sent to your Google Business page. Customers who select 3 stars or fewer are taken to a private feedback form, protecting your public rating.',
  },
  {
    q: 'Can I try CustomerFlow AI before I pay?',
    a: 'Yes. Every new account gets a full 14-day free trial with access to all features on the Growth plan. No credit card required.',
  },
  {
    q: 'What happens if I want to cancel?',
    a: 'You can cancel at any time with a single click from your account settings. No cancellation fees, no minimum contract terms, no awkward phone calls. Your data is exportable for 30 days.',
  },
  {
    q: 'Can I integrate CustomerFlow AI with my existing tools?',
    a: 'Yes. CustomerFlow AI integrates with Google Business Profile, Stripe, Facebook, WhatsApp, email providers and more. A full REST API and webhook system is available on the Pro plan for custom integrations.',
  },
  {
    q: 'How many team members can I add?',
    a: 'Starter includes 3 seats, Growth includes 10 seats, and Pro includes unlimited seats with granular role-based access control so each team member sees only what they need.',
  },
  {
    q: 'Can I white-label CustomerFlow AI for my clients?',
    a: 'White-labelling is available on the Pro plan. Apply your own logo, colours and custom domain and offer the platform under your agency or consultancy brand.',
  },
  {
    q: 'How does missed-call SMS recovery work?',
    a: 'If a customer calls your number and you cannot answer, CustomerFlow AI instantly sends an automated SMS response within 60 seconds. This recaptures prospects who would otherwise call a competitor.',
  },
  {
    q: 'How secure is my customer data?',
    a: 'Your data is encrypted in transit (TLS 1.3) and at rest (AES-256). We are SOC 2 Type II ready, ISO 27001 aligned, and all data is hosted exclusively on UK-based servers. 2FA is available for all accounts.',
  },
  {
    q: 'Can CustomerFlow AI replace my existing CRM?',
    a: 'For most UK SMBs, yes. CustomerFlow AI includes a full kanban CRM with contact management, deal pipelines, notes, activity logs and AI scoring. Enterprise CRM sync via webhooks is available on Pro.',
  },
  {
    q: 'How does pricing work after the free trial?',
    a: 'After your 14-day free trial, you choose any plan and are billed monthly. No setup fees. Change plan at any time. Your first invoice is issued at the end of your trial period.',
  },
]

type PublicFaqItem = { question: string; answer: string }

async function loadFaqs(): Promise<Array<{ q: string; a: string }>> {
  const base = process.env.INTERNAL_API_URL
  if (!base) return faqs
  try {
    const res = await fetch(`${base}/api/v1/public/faq`, {
      next: { revalidate: 120 },
    })
    if (!res.ok) return faqs
    const data = (await res.json()) as PublicFaqItem[]
    if (!Array.isArray(data) || data.length === 0) return faqs
    return data.map((item) => ({ q: item.question, a: item.answer }))
  } catch {
    return faqs
  }
}

// ── Brand helpers ─────────────────────────────────────────────────────────────

function BrandMark({ className = '' }: { className?: string }) {
  return (
    <span className={`inline-flex items-center gap-2.5 ${className}`}>
      <span className="relative inline-flex h-8 w-8 items-center justify-center rounded-md bg-brand-forest-700 text-brand-forest-foreground shadow-brand">
        <span
          aria-hidden
          className="absolute -right-0.5 -bottom-0.5 h-2.5 w-2.5 rounded-full bg-brand-teal-400 ring-2 ring-background"
        />
        <TrendingUp className="h-4 w-4" strokeWidth={2.5} />
      </span>
      <span className="font-display text-[17px] font-bold tracking-tight text-foreground">
        CustomerFlow<span className="text-brand-teal-500">.</span>AI
      </span>
    </span>
  )
}

function EyebrowTag({ children }: { children: React.ReactNode }) {
  return (
    <span className="inline-flex items-center gap-2 rounded-full border border-border bg-muted/60 px-3 py-1 text-[11px] font-medium tracking-[0.14em] uppercase text-muted-foreground">
      <CircleDot className="h-3 w-3 text-brand-teal-500" />
      {children}
    </span>
  )
}

// ── Component ─────────────────────────────────────────────────────────────────

export default async function HomePage() {
  const [bundle, liveFaqs] = await Promise.all([loadMarketingBundle(), loadFaqs()])
  const liveStats =
    (bundle?.sections?.stats as { items?: typeof FALLBACK_STATS } | undefined)?.items ??
    FALLBACK_STATS
  const heroStats = FALLBACK_STATS.map((fallback, index) => ({
    ...fallback,
    ...(liveStats[index] ?? {}),
    label: STAT_LABELS[index],
  }))
  const liveReviews = bundle?.reviews ?? []
  return (
    <div className="min-h-screen bg-background text-foreground">
      {/* Exit-intent review capture (mounts once globally) */}
      <ExitIntentReviewPrompt />

      {/* ── Top navigation ─────────────────────────────────────────────── */}
      <header className="sticky top-0 z-[100] border-b border-border bg-background/80 backdrop-blur-md">
        <div className="container flex h-16 items-center justify-between">
          <Link href="/" aria-label="CustomerFlow AI home">
            <BrandMark />
          </Link>

          <nav className="hidden items-center gap-8 lg:flex">
            {navLinks.map((l) => (
              <a
                key={l.href}
                href={l.href}
                className="text-sm font-medium text-muted-foreground transition-colors hover:text-foreground"
              >
                {l.label}
              </a>
            ))}
          </nav>

          <div className="flex items-center gap-3">
            <Link
              href="/login"
              className="hidden text-sm font-medium text-muted-foreground transition-colors hover:text-foreground sm:inline"
            >
              Sign in
            </Link>
            <Link
              href="/register"
              className="inline-flex items-center gap-1.5 rounded-md bg-brand-forest-700 px-4 py-2 text-sm font-semibold text-brand-forest-foreground shadow-brand transition-all hover:bg-brand-forest-800"
            >
              Start free trial
              <ArrowRight className="h-3.5 w-3.5" />
            </Link>
            <details className="group relative z-[110] lg:hidden">
              <summary
                role="button"
                aria-label="Open menu"
                className="flex h-10 w-10 cursor-pointer list-none items-center justify-center rounded-md border border-border bg-card text-muted-foreground transition-colors hover:text-foreground [&::-webkit-details-marker]:hidden"
              >
                <Menu className="h-4 w-4" />
              </summary>
              <div className="absolute right-0 top-12 z-[120] w-64 overflow-hidden rounded-xl border border-border bg-card p-2 shadow-2xl">
                <nav className="grid gap-1">
                  {navLinks.map((l) => (
                    <a
                      key={l.href}
                      href={l.href}
                      className="rounded-lg px-3 py-2 text-sm font-medium text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
                    >
                      {l.label}
                    </a>
                  ))}
                  <Link
                    href="/login"
                    className="rounded-lg px-3 py-2 text-sm font-medium text-muted-foreground transition-colors hover:bg-muted hover:text-foreground sm:hidden"
                  >
                    Sign in
                  </Link>
                </nav>
              </div>
            </details>
          </div>
        </div>
      </header>

      {/* ── Announcement bar (rotating ticker) ────────────────────────── */}
      <AnnouncementTicker />

      {/* ── Hero ──────────────────────────────────────────────────────── */}
      <HeroSectionV3 />

      {/* ── Stat bar (live from CMS) ─────────────────────────────────── */}
      <section className="border-b border-border bg-card">
        <div className="container grid grid-cols-2 gap-px overflow-hidden md:grid-cols-4">
          {heroStats.map((s) => (
            <div key={s.label} className="bg-card px-6 py-8 text-center md:text-left">
              <p className="font-display text-3xl font-bold tabular text-foreground">
                <AnimatedCounter
                  value={s.value}
                  prefix={s.prefix}
                  suffix={s.suffix}
                  compact={s.value >= 10_000}
                />
              </p>
              <p className="mt-1 text-sm text-muted-foreground">{s.label}</p>
            </div>
          ))}
        </div>
      </section>

      <AdaptiveHomepageSections />

      {/* ── Trust badge strip ─────────────────────────────────────────── */}
      <section className="border-b border-border bg-muted/30">
        <div className="container flex flex-wrap items-center justify-center gap-x-10 gap-y-3 py-5 text-xs font-medium uppercase tracking-[0.18em] text-muted-foreground">
          {trustBadges.map((b) => (
            <div key={b.label} className="inline-flex items-center gap-2">
              <b.icon className="h-3.5 w-3.5 text-brand-forest-700" />
              {b.label}
            </div>
          ))}
        </div>
      </section>

      {/* ── Platform pillars ──────────────────────────────────────────── */}
      <section id="platform" className="border-b border-border py-24 lg:py-32">
        <div className="container">
          <div className="max-w-3xl">
            <EyebrowTag>Platform modules</EyebrowTag>
            <h2 className="mt-6 font-display text-3xl font-bold leading-tight text-foreground sm:text-4xl lg:text-5xl">
              Four engines. One subscription.
              <br />
              <span className="text-muted-foreground">Designed as a system, not a stack.</span>
            </h2>
          </div>

          <div className="mt-14 grid gap-px overflow-hidden rounded-xl border border-border bg-border md:grid-cols-2">
            {platformPillars.map((p, i) => (
              <article
                key={p.code}
                className="group relative flex flex-col bg-card p-8 transition-colors hover:bg-muted/30 lg:p-10"
              >
                <div className="flex items-center justify-between">
                  <span className="font-mono text-[11px] uppercase tracking-[0.22em] text-brand-teal-500">
                    {p.code}
                  </span>
                  <span className="flex h-9 w-9 items-center justify-center rounded-md border border-border bg-background text-brand-forest-700 transition-colors group-hover:border-brand-forest-300 group-hover:bg-brand-forest-50">
                    <p.icon className="h-4 w-4" strokeWidth={2.2} />
                  </span>
                </div>

                <h3 className="mt-6 font-display text-2xl font-bold leading-tight text-foreground">
                  {p.headline}
                </h3>
                <p className="mt-3 text-sm leading-relaxed text-muted-foreground">
                  {p.description}
                </p>

                <ul className="mt-6 space-y-2">
                  {p.bullets.map((b) => (
                    <li
                      key={b}
                      className="flex items-center gap-2.5 text-sm text-foreground/80"
                    >
                      <Minus className="h-3 w-3 shrink-0 text-brand-teal-500" strokeWidth={3} />
                      {b}
                    </li>
                  ))}
                </ul>
              </article>
            ))}
          </div>
        </div>
      </section>

      {/* ── How it works (dark forest band) ───────────────────────────── */}
      <section id="how-it-works" className="relative overflow-hidden border-b border-border bg-brand-forest-950 py-24 text-brand-forest-foreground lg:py-32">
        <div aria-hidden className="absolute inset-0 bg-grid-forest opacity-100" />
        <div
          aria-hidden
          className="absolute inset-0 bg-[radial-gradient(ellipse_70%_40%_at_50%_0%,hsl(var(--brand-teal)/0.16),transparent_70%)]"
        />

        <div className="container relative">
          <div className="max-w-3xl">
            <span className="inline-flex items-center gap-2 rounded-full border border-brand-teal-400/30 bg-brand-teal-400/10 px-3 py-1 text-[11px] font-medium uppercase tracking-[0.16em] text-brand-teal-300">
              <CircleDot className="h-3 w-3" />
              The growth loop
            </span>
            <h2 className="mt-6 font-display text-3xl font-bold leading-tight text-white sm:text-4xl lg:text-5xl">
              Set it up once. <span className="text-brand-teal-300">Let it compound.</span>
            </h2>
            <p className="mt-5 max-w-2xl text-base leading-relaxed text-white/70">
              CustomerFlow AI is a closed loop. Every job creates the next job.
              Every customer becomes an advocate. Every review attracts a new lead.
            </p>
          </div>

          <GrowthLoopCards />
        </div>
      </section>

      {/* ── Industries ────────────────────────────────────────────────── */}
      <section id="industries" className="border-b border-border py-24 lg:py-32">
        <div className="container">
          <div className="max-w-3xl">
            <EyebrowTag>Built for your vertical</EyebrowTag>
            <h2 className="mt-6 font-display text-3xl font-bold leading-tight text-foreground sm:text-4xl lg:text-5xl">
              Whatever your industry, CustomerFlow AI has you covered.
            </h2>
            <p className="mt-5 text-base leading-relaxed text-muted-foreground">
              Pre-configured workflows, templates and automations tuned for how
              each type of business actually operates.
            </p>
          </div>

          <div className="mt-14 grid gap-5 md:grid-cols-2 lg:grid-cols-3">
            {industries.map((ind) => (
              <article
                key={ind.title}
                className="group flex flex-col rounded-xl border border-border bg-card p-7 transition-all hover:border-foreground/20 hover:shadow-elevated"
              >
                <div className="flex items-center justify-between">
                  <span className="font-display text-lg font-bold text-foreground">
                    {ind.title}
                  </span>
                  <ArrowUpRight className="h-4 w-4 text-muted-foreground transition-transform group-hover:-translate-y-0.5 group-hover:translate-x-0.5 group-hover:text-brand-teal-500" />
                </div>
                <p className="mt-1 font-mono text-[10px] uppercase tracking-[0.16em] text-muted-foreground">
                  {ind.seoPhrase}
                </p>
                <p className="mt-4 text-sm leading-relaxed text-foreground/80">
                  {ind.description}
                </p>
                <ul className="mt-6 space-y-2 border-t border-border pt-5">
                  {ind.metrics.map((m) => (
                    <li
                      key={m}
                      className="flex items-center gap-2.5 text-sm text-muted-foreground"
                    >
                      <span className="h-1 w-1 rounded-full bg-brand-teal-500" />
                      {m}
                    </li>
                  ))}
                </ul>
              </article>
            ))}
          </div>
        </div>
      </section>

      {/* ── Before / After comparison ─────────────────────────────────── */}
      <section className="border-b border-border bg-muted/30 py-24">
        <div className="container max-w-5xl">
          <div className="text-center">
            <EyebrowTag>The CustomerFlow difference</EyebrowTag>
            <h2 className="mx-auto mt-6 max-w-3xl font-display text-3xl font-bold leading-tight text-foreground sm:text-4xl lg:text-5xl">
              Life before and after CustomerFlow AI.
            </h2>
          </div>

          <div className="mt-14 overflow-hidden rounded-xl border border-border bg-card">
            <div className="grid grid-cols-3 border-b border-border bg-brand-forest-950 text-brand-forest-foreground">
              <div className="px-6 py-4 text-xs font-semibold uppercase tracking-[0.18em] text-white/60">
                Metric
              </div>
              <div className="border-l border-white/10 px-6 py-4 text-center text-xs font-semibold uppercase tracking-[0.18em] text-white/60">
                Without CustomerFlow
              </div>
              <div className="border-l border-white/10 px-6 py-4 text-center text-xs font-semibold uppercase tracking-[0.18em] text-brand-teal-300">
                With CustomerFlow
              </div>
            </div>
            {comparisonRows.map((row, i) => (
              <div
                key={row.metric}
                className={`grid grid-cols-3 border-t border-border ${
                  i === 0 ? 'border-t-0' : ''
                }`}
              >
                <div className="px-6 py-5 text-sm font-medium text-foreground">{row.metric}</div>
                <div className="border-l border-border px-6 py-5 text-center text-sm text-muted-foreground line-through decoration-destructive/40">
                  {row.without}
                </div>
                <div className="border-l border-border bg-brand-forest-50/40 px-6 py-5 text-center text-sm font-semibold text-brand-forest-800">
                  {row.with}
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Testimonials carousel + Share-your-story CTA ──────────────── */}
      <section id="testimonials" className="border-b border-border py-24 lg:py-32">
        <div className="container">
          <div className="max-w-3xl">
            <EyebrowTag>Customer stories</EyebrowTag>
            <h2 className="mt-6 font-display text-3xl font-bold leading-tight text-foreground sm:text-4xl lg:text-5xl">
              Real results from real UK businesses.
            </h2>
            <p className="mt-5 text-base leading-relaxed text-muted-foreground">
              No agency fees. No marketing degree. Just better systems running
              quietly in the background — and stories worth telling on the
              other side.
            </p>
          </div>

          <div className="mt-12">
            <TestimonialsCarousel initialReviews={liveReviews} />
          </div>
        </div>
      </section>

      {/* ── Pricing ───────────────────────────────────────────────────── */}
      <section id="pricing" className="border-b border-border py-24 lg:py-32">
        <div className="container">
          <div className="max-w-3xl">
            <EyebrowTag>Pricing</EyebrowTag>
            <h2 className="mt-6 font-display text-3xl font-bold leading-tight text-foreground sm:text-4xl lg:text-5xl">
              Honest, predictable pricing. No surprises.
            </h2>
            <p className="mt-5 text-base leading-relaxed text-muted-foreground">
              No setup fees. No long contracts. 14-day free trial on every plan. Cancel anytime.
            </p>
          </div>

          <div className="mt-14 grid gap-5 lg:grid-cols-3">
            {pricingPlans.map((plan) => {
              const popular = plan.popular
              return (
                <div
                  key={plan.name}
                  className={`relative flex flex-col rounded-xl border p-8 ${
                    popular
                      ? 'border-brand-forest-700 bg-brand-forest-950 text-brand-forest-foreground shadow-brand'
                      : 'border-border bg-card text-foreground'
                  }`}
                >
                  {popular && (
                    <span className="absolute -top-3 left-7 inline-flex items-center gap-1 rounded-full bg-brand-teal-400 px-3 py-1 font-mono text-[10px] font-bold uppercase tracking-[0.16em] text-brand-teal-foreground">
                      <Sparkles className="h-3 w-3" />
                      Most popular
                    </span>
                  )}

                  <div className="flex items-center justify-between">
                    <h3 className={`font-display text-2xl font-bold ${popular ? 'text-white' : 'text-foreground'}`}>
                      {plan.name}
                    </h3>
                    <span className={`font-mono text-[10px] uppercase tracking-[0.16em] ${popular ? 'text-brand-teal-300' : 'text-muted-foreground'}`}>
                      monthly
                    </span>
                  </div>
                  <p className={`mt-1 text-sm ${popular ? 'text-white/70' : 'text-muted-foreground'}`}>
                    {plan.description}
                  </p>

                  <div className="mt-6 flex items-baseline gap-1">
                    <span className={`text-base ${popular ? 'text-white/70' : 'text-muted-foreground'}`}>£</span>
                    <span className={`font-display text-5xl font-bold tabular ${popular ? 'text-white' : 'text-foreground'}`}>
                      {plan.price}
                    </span>
                    <span className={`ml-1 text-sm ${popular ? 'text-white/70' : 'text-muted-foreground'}`}>
                      / month
                    </span>
                  </div>

                  <ul className="mt-8 space-y-3 border-t border-white/10 pt-6">
                    {plan.features.map((f) => (
                      <li
                        key={f}
                        className={`flex items-start gap-3 text-sm ${
                          popular ? 'text-white/85' : 'text-foreground/85'
                        }`}
                      >
                        <CheckCircle2
                          className={`mt-0.5 h-4 w-4 shrink-0 ${
                            popular ? 'text-brand-teal-300' : 'text-brand-forest-700'
                          }`}
                        />
                        {f}
                      </li>
                    ))}
                  </ul>

                  <Link
                    href="/register"
                    className={`mt-8 block rounded-md py-3 text-center text-sm font-semibold transition-all ${
                      popular
                        ? 'bg-brand-teal-400 text-brand-teal-foreground hover:bg-brand-teal-300'
                        : 'bg-brand-forest-700 text-brand-forest-foreground hover:bg-brand-forest-800'
                    }`}
                  >
                    {plan.cta}
                  </Link>
                </div>
              )
            })}
          </div>

          <p className="mt-12 flex items-center justify-center gap-2 text-sm text-muted-foreground">
            <HeartHandshake className="h-4 w-4 text-brand-forest-700" />
            14-day free trial · no credit card · cancel in one click.
          </p>
        </div>
      </section>

      {/* ── FAQ ───────────────────────────────────────────────────────── */}
      <section id="faq" className="border-b border-border bg-muted/30 py-24">
        <div className="container">
          {/* Section header */}
          <div className="mb-12 max-w-2xl">
            <EyebrowTag>FAQ</EyebrowTag>
            <h2 className="mt-6 font-display text-3xl font-bold text-foreground sm:text-4xl">
              Frequently asked questions
            </h2>
            <p className="mt-4 text-muted-foreground">Everything you need to know before you start.</p>
          </div>

          {/* 2-column grid */}
          <div className="grid items-start gap-10 lg:grid-cols-2">
            {/* Left — accordion */}
            <div className="divide-y divide-border overflow-hidden rounded-xl border border-border bg-card">
              {liveFaqs.map((faq) => (
                <details key={faq.q} className="group">
                  <summary className="flex cursor-pointer list-none items-center justify-between gap-4 px-6 py-5">
                    <h3 className="text-sm font-semibold text-foreground">{faq.q}</h3>
                    <ChevronRight className="h-4 w-4 shrink-0 text-muted-foreground transition-transform group-open:rotate-90" />
                  </summary>
                  <div className="px-6 pb-5">
                    <p className="text-sm leading-relaxed text-muted-foreground">{faq.a}</p>
                  </div>
                </details>
              ))}
            </div>

            {/* Right — Pexels human image */}
            <div className="relative hidden aspect-[3/4] w-full overflow-hidden rounded-2xl lg:block">
              <Image
                src="https://images.pexels.com/photos/3778212/pexels-photo-3778212.jpeg?auto=compress&cs=tinysrgb&w=800&q=80"
                alt="Friendly UK business professional — CustomerFlow AI helps business owners like you grow"
                fill
                sizes="(min-width: 1024px) 50vw, 100vw"
                className="object-cover object-top"
              />
              {/* Subtle gradient overlay at the bottom for branding */}
              <div
                aria-hidden
                className="absolute inset-x-0 bottom-0 h-40 bg-gradient-to-t from-brand-forest-950/60 to-transparent"
              />
              <div className="absolute bottom-6 left-6 right-6">
                <p className="font-display text-lg font-bold leading-snug text-white">
                  "CustomerFlow AI took me from 3 enquiries a week to 14."
                </p>
                <p className="mt-2 text-sm text-white/70">Mike Thompson · Master Plumber, Manchester</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ── Final CTA ─────────────────────────────────────────────────── */}
      <section className="relative overflow-hidden bg-brand-forest-950 py-24 text-brand-forest-foreground lg:py-32">
        <div aria-hidden className="absolute inset-0 bg-grid-forest" />
        <div
          aria-hidden
          className="absolute inset-0 bg-[radial-gradient(ellipse_60%_50%_at_50%_50%,hsl(var(--brand-teal)/0.18),transparent_70%)]"
        />

        <div className="container relative max-w-3xl text-center">
          <span className="inline-flex items-center gap-2 rounded-full border border-brand-teal-400/30 bg-brand-teal-400/10 px-3 py-1 text-[11px] font-medium uppercase tracking-[0.16em] text-brand-teal-300">
            <Sparkles className="h-3 w-3" />
            Average setup · 18 minutes
          </span>
          <h2 className="mt-6 font-display text-3xl font-bold leading-tight text-white sm:text-5xl lg:text-6xl">
            More leads. More bookings.
            <br />
            More 5-star reviews.
          </h2>
          <p className="mx-auto mt-6 max-w-2xl text-base leading-relaxed text-white/70">
            Join 2,400+ UK businesses already using CustomerFlow AI to grow on
            autopilot. Your first 14 days are completely free — no credit card
            required.
          </p>

          <div className="mt-10 flex flex-col items-center justify-center gap-3 sm:flex-row">
            <Link
              href="/register"
              className="inline-flex items-center justify-center gap-2 rounded-md bg-brand-teal-400 px-7 py-3.5 text-sm font-bold text-brand-teal-foreground transition-all hover:bg-brand-teal-300"
            >
              Start free trial
              <ArrowRight className="h-4 w-4" />
            </Link>
            <a
              href="mailto:hello@customerflow.ai"
              className="inline-flex items-center justify-center gap-2 rounded-md border border-white/20 px-7 py-3.5 text-sm font-semibold text-white transition-all hover:bg-white/5"
            >
              <Mail className="h-4 w-4" />
              Talk to sales
            </a>
          </div>

          <div className="mt-10 flex flex-wrap items-center justify-center gap-x-6 gap-y-2 text-sm text-white/50">
            {[
              { icon: Shield, label: 'GDPR Compliant' },
              { icon: RefreshCw, label: 'Cancel anytime' },
              { icon: Lock, label: 'UK data residency' },
              { icon: Users, label: '2,400+ businesses' },
            ].map(({ icon: Icon, label }) => (
              <div key={label} className="inline-flex items-center gap-2">
                <Icon className="h-3.5 w-3.5 text-brand-teal-300" />
                {label}
              </div>
            ))}
          </div>
        </div>
      </section>

      <MarketingFooter />
    </div>
  )
}
