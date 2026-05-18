'use client'

import { useEffect, useMemo, useState } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import { useMutation } from '@tanstack/react-query'
import { ArrowLeft, ArrowRight, Loader2, Sparkles } from 'lucide-react'
import { toast } from 'sonner'
import {
  landingPages,
  marketingTemplates,
  type LandingSection,
} from '@/lib/api-client'
import { SectionRenderer } from '@/components/landing/SectionRenderer'

const ALL_SECTIONS = [
  'hero',
  'features',
  'testimonials',
  'trust_badges',
  'faq',
  'gallery',
  'cta',
  'pricing',
  'lead_form',
]

type GenerateResponse = {
  page_id: string | null
  slug: string
  title: string
  meta_description: string
  sections: LandingSection[]
  provider: string
  model: string
}

interface TemplateSummary {
  id: string
  slug: string
  name: string
  niche: string
  description: string | null
  preview_image_url: string | null
}

const NICHE_LABEL: Record<string, string> = {
  trades: 'Trades & Services',
  hospitality: 'Hospitality',
  beauty: 'Beauty & Wellness',
  healthcare: 'Healthcare',
  real_estate: 'Real Estate',
  generic: 'Generic / SaaS',
}

export default function NewLandingPage() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const [mode, setMode] = useState<'template' | 'ai'>('template')
  const [summary, setSummary] = useState('')
  const [offer, setOffer] = useState('')
  const [audience, setAudience] = useState('')
  const [tone, setTone] = useState('confident, friendly, professional')
  const [cta, setCta] = useState('Get a free quote')
  const [include, setInclude] = useState<string[]>([
    'hero',
    'features',
    'testimonials',
    'faq',
    'cta',
    'lead_form',
  ])
  const [preview, setPreview] = useState<GenerateResponse | null>(null)

  // Template chooser ------------------------------------------------------
  const [templates, setTemplates] = useState<TemplateSummary[]>([])
  const [templatesLoading, setTemplatesLoading] = useState(true)
  const [activeNiche, setActiveNiche] = useState<string>('all')
  const [applyingSlug, setApplyingSlug] = useState<string | null>(null)

  useEffect(() => {
    marketingTemplates
      .list()
      .then((res) => setTemplates(res.data as TemplateSummary[]))
      .catch(() => toast.error('Could not load page templates'))
      .finally(() => setTemplatesLoading(false))
  }, [])

  // If the user landed with ?template=... auto-scroll to template mode.
  useEffect(() => {
    const slug = searchParams.get('template')
    if (slug) setMode('template')
  }, [searchParams])

  const niches = useMemo(() => {
    const set = new Set(templates.map((t) => t.niche))
    return Array.from(set).sort()
  }, [templates])

  const filteredTemplates =
    activeNiche === 'all'
      ? templates
      : templates.filter((t) => t.niche === activeNiche)

  async function applyTemplate(t: TemplateSummary) {
    setApplyingSlug(t.slug)
    try {
      const res = await marketingTemplates.apply({
        template_slug: t.slug,
        page_title: t.name,
      })
      const payload = res.data as { id: string; redirect_to?: string }
      toast.success(`Template "${t.name}" applied — opening editor`)
      router.push(payload.redirect_to || `/dashboard/landing-pages/${payload.id}`)
    } catch (err) {
      const e = err as { response?: { data?: { detail?: string } } }
      toast.error(e.response?.data?.detail || 'Could not apply template')
    } finally {
      setApplyingSlug(null)
    }
  }

  const generate = useMutation<{ data: GenerateResponse }, Error>({
    mutationFn: () =>
      landingPages.generate({
        business_summary: summary,
        primary_offer: offer,
        target_audience: audience,
        tone,
        cta_text: cta,
        include_sections: include,
        save: false,
      }),
    onSuccess: (res) => setPreview(res.data),
  })

  const saveAndOpen = useMutation<{ data: GenerateResponse }, Error>({
    mutationFn: () =>
      landingPages.generate({
        business_summary: summary,
        primary_offer: offer,
        target_audience: audience,
        tone,
        cta_text: cta,
        include_sections: include,
        save: true,
      }),
    onSuccess: (res) => {
      if (res.data.page_id) {
        router.push(`/dashboard/landing-pages/${res.data.page_id}`)
      }
    },
  })

  const toggleSection = (s: string) =>
    setInclude((curr) => (curr.includes(s) ? curr.filter((x) => x !== s) : [...curr, s]))

  return (
    <div className="space-y-6">
      <button
        onClick={() => router.back()}
        className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground"
      >
        <ArrowLeft className="w-4 h-4" /> Back to landing pages
      </button>

      {/* Mode switch ────────────────────────────────────────────────── */}
      <div className="inline-flex items-center gap-1 rounded-lg border bg-gray-50 p-1">
        <button
          type="button"
          onClick={() => setMode('template')}
          className={`rounded-md px-4 py-1.5 text-sm font-semibold transition-colors ${
            mode === 'template' ? 'bg-white text-foreground shadow' : 'text-muted-foreground hover:text-foreground'
          }`}
        >
          Pick a template
        </button>
        <button
          type="button"
          onClick={() => setMode('ai')}
          className={`inline-flex items-center gap-1.5 rounded-md px-4 py-1.5 text-sm font-semibold transition-colors ${
            mode === 'ai' ? 'bg-white text-foreground shadow' : 'text-muted-foreground hover:text-foreground'
          }`}
        >
          <Sparkles className="h-3.5 w-3.5" /> Generate with AI
        </button>
      </div>

      {mode === 'template' && (
        <section className="rounded-xl border bg-card p-6">
          <header className="mb-5 flex flex-wrap items-end justify-between gap-3">
            <div>
              <h2 className="text-base font-semibold text-foreground">
                Niche-specific starter templates
              </h2>
              <p className="mt-1 text-sm text-muted-foreground">
                Pick a polished page built for your industry. You can fully edit
                every section after applying.
              </p>
            </div>
            <div className="flex flex-wrap gap-1.5 rounded-md border bg-gray-50 p-1">
              <button
                type="button"
                onClick={() => setActiveNiche('all')}
                className={`rounded-md px-3 py-1 text-xs font-semibold transition-colors ${
                  activeNiche === 'all'
                    ? 'bg-white text-foreground shadow-sm'
                    : 'text-muted-foreground hover:text-foreground'
                }`}
              >
                All ({templates.length})
              </button>
              {niches.map((n) => (
                <button
                  type="button"
                  key={n}
                  onClick={() => setActiveNiche(n)}
                  className={`rounded-md px-3 py-1 text-xs font-semibold transition-colors ${
                    activeNiche === n
                      ? 'bg-white text-foreground shadow-sm'
                      : 'text-muted-foreground hover:text-foreground'
                  }`}
                >
                  {NICHE_LABEL[n] || n}
                </button>
              ))}
            </div>
          </header>

          {templatesLoading ? (
            <p className="text-sm text-gray-400">Loading templates…</p>
          ) : filteredTemplates.length === 0 ? (
            <p className="rounded-lg border border-dashed bg-gray-50 p-10 text-center text-sm text-muted-foreground">
              No templates in this niche yet.
            </p>
          ) : (
            <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
              {filteredTemplates.map((t) => (
                <article
                  key={t.id}
                  className="group flex flex-col rounded-lg border bg-card p-5 transition-all hover:border-brand-forest-300 hover:shadow-sm"
                >
                  <div className="mb-2 flex items-center justify-between">
                    <span className="inline-flex items-center rounded-full bg-brand-forest-50 px-2 py-0.5 font-mono text-[10px] font-bold uppercase tracking-wider text-brand-forest-700">
                      {NICHE_LABEL[t.niche] || t.niche}
                    </span>
                    <Sparkles className="h-3.5 w-3.5 text-brand-teal-500" />
                  </div>
                  <h3 className="text-sm font-semibold text-foreground">{t.name}</h3>
                  <p className="mt-1.5 line-clamp-3 flex-1 text-xs leading-relaxed text-muted-foreground">
                    {t.description}
                  </p>
                  <button
                    type="button"
                    disabled={applyingSlug !== null}
                    onClick={() => applyTemplate(t)}
                    className="mt-4 inline-flex items-center justify-center gap-1.5 rounded-md bg-brand-forest-700 px-3 py-2 text-xs font-semibold text-brand-forest-foreground transition-colors hover:bg-brand-forest-800 disabled:opacity-60"
                  >
                    {applyingSlug === t.slug ? (
                      <Loader2 className="h-3.5 w-3.5 animate-spin" />
                    ) : (
                      <ArrowRight className="h-3.5 w-3.5" />
                    )}
                    Use this template
                  </button>
                </article>
              ))}
            </div>
          )}
        </section>
      )}

      {mode === 'ai' && (
      <div className="grid gap-6 lg:grid-cols-[400px_1fr]">
        <section className="rounded-xl border bg-card p-5 space-y-4 h-fit sticky top-4">
          <h2 className="text-sm font-semibold uppercase tracking-wide text-muted-foreground">
            AI Generator
          </h2>

          <Field
            label="Business summary"
            value={summary}
            onChange={setSummary}
            multiline
            rows={3}
            placeholder="One paragraph about your business, services, and what makes you different."
          />
          <Field
            label="Primary offer"
            value={offer}
            onChange={setOffer}
            placeholder="Free no-obligation quote, fixed prices, 12-month warranty"
          />
          <Field
            label="Target audience"
            value={audience}
            onChange={setAudience}
            placeholder="Homeowners aged 35-65 in Greater Manchester"
          />
          <Field label="Tone of voice" value={tone} onChange={setTone} />
          <Field label="Primary CTA text" value={cta} onChange={setCta} />

          <div>
            <label className="text-xs font-medium text-foreground/80 uppercase tracking-wide">
              Sections to include
            </label>
            <div className="mt-1 flex flex-wrap gap-1.5">
              {ALL_SECTIONS.map((s) => (
                <button
                  key={s}
                  type="button"
                  onClick={() => toggleSection(s)}
                  className={`text-xs px-2.5 py-1 rounded-full border capitalize transition-colors ${
                    include.includes(s)
                      ? 'border-blue-600 bg-blue-50 text-blue-700 font-medium'
                      : 'border-border text-muted-foreground hover:bg-gray-50'
                  }`}
                >
                  {s.replace('_', ' ')}
                </button>
              ))}
            </div>
          </div>

          <div className="flex flex-col gap-2 pt-2">
            <button
              onClick={() => generate.mutate()}
              disabled={generate.isPending || !summary.trim() || !offer.trim()}
              className="w-full inline-flex items-center justify-center gap-2 rounded-lg border bg-card px-4 py-2.5 text-sm font-medium text-foreground/80 hover:bg-gray-50 disabled:opacity-50"
            >
              {generate.isPending ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Sparkles className="w-4 h-4" />
              )}
              Preview
            </button>
            <button
              onClick={() => saveAndOpen.mutate()}
              disabled={saveAndOpen.isPending || !summary.trim() || !offer.trim()}
              className="w-full inline-flex items-center justify-center gap-2 rounded-lg bg-blue-600 px-4 py-2.5 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
            >
              {saveAndOpen.isPending && <Loader2 className="w-4 h-4 animate-spin" />}
              Generate & save as draft
            </button>
          </div>

          {(generate.error || saveAndOpen.error) && (
            <p className="text-xs text-red-600">
              {(generate.error || saveAndOpen.error)?.message || 'Generation failed'}
            </p>
          )}
        </section>

        <section className="rounded-xl border bg-card overflow-hidden">
          {preview ? (
            <div>
              <header className="border-b px-5 py-3 bg-gray-50 text-xs text-muted-foreground flex items-center justify-between">
                <span>
                  <strong>{preview.title}</strong> · {preview.sections.length} sections ·{' '}
                  {preview.provider}/{preview.model}
                </span>
              </header>
              <div className="max-h-[80vh] overflow-y-auto">
                {preview.sections.map((s, i) => (
                  <SectionRenderer key={i} section={s} />
                ))}
              </div>
            </div>
          ) : (
            <div className="p-12 text-center text-muted-foreground text-sm">
              Configure the brief and click <strong>Preview</strong> to see the AI-generated page.
            </div>
          )}
        </section>
      </div>
      )}
    </div>
  )
}

function Field({
  label,
  value,
  onChange,
  multiline,
  rows,
  placeholder,
}: {
  label: string
  value: string
  onChange: (v: string) => void
  multiline?: boolean
  rows?: number
  placeholder?: string
}) {
  return (
    <div>
      <label className="text-xs font-medium text-foreground/80 uppercase tracking-wide">{label}</label>
      {multiline ? (
        <textarea
          value={value}
          onChange={(e) => onChange(e.target.value)}
          rows={rows || 3}
          placeholder={placeholder}
          className="mt-1 w-full rounded-md border px-3 py-2 text-sm"
        />
      ) : (
        <input
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder={placeholder}
          className="mt-1 w-full rounded-md border px-3 py-2 text-sm"
        />
      )}
    </div>
  )
}
