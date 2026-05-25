import Link from 'next/link'
import { ArrowRight, Menu, TrendingUp } from 'lucide-react'

import { AnnouncementTicker } from '@/components/marketing/AnnouncementTicker'
import { AnimatedCounter } from '@/components/marketing/AnimatedCounter'
import { HeroSectionV2 } from '@/components/marketing/HeroSectionV2'

const navLinks = [
  { href: '#platform-preview', label: 'Platform' },
  { href: '#compare', label: 'Compare' },
]

const heroStats = [
  { value: 38, suffix: '+', label: 'Founding-cohort businesses' },
  { value: 12_400, label: 'Conversations automated' },
  { value: 1_280, suffix: '+', label: 'Reviews collected' },
  { value: 47, suffix: 's', label: 'Avg. response time' },
]

function BrandMark() {
  return (
    <span className="inline-flex items-center gap-2.5">
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

export default function PreviewHeroPage() {
  return (
    <div className="min-h-screen bg-background text-foreground">
      {/* Review banner */}
      <div className="sticky top-0 z-[110] border-b border-brand-teal-200 bg-brand-teal-50 px-4 py-2 text-center text-xs text-brand-forest-900">
        <span className="font-semibold">Hero section preview</span>
        {' — only the hero below is revised. '}
        <Link href="/" className="font-medium underline underline-offset-2 hover:text-brand-forest-700">
          View current homepage (V1 hero)
        </Link>
      </div>

      <header className="sticky top-[34px] z-[100] border-b border-border bg-background/80 backdrop-blur-md">
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
                className="flex h-10 w-10 cursor-pointer list-none items-center justify-center rounded-md border border-border bg-card text-muted-foreground [&::-webkit-details-marker]:hidden"
              >
                <Menu className="h-4 w-4" />
              </summary>
            </details>
          </div>
        </div>
      </header>

      <AnnouncementTicker />

      <HeroSectionV2 />

      {/* Unchanged V1 stat bar (for context) */}
      <section className="border-b border-border bg-card">
        <div className="container grid grid-cols-2 gap-px overflow-hidden md:grid-cols-4">
          {heroStats.map((s) => (
            <div key={s.label} className="bg-card px-6 py-8 text-center md:text-left">
              <p className="font-display text-3xl font-bold tabular text-foreground">
                <AnimatedCounter
                  value={s.value}
                  suffix={s.suffix}
                  compact={s.value >= 10_000}
                />
              </p>
              <p className="mt-1 text-sm text-muted-foreground">{s.label}</p>
            </div>
          ))}
        </div>
      </section>

      <section id="compare" className="border-b border-border bg-muted/30 py-16">
        <div className="container max-w-3xl text-center">
          <h2 className="font-display text-2xl font-bold text-foreground">What changed?</h2>
          <p className="mt-3 text-muted-foreground">
            This preview replaces <strong>only the hero</strong> — headline, subcopy, workflow chips,
            and background treatment. The dashboard mock, stat bar, and everything below on the live
            homepage stay the same.
          </p>
          <div className="mt-8 flex flex-wrap justify-center gap-3">
            <Link
              href="/"
              className="rounded-md border border-border bg-background px-5 py-2.5 text-sm font-semibold text-foreground hover:bg-muted/50"
            >
              V1 — current live
            </Link>
            <Link
              href="/preview-hero"
              className="rounded-md bg-brand-forest-700 px-5 py-2.5 text-sm font-semibold text-brand-forest-foreground shadow-brand"
            >
              V2 — this page
            </Link>
            <Link
              href="/preview-hero-v3"
              className="rounded-md border border-border px-5 py-2.5 text-sm font-semibold hover:bg-muted/50"
            >
              V3 — goal + demo
            </Link>
          </div>
        </div>
      </section>

      <section id="platform-preview" className="py-12">
        <div className="container rounded-xl border border-dashed border-border bg-muted/20 px-6 py-10 text-center text-sm text-muted-foreground">
          Remaining homepage sections (platform, pricing, FAQ, etc.) are unchanged on{' '}
          <Link href="/" className="font-medium text-brand-forest-700 underline underline-offset-2">
            customerflow.ai /
          </Link>
        </div>
      </section>
    </div>
  )
}
