import Link from 'next/link'
import { ArrowRight, CheckCircle2 } from 'lucide-react'

import { HeroLoopCards } from '@/components/marketing/HeroLoopCards'
import { HeroProductDemo } from '@/components/marketing/HeroProductDemo'

function HeroEyebrow({ children }: { children: React.ReactNode }) {
  return (
    <p className="inline-flex max-w-xl flex-wrap items-center gap-x-1 text-sm font-medium leading-relaxed text-muted-foreground">
      <span className="mr-1 inline-block h-2 w-2 animate-pulse rounded-full bg-brand-teal-500" />
      {children}
    </p>
  )
}

export function HeroSectionV3() {
  return (
    <section className="relative overflow-hidden border-b border-border">
      <div aria-hidden className="pointer-events-none absolute inset-0 bg-grid-faint opacity-40" />
      <div
        aria-hidden
        className="pointer-events-none absolute inset-x-0 top-0 h-[560px] bg-[radial-gradient(ellipse_70%_55%_at_75%_0%,hsl(var(--brand-teal)/0.14),transparent_68%)]"
      />

      <div className="container relative grid items-stretch gap-8 py-14 text-center lg:grid-cols-12 lg:gap-6 lg:py-16 xl:gap-8 lg:text-left">
        <div className="flex h-full flex-col lg:col-span-5 xl:col-span-5">
          <HeroEyebrow>
            Attract leads. Automate follow-ups. Keep customers loyal. Grow revenue.
          </HeroEyebrow>

          <h1 className="mt-5 flex w-full flex-col items-start gap-0 text-left leading-none">
            <span className="font-display text-4xl font-extrabold tracking-tight text-brand-forest-700 sm:text-5xl lg:text-[65px]">
              One Platform
            </span>
            <span className="font-display mt-2 text-xl font-medium leading-snug text-foreground sm:text-2xl lg:hidden">
              for your customer journey not ten tools duct-taped together
            </span>
            <span className="font-display -mt-1.5 hidden text-[35px] font-medium text-foreground lg:block">
              for your customer journey
            </span>
            <span className="-mt-1 hidden text-[25px] italic text-muted-foreground lg:block">
              not ten tool duct-taped together
            </span>
          </h1>

          <p className="mx-auto mt-4 max-w-xl text-sm leading-relaxed text-muted-foreground lg:mx-0">
            CustomerFlowai unifies lead generation, CRM, operations, invoicing, and retention in a
            single closed loop — with AI and automations running quietly behind every step.
          </p>

          <HeroLoopCards />

          <div className="mt-6 flex flex-col justify-center gap-3 sm:flex-row lg:justify-start">
            <Link
              href="/register"
              aria-label="Start 14-day free trial"
              className="inline-flex h-11 w-11 items-center justify-center rounded-md bg-brand-forest-700 text-brand-forest-foreground shadow-brand transition-all hover:bg-brand-forest-800 sm:h-auto sm:w-auto sm:gap-2 sm:px-6 sm:py-3"
            >
              <span className="hidden text-sm font-semibold sm:inline">Start 14-day free trial</span>
              <ArrowRight className="h-4 w-4" />
            </Link>
            <a
              href="#platform"
              className="inline-flex items-center justify-center gap-2 rounded-md border border-border bg-background px-6 py-3 text-sm font-semibold text-foreground transition-all hover:border-foreground/40 hover:bg-muted/50"
            >
              See the platform
            </a>
          </div>

          <ul className="mt-6 flex flex-wrap items-center justify-center gap-x-5 gap-y-2 text-sm text-muted-foreground lg:justify-start">
            {[
              'No credit card required',
              '14-day free trial',
              'UK GDPR-ready',
              'UK data residency',
            ].map((t) => (
              <li key={t} className="inline-flex items-center gap-2">
                <CheckCircle2 className="h-4 w-4 text-brand-forest-700" />
                {t}
              </li>
            ))}
          </ul>
        </div>

        <div className="flex min-h-0 lg:col-span-7 xl:col-span-7">
          <HeroProductDemo size="large" className="h-full w-full" />
        </div>
      </div>
    </section>
  )
}
