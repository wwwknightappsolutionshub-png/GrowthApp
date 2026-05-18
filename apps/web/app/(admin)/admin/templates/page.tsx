'use client'

import Link from 'next/link'
import { useEffect, useMemo, useState } from 'react'
import { ExternalLink, Sparkles } from 'lucide-react'

import { admin } from '@/lib/api-client'

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

const NICHE_TONE: Record<string, string> = {
  trades: 'bg-emerald-500/15 text-emerald-300',
  hospitality: 'bg-orange-500/15 text-orange-300',
  beauty: 'bg-purple-500/15 text-purple-300',
  healthcare: 'bg-sky-500/15 text-sky-300',
  real_estate: 'bg-amber-500/15 text-amber-300',
  generic: 'bg-gray-500/15 text-gray-300',
}

export default function AdminTemplatesPage() {
  const [templates, setTemplates] = useState<TemplateSummary[]>([])
  const [loading, setLoading] = useState(true)
  const [activeNiche, setActiveNiche] = useState<string>('all')

  useEffect(() => {
    admin
      .listLandingTemplates()
      .then((res) => setTemplates(res.data as TemplateSummary[]))
      .finally(() => setLoading(false))
  }, [])

  const groups = useMemo(() => {
    const m = new Map<string, TemplateSummary[]>()
    for (const t of templates) {
      const arr = m.get(t.niche) ?? []
      arr.push(t)
      m.set(t.niche, arr)
    }
    return m
  }, [templates])

  const niches = useMemo(() => Array.from(groups.keys()).sort(), [groups])
  const filtered = activeNiche === 'all' ? templates : groups.get(activeNiche) || []

  return (
    <div>
      <header className="mb-6">
        <h1 className="text-2xl font-bold text-white">Landing-page templates</h1>
        <p className="mt-1 text-sm text-gray-400">
          Pre-built, niche-specific page starters. Tenants can apply any of these
          from the dashboard&rsquo;s &ldquo;New page&rdquo; flow.
        </p>
      </header>

      <div className="mb-5 flex flex-wrap gap-1.5 rounded-md border border-gray-800 bg-gray-900/60 p-1">
        <button
          type="button"
          onClick={() => setActiveNiche('all')}
          className={`rounded-md px-3 py-1.5 text-xs font-semibold transition-colors ${
            activeNiche === 'all'
              ? 'bg-amber-500/15 text-amber-200'
              : 'text-gray-400 hover:text-white'
          }`}
        >
          All ({templates.length})
        </button>
        {niches.map((n) => (
          <button
            type="button"
            key={n}
            onClick={() => setActiveNiche(n)}
            className={`rounded-md px-3 py-1.5 text-xs font-semibold transition-colors ${
              activeNiche === n
                ? 'bg-amber-500/15 text-amber-200'
                : 'text-gray-400 hover:text-white'
            }`}
          >
            {NICHE_LABEL[n] || n} ({groups.get(n)?.length || 0})
          </button>
        ))}
      </div>

      {loading ? (
        <p className="text-sm text-gray-400">Loading…</p>
      ) : filtered.length === 0 ? (
        <p className="rounded-lg border border-dashed border-gray-800 bg-gray-900/40 p-10 text-center text-sm text-gray-500">
          No templates in this niche yet.
        </p>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {filtered.map((t) => (
            <article
              key={t.id}
              className="group flex flex-col rounded-lg border border-gray-800 bg-gray-900/60 p-5 transition-colors hover:border-amber-500/40 hover:bg-gray-900"
            >
              <div className="mb-3 flex items-start justify-between gap-2">
                <span
                  className={`rounded-full px-2 py-0.5 font-mono text-[10px] font-bold uppercase tracking-wider ${
                    NICHE_TONE[t.niche] || 'bg-gray-700/40 text-gray-300'
                  }`}
                >
                  {NICHE_LABEL[t.niche] || t.niche}
                </span>
                <Sparkles className="h-4 w-4 text-amber-400/70" />
              </div>
              <h3 className="text-base font-semibold text-white">{t.name}</h3>
              <p className="mt-1.5 line-clamp-3 text-xs leading-relaxed text-gray-400">
                {t.description}
              </p>
              <div className="mt-4 flex items-center justify-between border-t border-gray-800 pt-3">
                <span className="font-mono text-[10px] text-gray-600">{t.slug}</span>
                <Link
                  href={`/dashboard/landing-pages/new?template=${encodeURIComponent(
                    t.slug,
                  )}`}
                  className="inline-flex items-center gap-1 text-xs font-semibold text-amber-300 hover:text-amber-200"
                >
                  Use template <ExternalLink className="h-3 w-3" />
                </Link>
              </div>
            </article>
          ))}
        </div>
      )}
    </div>
  )
}
