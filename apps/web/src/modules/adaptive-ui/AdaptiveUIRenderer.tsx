'use client'

import Link from 'next/link'
import { ArrowRight, CheckCircle2, Sparkles } from 'lucide-react'
import type { AdaptiveUIResult } from './useAdaptiveUI'

type RendererMode = 'hero' | 'visual' | 'sections'

export function AdaptiveUIRenderer({
  adaptive,
  mode,
  fallback = null,
}: {
  adaptive: AdaptiveUIResult
  mode: RendererMode
  fallback?: React.ReactNode
}) {
  if (!adaptive) return <>{fallback}</>

  if (mode === 'hero') {
    return (
      <>
        {adaptive.hero && <HeroOverride adaptive={adaptive} />}
      </>
    )
  }

  if (mode === 'visual') {
    return (
      <>
        {adaptive.imageSet && <ImageSetOverride adaptive={adaptive} />}
      </>
    )
  }

  return (
    <>
      {(adaptive.painPointBlocks.length > 0 || adaptive.goalBlock || adaptive.testimonialBlock.length > 0) && (
        <AdaptiveSections adaptive={adaptive} />
      )}
    </>
  )
}

function HeroOverride({ adaptive }: { adaptive: NonNullable<AdaptiveUIResult> }) {
  return (
    <>
      <span className="inline-flex items-center gap-2 rounded-full border border-brand-teal-400/30 bg-brand-teal-400/10 px-3 py-1 text-[11px] font-medium uppercase tracking-[0.16em] text-brand-teal-600">
        <Sparkles className="h-3 w-3" />
        {adaptive.hero.eyebrow}
      </span>

      <h1 className="mt-6 font-display text-4xl font-bold leading-[1.05] tracking-tight text-foreground sm:text-5xl xl:text-[64px] xl:leading-[1.04]">
        {adaptive.hero.headline}
      </h1>

      <p className="mx-auto mt-6 max-w-2xl text-lg leading-relaxed text-muted-foreground lg:mx-0">
        {adaptive.hero.subheadline}
      </p>

      <div className="mt-9 flex flex-col justify-center gap-3 sm:flex-row lg:justify-start">
        <Link
          href={adaptive.cta.href}
          className="inline-flex items-center justify-center gap-2 rounded-md bg-brand-forest-700 px-6 py-3.5 text-sm font-semibold text-brand-forest-foreground shadow-brand transition-all hover:bg-brand-forest-800"
        >
          {adaptive.hero.primaryCta}
          <ArrowRight className="h-4 w-4" />
        </Link>
        <a
          href="#adaptive-demo"
          className="inline-flex items-center justify-center gap-2 rounded-md border border-border bg-background px-6 py-3.5 text-sm font-semibold text-foreground transition-all hover:border-foreground/40 hover:bg-muted/50"
        >
          {adaptive.hero.secondaryCta}
        </a>
      </div>

      <ul className="mt-10 flex flex-wrap items-center justify-center gap-x-7 gap-y-3 text-sm text-muted-foreground lg:justify-start">
        {adaptive.painPointBlocks.map((painPoint) => (
          <li key={painPoint.id} className="inline-flex items-center gap-2">
            <CheckCircle2 className="h-4 w-4 text-brand-forest-700" />
            {painPoint.label}
          </li>
        ))}
      </ul>
    </>
  )
}

function ImageSetOverride({ adaptive }: { adaptive: NonNullable<AdaptiveUIResult> }) {
  return (
    <div className="overflow-hidden rounded-2xl border border-border bg-card shadow-elevated">
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img
        src={adaptive.imageSet.hero}
        alt={adaptive.imageSet.heroAlt}
        className="h-72 w-full object-cover sm:h-96"
      />
      <div className="border-t border-border bg-brand-forest-950 p-5 text-brand-forest-foreground">
        <p className="text-xs font-semibold uppercase tracking-widest text-brand-teal-300">
          Personalized demo view
        </p>
        <p className="mt-2 text-sm text-white/75">
          Homepage copy, images and proof points are now focused on {adaptive.nicheName.toLowerCase()}.
        </p>
      </div>
    </div>
  )
}

function AdaptiveSections({ adaptive }: { adaptive: NonNullable<AdaptiveUIResult> }) {
  return (
    <section id="adaptive-demo" className="border-b border-border bg-brand-forest-950 py-20 text-brand-forest-foreground">
      <div className="container space-y-12">
        <div className="max-w-3xl">
          <span className="inline-flex items-center gap-2 rounded-full border border-brand-teal-400/30 bg-brand-teal-400/10 px-3 py-1 text-[11px] font-medium uppercase tracking-[0.16em] text-brand-teal-300">
            <Sparkles className="h-3 w-3" />
            Customized demo for {adaptive.nicheName}
          </span>
          <h2 className="mt-6 font-display text-3xl font-bold leading-tight text-white sm:text-4xl">
            Why CustomerFlow fits your workflow
          </h2>
          <p className="mt-4 text-base leading-relaxed text-white/70">
            These blocks are layered onto the existing homepage so you can experience the platform through your niche.
          </p>
        </div>

        {adaptive.painPointBlocks.length > 0 && (
          <div className="grid gap-4 md:grid-cols-3">
            {adaptive.painPointBlocks.map((painPoint) => (
              <article key={painPoint.id} className="rounded-xl border border-white/10 bg-white/5 p-6">
                <p className="text-sm font-semibold text-brand-teal-300">{painPoint.label}</p>
                <p className="mt-3 text-sm leading-relaxed text-white/70">{painPoint.description}</p>
              </article>
            ))}
          </div>
        )}

        <div className="grid gap-5 lg:grid-cols-[1.2fr_0.8fr]">
          {adaptive.goalBlock && (
            <article className="rounded-xl border border-brand-teal-400/20 bg-brand-teal-400/10 p-7">
              <p className="text-xs font-semibold uppercase tracking-widest text-brand-teal-300">
                Main goal
              </p>
              <h3 className="mt-3 font-display text-2xl font-bold text-white">
                {adaptive.goalBlock.title}
              </h3>
              <p className="mt-3 text-sm leading-relaxed text-white/70">{adaptive.goalBlock.body}</p>
            </article>
          )}

          {adaptive.whyBlock && (
            <article className="rounded-xl border border-white/10 bg-white/5 p-7">
              <p className="text-xs font-semibold uppercase tracking-widest text-brand-teal-300">
                Why CustomerFlow solves your pain
              </p>
              <h3 className="mt-3 font-display text-2xl font-bold text-white">
                {adaptive.whyBlock.title}
              </h3>
              <p className="mt-3 text-sm leading-relaxed text-white/70">{adaptive.whyBlock.body}</p>
            </article>
          )}
        </div>

        {adaptive.testimonialBlock.length > 0 && (
          <div className="grid gap-4 md:grid-cols-2">
            {adaptive.testimonialBlock.map((testimonial) => (
              <blockquote key={`${testimonial.name}-${testimonial.role}`} className="rounded-xl border border-white/10 bg-white/5 p-6">
                <p className="text-sm leading-relaxed text-white/80">"{testimonial.quote}"</p>
                <footer className="mt-4 text-xs text-brand-teal-300">
                  {testimonial.name} · {testimonial.role}
                </footer>
              </blockquote>
            ))}
          </div>
        )}

        {adaptive.cta && (
          <div className="flex flex-wrap items-center justify-between gap-4 rounded-xl border border-brand-teal-400/20 bg-brand-teal-400/10 p-6">
            <div>
              <p className="font-display text-xl font-bold text-white">{adaptive.cta.text}</p>
              <p className="mt-1 text-sm text-white/65">
                Continue with this personalized view or start a real workspace.
              </p>
            </div>
            <Link
              href={adaptive.cta.href}
              className="inline-flex items-center gap-2 rounded-md bg-brand-teal-400 px-5 py-3 text-sm font-bold text-brand-teal-foreground shadow-brand hover:bg-brand-teal-300"
            >
              Start free trial
              <ArrowRight className="h-4 w-4" />
            </Link>
          </div>
        )}
      </div>
    </section>
  )
}
