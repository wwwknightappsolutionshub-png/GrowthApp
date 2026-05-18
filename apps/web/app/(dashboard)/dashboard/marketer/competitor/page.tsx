'use client'

import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { ExternalLink, Radar, Sparkles } from 'lucide-react'
import { marketer } from '@/lib/api-client'
import { toast } from 'sonner'

interface CompetitorResult {
  competitor_name: string
  website: string | null
  strengths: string[]
  weaknesses: string[]
  pricing: {
    samples?: string[]
    positioning_gaps?: string[]
    fetch_error?: string | null
    page_title?: string | null
  }
}

export default function CompetitorPage() {
  const [name, setName] = useState('')
  const [website, setWebsite] = useState('')
  const [result, setResult] = useState<CompetitorResult | null>(null)

  const scanMut = useMutation({
    mutationFn: () =>
      marketer.scanCompetitor({
        competitor_name: name || undefined,
        website: website || undefined,
      }),
    onSuccess: (res) => {
      if (!res.data?.ok) {
        toast.error(res.data?.error || 'Failed to scan competitor')
        return
      }
      setResult({
        competitor_name: res.data.competitor_name,
        website: res.data.website,
        strengths: res.data.strengths,
        weaknesses: res.data.weaknesses,
        pricing: res.data.pricing || {},
      })
      toast.success('Competitor scan complete')
    },
    onError: () => toast.error('Failed to scan competitor'),
  })

  return (
    <div className="space-y-6 max-w-5xl">
      <div>
        <h1 className="text-2xl font-bold text-foreground flex items-center gap-2">
          <Radar className="h-6 w-6 text-primary" /> Competitor Intelligence
        </h1>
        <p className="text-sm text-muted-foreground mt-1">
          Drop in a competitor's website and we'll extract their strengths, weaknesses, visible
          pricing, and positioning gaps.
        </p>
      </div>

      <div className="bg-card border border-border rounded-xl p-6 grid grid-cols-1 md:grid-cols-2 gap-3">
        <div>
          <label className="block text-sm font-medium mb-1">Competitor name</label>
          <input
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="Acme Plumbing"
            className="w-full rounded-lg bg-background border border-border px-3 py-2 text-sm"
          />
        </div>
        <div>
          <label className="block text-sm font-medium mb-1">Website</label>
          <input
            value={website}
            onChange={(e) => setWebsite(e.target.value)}
            placeholder="https://acmeplumbing.co.uk"
            className="w-full rounded-lg bg-background border border-border px-3 py-2 text-sm"
          />
        </div>
        <div className="md:col-span-2">
          <button
            onClick={() => scanMut.mutate()}
            disabled={scanMut.isPending}
            className="flex items-center gap-2 rounded-lg bg-primary px-5 py-3 text-sm font-semibold text-primary-foreground hover:bg-primary/90 disabled:opacity-60"
          >
            <Sparkles className="h-4 w-4" />
            {scanMut.isPending ? 'Scanning…' : 'Run competitor scan'}
          </button>
        </div>
      </div>

      {result && (
        <div className="bg-card border border-border rounded-xl p-6 space-y-5">
          <div>
            <h2 className="text-xl font-bold text-foreground">{result.competitor_name}</h2>
            {result.website && (
              <a
                href={result.website.startsWith('http') ? result.website : `https://${result.website}`}
                target="_blank"
                rel="noreferrer"
                className="inline-flex items-center gap-1 text-xs text-primary mt-1 hover:underline"
              >
                {result.website} <ExternalLink className="h-3 w-3" />
              </a>
            )}
            {result.pricing.fetch_error && (
              <div className="mt-2 text-xs rounded bg-red-50 border border-red-200 px-2 py-1 text-red-700">
                Fetch error: {result.pricing.fetch_error}
              </div>
            )}
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <Card title="Strengths" color="text-green-600" items={result.strengths} />
            <Card title="Weaknesses" color="text-red-600" items={result.weaknesses} />
            <Card
              title="Pricing samples"
              color="text-amber-600"
              items={result.pricing.samples || []}
            />
            <Card
              title="Positioning gaps"
              color="text-blue-600"
              items={result.pricing.positioning_gaps || []}
            />
          </div>
        </div>
      )}
    </div>
  )
}

function Card({
  title,
  color,
  items,
}: {
  title: string
  color: string
  items: string[]
}) {
  return (
    <div className="bg-muted/30 border border-border rounded-xl p-4">
      <div className={`text-xs font-semibold uppercase tracking-wider mb-2 ${color}`}>
        {title}
      </div>
      {items.length === 0 ? (
        <div className="text-xs text-muted-foreground">—</div>
      ) : (
        <ul className="space-y-1 text-sm">
          {items.map((s, i) => (
            <li key={i} className="text-foreground">
              • {s}
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
