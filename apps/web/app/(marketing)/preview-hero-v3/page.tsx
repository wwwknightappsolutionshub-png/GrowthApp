import Link from 'next/link'
import { ArrowRight, Menu } from 'lucide-react'

import { BrandMark } from '@/components/brand/BrandMark'
import { AnnouncementTicker } from '@/components/marketing/AnnouncementTicker'
import { HeroSectionV3 } from '@/components/marketing/HeroSectionV3'

const navLinks = [
  { href: '#compare', label: 'Compare' },
  { href: '#goal', label: 'Product goal' },
]


export default function PreviewHeroV3Page() {
  return (
    <div className="min-h-screen bg-background text-foreground">
      <div className="sticky top-0 z-[110] border-b border-brand-forest-200 bg-brand-forest-50 px-4 py-2 text-center text-xs text-brand-forest-900">
        <span className="font-semibold">Hero V3</span>
        {' — redefined goal + animated Leads · CRM · Accounts demo. '}
        <Link href="/" className="font-medium underline underline-offset-2">
          V1
        </Link>
        {' · '}
        <Link href="/preview-hero" className="font-medium underline underline-offset-2">
          V2
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
              href="/register"
              className="inline-flex items-center gap-1.5 rounded-md bg-brand-forest-700 px-4 py-2 text-sm font-semibold text-brand-forest-foreground shadow-brand hover:bg-brand-forest-800"
            >
              Start free trial
              <ArrowRight className="h-3.5 w-3.5" />
            </Link>
            <details className="lg:hidden">
              <summary className="flex h-10 w-10 cursor-pointer list-none items-center justify-center rounded-md border border-border [&::-webkit-details-marker]:hidden">
                <Menu className="h-4 w-4" />
              </summary>
            </details>
          </div>
        </div>
      </header>

      <AnnouncementTicker />

      <HeroSectionV3 />

      <section id="goal" className="border-b border-border bg-muted/30 py-14">
        <div className="container max-w-3xl">
          <h2 className="font-display text-xl font-bold text-foreground">Redefined product goal</h2>
          <p className="mt-3 text-muted-foreground">
            CustomerFlow is not just a CRM or a lead tool — it is a{' '}
            <strong className="text-foreground">closed-loop growth system</strong>: Lead → CRM →
            Operate → Bill → Retain → Refer. The hero demo on the right auto-plays that story through
            three realistic screens: a lead arriving and getting an instant reply, a deal moving on
            the pipeline, and an invoice marked paid in Accounts.
          </p>
          <ul className="mt-6 grid gap-3 sm:grid-cols-2">
            {[
              'Lead generation & scoring',
              'CRM pipeline & customer records',
              'Operations (bookings, tasks, quotes)',
              'Money intelligence (invoices, cashflow)',
            ].map((item) => (
              <li
                key={item}
                className="rounded-lg border border-border bg-card px-4 py-3 text-sm text-foreground"
              >
                {item}
              </li>
            ))}
          </ul>
        </div>
      </section>

      <section id="icons" className="border-b border-border bg-card py-14">
        <div className="container max-w-3xl">
          <h2 className="font-display text-xl font-bold text-foreground">Brand icons</h2>
          <p className="mt-2 text-sm text-muted-foreground">
            Updated favicon (browser tab) and PWA install icon — forest green, teal accent, growth
            chart motif.
          </p>
          <div className="mt-8 flex flex-wrap items-end justify-center gap-10 sm:justify-start">
            <div className="text-center">
              <img
                src="/icons/icon.svg"
                alt="CustomerFlow favicon"
                width={64}
                height={64}
                className="mx-auto rounded-2xl shadow-elevated"
              />
              <p className="mt-2 text-xs font-medium text-muted-foreground">Favicon · 512 SVG</p>
            </div>
            <div className="text-center">
              <img
                src="/icons/pwa-icon.svg"
                alt="CustomerFlow PWA icon"
                width={96}
                height={96}
                className="mx-auto rounded-2xl shadow-elevated"
              />
              <p className="mt-2 text-xs font-medium text-muted-foreground">PWA install · 512 SVG</p>
            </div>
            <div className="text-center">
              <img
                src="/icons/maskable-icon.svg"
                alt="CustomerFlow maskable PWA icon"
                width={96}
                height={96}
                className="mx-auto rounded-none shadow-elevated"
              />
              <p className="mt-2 text-xs font-medium text-muted-foreground">Maskable · safe zone</p>
            </div>
            <div className="text-center">
              <img
                src="/apple-icon"
                alt="CustomerFlow Apple touch icon"
                width={96}
                height={96}
                className="mx-auto rounded-[22%] shadow-elevated"
              />
              <p className="mt-2 text-xs font-medium text-muted-foreground">Apple touch · 512 PNG</p>
            </div>
          </div>
        </div>
      </section>

      <section id="compare" className="py-14">
        <div className="container max-w-3xl text-center">
          <h2 className="font-display text-2xl font-bold">Compare hero versions</h2>
          <div className="mt-8 flex flex-wrap justify-center gap-3">
            <Link
              href="/"
              className="rounded-md border border-border px-5 py-2.5 text-sm font-semibold hover:bg-muted/50"
            >
              V1 — current live
            </Link>
            <Link
              href="/preview-hero"
              className="rounded-md border border-border px-5 py-2.5 text-sm font-semibold hover:bg-muted/50"
            >
              V2 — action copy
            </Link>
            <Link
              href="/preview-hero-v3"
              className="rounded-md bg-brand-forest-700 px-5 py-2.5 text-sm font-semibold text-brand-forest-foreground shadow-brand"
            >
              V3 — goal + demo (this page)
            </Link>
          </div>
        </div>
      </section>
    </div>
  )
}
