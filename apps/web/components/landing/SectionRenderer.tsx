'use client'

import type { LandingSection } from '@/lib/api-client'

interface Props {
  section: LandingSection
  primaryColor?: string
}

/**
 * Renders a single landing-page section from the typed JSON schema.
 *
 * Designed to be safe with partial / AI-generated data: every prop is
 * defensively coerced to its expected shape and unknown section types
 * fall back to a `rich_text` block.
 */
export function SectionRenderer({ section, primaryColor = '#2563EB' }: Props) {
  const p = section.props || {}
  switch (section.type) {
    case 'hero':
      return <HeroSection props={p} primary={primaryColor} />
    case 'features':
      return <FeaturesSection props={p} />
    case 'testimonials':
      return <TestimonialsSection props={p} />
    case 'trust_badges':
      return <TrustBadgesSection props={p} />
    case 'faq':
      return <FaqSection props={p} />
    case 'gallery':
      return <GallerySection props={p} />
    case 'cta':
      return <CtaSection props={p} primary={primaryColor} />
    case 'pricing':
      return <PricingSection props={p} primary={primaryColor} />
    case 'lead_form':
      return <LeadFormSection props={p} primary={primaryColor} />
    case 'rich_text':
      return <RichTextSection props={p} />
    default:
      return (
        <section className="py-12 px-6 max-w-3xl mx-auto text-gray-500 text-sm">
          (Unknown section type: <code>{section.type}</code>)
        </section>
      )
  }
}

function asString(v: unknown, fallback = ''): string {
  return typeof v === 'string' ? v : fallback
}
function asArr<T = Record<string, unknown>>(v: unknown): T[] {
  return Array.isArray(v) ? (v as T[]) : []
}

function HeroSection({ props, primary }: { props: Record<string, unknown>; primary: string }) {
  return (
    <section className="bg-gradient-to-br from-slate-50 to-white py-20 px-6">
      <div className="max-w-4xl mx-auto text-center">
        {asString(props.eyebrow) && (
          <p
            className="text-sm font-semibold uppercase tracking-wide mb-3"
            style={{ color: primary }}
          >
            {asString(props.eyebrow)}
          </p>
        )}
        <h1 className="text-4xl sm:text-5xl font-bold tracking-tight mb-4">
          {asString(props.headline, 'Welcome')}
        </h1>
        <p className="text-lg text-gray-600 mb-8 max-w-2xl mx-auto">
          {asString(props.subheadline)}
        </p>
        <div className="flex items-center justify-center gap-3">
          <a
            href="#enquiry"
            className="rounded-lg px-6 py-3 text-white font-semibold shadow-md hover:opacity-90"
            style={{ backgroundColor: primary }}
          >
            {asString(props.primary_cta_text, 'Get a quote')}
          </a>
          {asString(props.secondary_cta_text) && (
            <a
              href="#features"
              className="rounded-lg px-6 py-3 border border-gray-300 font-semibold hover:bg-gray-50"
            >
              {asString(props.secondary_cta_text)}
            </a>
          )}
        </div>
      </div>
    </section>
  )
}

function FeaturesSection({ props }: { props: Record<string, unknown> }) {
  const items = asArr(props.items)
  return (
    <section id="features" className="py-16 px-6">
      <div className="max-w-5xl mx-auto">
        <h2 className="text-2xl sm:text-3xl font-bold text-center mb-10">
          {asString(props.title, 'What we offer')}
        </h2>
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {items.map((it, i) => (
            <article key={i} className="rounded-xl border bg-white p-6">
              <h3 className="font-semibold text-lg mb-2">{asString(it.title)}</h3>
              <p className="text-sm text-gray-600 leading-relaxed">
                {asString(it.description)}
              </p>
            </article>
          ))}
        </div>
      </div>
    </section>
  )
}

function TestimonialsSection({ props }: { props: Record<string, unknown> }) {
  const items = asArr(props.items)
  return (
    <section className="bg-slate-50 py-16 px-6">
      <div className="max-w-4xl mx-auto">
        {asString(props.title) && (
          <h2 className="text-2xl sm:text-3xl font-bold text-center mb-10">
            {asString(props.title)}
          </h2>
        )}
        <div className="grid sm:grid-cols-2 gap-6">
          {items.map((it, i) => (
            <blockquote key={i} className="rounded-xl bg-white p-6 shadow-sm">
              <p className="text-sm text-gray-700 italic mb-3">"{asString(it.quote)}"</p>
              <footer className="text-sm font-medium">
                {asString(it.author)}
                {asString(it.role) && (
                  <span className="text-gray-500 font-normal"> · {asString(it.role)}</span>
                )}
              </footer>
            </blockquote>
          ))}
        </div>
      </div>
    </section>
  )
}

function TrustBadgesSection({ props }: { props: Record<string, unknown> }) {
  const items = asArr(props.items)
  return (
    <section className="py-12 px-6 border-y bg-white">
      <div className="max-w-5xl mx-auto text-center">
        {asString(props.title) && (
          <p className="text-xs font-semibold uppercase tracking-widest text-gray-500 mb-6">
            {asString(props.title)}
          </p>
        )}
        <div className="flex flex-wrap items-center justify-center gap-x-8 gap-y-3 text-sm font-medium text-gray-600">
          {items.map((it, i) => (
            <span key={i} className="rounded-full bg-gray-100 px-3 py-1">
              {asString(it.label)}
            </span>
          ))}
        </div>
      </div>
    </section>
  )
}

function FaqSection({ props }: { props: Record<string, unknown> }) {
  const items = asArr(props.items)
  return (
    <section className="py-16 px-6">
      <div className="max-w-3xl mx-auto">
        <h2 className="text-2xl sm:text-3xl font-bold text-center mb-10">
          {asString(props.title, 'Frequently asked')}
        </h2>
        <dl className="space-y-3">
          {items.map((it, i) => (
            <details key={i} className="rounded-lg border bg-white p-4 group">
              <summary className="font-semibold cursor-pointer text-sm flex items-center justify-between">
                {asString(it.question)}
                <span className="text-gray-400 group-open:rotate-180 transition-transform">▾</span>
              </summary>
              <p className="text-sm text-gray-600 mt-3 leading-relaxed">
                {asString(it.answer)}
              </p>
            </details>
          ))}
        </dl>
      </div>
    </section>
  )
}

function GallerySection({ props }: { props: Record<string, unknown> }) {
  const briefs = asArr<string>(props.image_briefs).map((b) => (typeof b === 'string' ? b : ''))
  return (
    <section className="py-12 px-6">
      <div className="max-w-5xl mx-auto">
        {asString(props.title) && (
          <h2 className="text-2xl font-bold mb-6">{asString(props.title)}</h2>
        )}
        <div className="grid sm:grid-cols-3 gap-4">
          {briefs.map((b, i) => (
            <div
              key={i}
              className="aspect-square rounded-lg bg-gradient-to-br from-gray-100 to-gray-200 flex items-center justify-center text-xs text-gray-500 p-4 text-center"
            >
              {b || `Image ${i + 1}`}
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}

function CtaSection({ props, primary }: { props: Record<string, unknown>; primary: string }) {
  return (
    <section className="py-16 px-6" style={{ backgroundColor: primary }}>
      <div className="max-w-3xl mx-auto text-center text-white">
        <h2 className="text-3xl font-bold mb-3">{asString(props.headline, 'Ready to start?')}</h2>
        <p className="text-white/90 mb-6">{asString(props.subheadline)}</p>
        <a
          href="#enquiry"
          className="inline-block rounded-lg bg-white text-gray-900 font-semibold px-6 py-3 shadow-md hover:bg-gray-100"
        >
          {asString(props.primary_cta_text, 'Get in touch')}
        </a>
      </div>
    </section>
  )
}

function PricingSection({ props, primary }: { props: Record<string, unknown>; primary: string }) {
  const plans = asArr(props.plans)
  return (
    <section className="py-16 px-6 bg-slate-50">
      <div className="max-w-5xl mx-auto">
        <h2 className="text-2xl sm:text-3xl font-bold text-center mb-10">
          {asString(props.title, 'Pricing')}
        </h2>
        <div className="grid sm:grid-cols-3 gap-6">
          {plans.map((plan, i) => {
            const featured = Boolean(plan.featured)
            return (
              <div
                key={i}
                className={`rounded-xl p-6 ${
                  featured ? 'text-white shadow-xl scale-[1.02]' : 'bg-white border'
                }`}
                style={featured ? { backgroundColor: primary } : undefined}
              >
                <h3 className="font-semibold text-lg">{asString(plan.name)}</h3>
                <p className="text-3xl font-bold my-3">{asString(plan.price_text)}</p>
                <ul className="space-y-1.5 text-sm mb-6">
                  {asArr<string>(plan.features).map((f, j) => (
                    <li key={j}>{typeof f === 'string' ? f : ''}</li>
                  ))}
                </ul>
                <a
                  href="#enquiry"
                  className={`block text-center rounded-lg py-2.5 font-semibold ${
                    featured ? 'bg-white text-gray-900' : 'border'
                  }`}
                  style={!featured ? { color: primary, borderColor: primary } : undefined}
                >
                  {asString(plan.cta_text, 'Choose plan')}
                </a>
              </div>
            )
          })}
        </div>
      </div>
    </section>
  )
}

function LeadFormSection({ props, primary }: { props: Record<string, unknown>; primary: string }) {
  const fields = asArr(props.fields)
  return (
    <section id="enquiry" className="py-16 px-6">
      <div className="max-w-xl mx-auto">
        <h2 className="text-2xl sm:text-3xl font-bold text-center mb-2">
          {asString(props.title, 'Get a free quote')}
        </h2>
        {asString(props.subheadline) && (
          <p className="text-center text-gray-600 mb-6">{asString(props.subheadline)}</p>
        )}
        <form className="space-y-3 rounded-xl border bg-white p-6 shadow-sm">
          {fields.map((f, i) => {
            const type = asString(f.type, 'text')
            const name = asString(f.name)
            return (
              <div key={i}>
                <label className="text-xs font-medium text-gray-700 uppercase tracking-wide">
                  {asString(f.label)}{f.required ? ' *' : ''}
                </label>
                {type === 'textarea' ? (
                  <textarea
                    name={name}
                    required={!!f.required}
                    rows={4}
                    className="mt-1 w-full rounded-md border px-3 py-2 text-sm"
                  />
                ) : (
                  <input
                    name={name}
                    type={type}
                    required={!!f.required}
                    className="mt-1 w-full rounded-md border px-3 py-2 text-sm"
                  />
                )}
              </div>
            )
          })}
          <button
            type="submit"
            className="w-full rounded-lg py-3 text-white font-semibold"
            style={{ backgroundColor: primary }}
          >
            {asString(props.submit_text, 'Send enquiry')}
          </button>
        </form>
      </div>
    </section>
  )
}

function RichTextSection({ props }: { props: Record<string, unknown> }) {
  return (
    <section className="py-12 px-6">
      <div className="max-w-3xl mx-auto prose prose-sm sm:prose">
        <p>{asString(props.markdown)}</p>
      </div>
    </section>
  )
}
