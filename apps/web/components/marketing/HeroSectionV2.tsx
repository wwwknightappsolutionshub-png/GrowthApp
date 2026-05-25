import Link from 'next/link'
import { ArrowRight, CheckCircle2, CircleDot } from 'lucide-react'

import { HeroDashboardPreview } from '@/components/marketing/HeroDashboardPreview'

function EyebrowTag({ children }: { children: React.ReactNode }) {
  return (
    <span className="inline-flex items-center gap-2 rounded-full border border-border bg-muted/60 px-3 py-1 text-[11px] font-medium uppercase tracking-[0.14em] text-muted-foreground">
      <CircleDot className="h-3 w-3 text-brand-teal-500" />
      {children}
    </span>
  )
}

/**
 * Revised hero — same V1 light brand tokens, new layout & messaging.
 * Used on /preview-hero for side-by-side review against the live homepage hero.
 */
export function HeroSectionV2() {
  return (
    <section className="relative overflow-hidden border-b border-border">
      <div aria-hidden className="pointer-events-none absolute inset-0 bg-grid-faint opacity-50" />
      <div
        aria-hidden
        className="pointer-events-none absolute -left-32 top-0 h-[520px] w-[520px] rounded-full bg-brand-forest-700/5 blur-3xl"
      />
      <div
        aria-hidden
        className="pointer-events-none absolute -right-24 top-12 h-[420px] w-[420px] rounded-full bg-brand-teal-400/10 blur-3xl"
      />

      <div className="container relative grid items-center gap-12 py-16 text-center lg:grid-cols-12 lg:gap-16 lg:py-24 lg:text-left">
        <div className="lg:col-span-7">
          <EyebrowTag>Hero preview · revised copy & layout</EyebrowTag>

          <h1 className="mt-6 font-display text-4xl font-bold leading-[1.06] tracking-tight text-foreground sm:text-5xl xl:text-[58px] xl:leading-[1.05]">
            Stop chasing leads.{' '}
            <span className="text-brand-forest-700">Start closing them</span>{' '}
            while CustomerFlow handles the follow-up.
          </h1>

          <p className="mx-auto mt-6 max-w-2xl text-lg leading-relaxed text-muted-foreground lg:mx-0">
            The AI operating system for UK businesses — leads, CRM, bookings, quotes,
            reviews and cashflow in one place, with automations that fire the moment
            something happens.
          </p>

          <div className="mt-8 flex flex-wrap justify-center gap-2 lg:justify-start">
            {['New lead → SMS in 60s', 'Job done → review request', 'Quote sent → chase sequence'].map(
              (chip) => (
                <span
                  key={chip}
                  className="rounded-full border border-brand-forest-200 bg-brand-forest-50 px-3 py-1 text-xs font-medium text-brand-forest-800"
                >
                  {chip}
                </span>
              ),
            )}
          </div>

          <div className="mt-9 flex flex-col justify-center gap-3 sm:flex-row lg:justify-start">
            <Link
              href="/register"
              className="inline-flex items-center justify-center gap-2 rounded-md bg-brand-forest-700 px-6 py-3.5 text-sm font-semibold text-brand-forest-foreground shadow-brand transition-all hover:bg-brand-forest-800"
            >
              Start 14-day free trial
              <ArrowRight className="h-4 w-4" />
            </Link>
            <a
              href="#platform-preview"
              className="inline-flex items-center justify-center gap-2 rounded-md border border-border bg-background px-6 py-3.5 text-sm font-semibold text-foreground transition-all hover:border-foreground/40 hover:bg-muted/50"
            >
              See what changes below
            </a>
          </div>

          <ul className="mt-10 flex flex-wrap items-center justify-center gap-x-7 gap-y-3 text-sm text-muted-foreground lg:justify-start">
            {[
              'No credit card required',
              '14-day free trial',
              'GDPR compliant',
              'UK data residency',
            ].map((t) => (
              <li key={t} className="inline-flex items-center gap-2">
                <CheckCircle2 className="h-4 w-4 text-brand-forest-700" />
                {t}
              </li>
            ))}
          </ul>
        </div>

        <div className="mx-auto w-full max-w-xl lg:col-span-5 lg:max-w-none">
          <HeroDashboardPreview />
        </div>
      </div>
    </section>
  )
}
