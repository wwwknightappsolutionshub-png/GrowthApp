import Link from 'next/link'
import {
  ArrowRight,
  BarChart3,
  Bot,
  Calendar,
  CheckCircle2,
  MessageSquare,
  Sparkles,
  Star,
  Zap,
} from 'lucide-react'

export const metadata = {
  title: 'CustomerFlow AI — Preview V2',
  description: 'Alternative marketing homepage for side-by-side comparison.',
  robots: { index: false, follow: false },
}

const workflows = [
  {
    trigger: 'New lead arrives',
    steps: ['Instant SMS acknowledgement', 'Wait 2h', 'Email quote template', 'Notify owner if no reply'],
    icon: MessageSquare,
  },
  {
    trigger: 'Job marked complete',
    steps: ['Send review request', 'Wait 24h', 'Win-back offer if no review', 'Log on CRM timeline'],
    icon: Star,
  },
  {
    trigger: 'Booking confirmed',
    steps: ['Confirmation SMS', 'Reminder 24h before', 'Follow-up after visit', 'Invoice prompt'],
    icon: Calendar,
  },
]

const pillars = [
  {
    title: 'Capture',
    body: 'Leads from forms, ads, referrals, WhatsApp, and Google — one inbox, zero copy-paste.',
    icon: Sparkles,
  },
  {
    title: 'Convert',
    body: 'Quotes, bookings, and follow-ups run on autopilot while you stay in control.',
    icon: Zap,
  },
  {
    title: 'Grow',
    body: 'Reviews, loyalty, outreach, and AI social posts compound without hiring ops staff.',
    icon: BarChart3,
  },
]

export default function PreviewV2Page() {
  return (
    <>
      {/* Nav */}
      <header className="mx-auto flex max-w-6xl items-center justify-between px-6 py-5">
        <div className="flex items-center gap-2">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-amber-500/15 ring-1 ring-amber-500/40">
            <Bot className="h-5 w-5 text-amber-400" />
          </div>
          <span className="text-lg font-bold tracking-tight">CustomerFlow AI</span>
          <span className="rounded bg-amber-500/20 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider text-amber-300">
            V2 preview
          </span>
        </div>
        <nav className="hidden items-center gap-8 text-sm text-gray-400 md:flex">
          <a href="#workflows" className="hover:text-white">Workflows</a>
          <a href="#platform" className="hover:text-white">Platform</a>
          <a href="#compare" className="hover:text-white">Compare</a>
        </nav>
        <div className="flex items-center gap-3">
          <Link href="/login" className="text-sm text-gray-400 hover:text-white">
            Sign in
          </Link>
          <Link
            href="/register"
            className="inline-flex items-center gap-1.5 rounded-lg bg-amber-500 px-4 py-2 text-sm font-semibold text-gray-950 hover:bg-amber-400"
          >
            Start free trial
            <ArrowRight className="h-4 w-4" />
          </Link>
        </div>
      </header>

      {/* Hero */}
      <section className="mx-auto max-w-6xl px-6 pb-20 pt-8 md:pt-16">
        <div className="grid items-center gap-12 lg:grid-cols-2">
          <div>
            <p className="mb-4 inline-flex items-center gap-2 rounded-full border border-gray-800 bg-gray-900 px-3 py-1 text-xs text-gray-400">
              <span className="h-1.5 w-1.5 rounded-full bg-emerald-400" />
              Built for UK trades, salons, clinics & local services
            </p>
            <h1 className="text-4xl font-bold leading-[1.1] tracking-tight text-white md:text-5xl lg:text-6xl">
              Your business runs itself{' '}
              <span className="text-amber-400">while you do the work</span>
            </h1>
            <p className="mt-6 max-w-xl text-lg text-gray-400">
              One AI platform for leads, CRM, bookings, quotes, reviews, and money — with automations
              that actually fire when things happen, not when you remember to chase.
            </p>
            <div className="mt-8 flex flex-wrap gap-3">
              <Link
                href="/register"
                className="inline-flex items-center gap-2 rounded-xl bg-amber-500 px-6 py-3 text-sm font-semibold text-gray-950 hover:bg-amber-400"
              >
                Get started free
                <ArrowRight className="h-4 w-4" />
              </Link>
              <Link
                href="/"
                className="inline-flex items-center gap-2 rounded-xl border border-gray-700 px-6 py-3 text-sm font-medium text-gray-300 hover:border-gray-600 hover:text-white"
              >
                Compare with current site
              </Link>
            </div>
            <ul className="mt-8 grid gap-2 text-sm text-gray-400 sm:grid-cols-2">
              {['No card for 14-day trial', 'GDPR-ready UK hosting', 'Cancel anytime', 'Setup in under an hour'].map(
                (item) => (
                  <li key={item} className="flex items-center gap-2">
                    <CheckCircle2 className="h-4 w-4 shrink-0 text-emerald-400" />
                    {item}
                  </li>
                ),
              )}
            </ul>
          </div>

          {/* Mock dashboard card */}
          <div className="relative">
            <div className="absolute -inset-4 rounded-3xl bg-amber-500/10 blur-3xl" />
            <div className="relative overflow-hidden rounded-2xl border border-gray-800 bg-gray-900 shadow-2xl">
              <div className="flex items-center gap-2 border-b border-gray-800 px-4 py-3">
                <div className="flex gap-1.5">
                  <span className="h-2.5 w-2.5 rounded-full bg-red-500/80" />
                  <span className="h-2.5 w-2.5 rounded-full bg-amber-500/80" />
                  <span className="h-2.5 w-2.5 rounded-full bg-emerald-500/80" />
                </div>
                <span className="text-xs text-gray-500">dashboard.customerflow.ai</span>
              </div>
              <div className="grid gap-3 p-4 sm:grid-cols-2">
                {[
                  ['New leads today', '7', '+3 vs yesterday'],
                  ['Open conversations', '4', '2 need reply'],
                  ['Bookings this week', '12', '3 tomorrow'],
                  ['Reviews this month', '9', '4.8★ avg'],
                ].map(([label, value, sub]) => (
                  <div key={label} className="rounded-xl border border-gray-800 bg-gray-950 p-4">
                    <div className="text-xs text-gray-500">{label}</div>
                    <div className="mt-1 text-2xl font-bold text-white">{value}</div>
                    <div className="mt-1 text-xs text-emerald-400">{sub}</div>
                  </div>
                ))}
              </div>
              <div className="border-t border-gray-800 p-4">
                <div className="mb-2 text-xs font-semibold uppercase tracking-wider text-gray-500">
                  Live automations
                </div>
                <div className="space-y-2">
                  {['Lead → welcome SMS sent', 'Job complete → review request queued'].map((line) => (
                    <div
                      key={line}
                      className="flex items-center gap-2 rounded-lg bg-gray-950 px-3 py-2 text-xs text-gray-300"
                    >
                      <Zap className="h-3.5 w-3.5 text-amber-400" />
                      {line}
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Workflows */}
      <section id="workflows" className="border-y border-gray-800 bg-gray-900/50 py-20">
        <div className="mx-auto max-w-6xl px-6">
          <div className="max-w-2xl">
            <h2 className="text-3xl font-bold text-white">Automations that match real jobs</h2>
            <p className="mt-3 text-gray-400">
              Trigger on business events — not generic &quot;if this then that&quot; puzzles. Every run shows
              on the CRM timeline so you always know what fired.
            </p>
          </div>
          <div className="mt-10 grid gap-6 md:grid-cols-3">
            {workflows.map(({ trigger, steps, icon: Icon }) => (
              <article
                key={trigger}
                className="rounded-2xl border border-gray-800 bg-gray-950 p-6 hover:border-amber-500/30"
              >
                <div className="mb-4 flex h-10 w-10 items-center justify-center rounded-lg bg-amber-500/10">
                  <Icon className="h-5 w-5 text-amber-400" />
                </div>
                <h3 className="font-semibold text-white">{trigger}</h3>
                <ol className="mt-4 space-y-2">
                  {steps.map((step, i) => (
                    <li key={step} className="flex gap-2 text-sm text-gray-400">
                      <span className="font-mono text-xs text-amber-500/80">{i + 1}.</span>
                      {step}
                    </li>
                  ))}
                </ol>
              </article>
            ))}
          </div>
        </div>
      </section>

      {/* Platform pillars */}
      <section id="platform" className="py-20">
        <div className="mx-auto max-w-6xl px-6">
          <h2 className="text-center text-3xl font-bold text-white">One platform, three loops</h2>
          <div className="mt-12 grid gap-6 md:grid-cols-3">
            {pillars.map(({ title, body, icon: Icon }) => (
              <div key={title} className="text-center">
                <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-2xl bg-gray-900 ring-1 ring-gray-800">
                  <Icon className="h-6 w-6 text-amber-400" />
                </div>
                <h3 className="text-lg font-semibold text-white">{title}</h3>
                <p className="mt-2 text-sm text-gray-400">{body}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Compare strip */}
      <section id="compare" className="border-t border-gray-800 bg-gray-900 py-16">
        <div className="mx-auto max-w-4xl px-6 text-center">
          <h2 className="text-2xl font-bold text-white">Comparing designs?</h2>
          <p className="mt-3 text-gray-400">
            This V2 preview uses a dark, ops-focused layout with workflow-first messaging. The current
            homepage at <strong className="text-white">/</strong> uses the light forest brand with adaptive
            niche personalisation.
          </p>
          <div className="mt-8 flex flex-wrap justify-center gap-4">
            <Link
              href="/"
              className="rounded-lg border border-gray-700 px-5 py-2.5 text-sm font-medium text-gray-300 hover:text-white"
            >
              Current homepage (V1)
            </Link>
            <Link
              href="/register"
              className="rounded-lg bg-amber-500 px-5 py-2.5 text-sm font-semibold text-gray-950 hover:bg-amber-400"
            >
              Try the product
            </Link>
          </div>
        </div>
      </section>

      <footer className="border-t border-gray-800 py-8 text-center text-xs text-gray-600">
        CustomerFlow AI · Preview V2 · Not indexed · For internal comparison only
      </footer>
    </>
  )
}
