'use client'

import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { Sparkles, Users } from 'lucide-react'
import { marketer } from '@/lib/api-client'
import { toast } from 'sonner'

interface AudienceResult {
  industry: string | null
  demographics: Record<string, string>
  pain_points: string[]
  opportunities: string[]
}

const SUGGESTED = ['plumbing', 'electrical', 'cleaning', 'roofing', 'beauty', 'fitness']

export default function AudiencePage() {
  const [industry, setIndustry] = useState('')
  const [result, setResult] = useState<AudienceResult | null>(null)

  const genMut = useMutation({
    mutationFn: () => marketer.generateAudience({ industry: industry || undefined }),
    onSuccess: (res) => {
      if (!res.data?.ok) {
        toast.error(res.data?.error || 'Failed to generate research')
        return
      }
      setResult({
        industry: res.data.industry,
        demographics: res.data.demographics,
        pain_points: res.data.pain_points,
        opportunities: res.data.opportunities,
      })
      toast.success('Audience research generated')
    },
    onError: () => toast.error('Failed to generate research'),
  })

  return (
    <div className="space-y-6 max-w-5xl">
      <div>
        <h1 className="text-2xl font-bold text-foreground flex items-center gap-2">
          <Users className="h-6 w-6 text-primary" /> Audience Research
        </h1>
        <p className="text-sm text-muted-foreground mt-1">
          Get a snapshot of who your customers are, what hurts them, and where the
          opportunities are.
        </p>
      </div>

      <div className="bg-card border border-border rounded-xl p-6 space-y-4">
        <div>
          <label className="block text-sm font-medium mb-1">Industry</label>
          <input
            value={industry}
            onChange={(e) => setIndustry(e.target.value)}
            placeholder="e.g. plumbing, electrical, cleaning"
            className="w-full max-w-sm rounded-lg bg-background border border-border px-3 py-2 text-sm"
          />
          <div className="mt-2 flex flex-wrap gap-2">
            {SUGGESTED.map((s) => (
              <button
                key={s}
                onClick={() => setIndustry(s)}
                className="px-2.5 py-1 rounded-md bg-muted text-xs text-muted-foreground hover:text-foreground"
              >
                {s}
              </button>
            ))}
          </div>
        </div>
        <button
          onClick={() => genMut.mutate()}
          disabled={genMut.isPending}
          className="flex items-center gap-2 rounded-lg bg-primary px-5 py-3 text-sm font-semibold text-primary-foreground hover:bg-primary/90 disabled:opacity-60"
        >
          <Sparkles className="h-4 w-4" />
          {genMut.isPending ? 'Generating…' : 'Generate research'}
        </button>
      </div>

      {result && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          <section className="bg-card border border-border rounded-xl p-5">
            <h2 className="text-sm font-semibold text-foreground mb-3">Demographics</h2>
            <dl className="space-y-2 text-sm">
              {Object.entries(result.demographics).map(([k, v]) => (
                <div key={k} className="flex justify-between gap-3">
                  <dt className="text-muted-foreground capitalize">{k.replace(/_/g, ' ')}</dt>
                  <dd className="font-medium text-foreground text-right">{v}</dd>
                </div>
              ))}
            </dl>
          </section>

          <section className="bg-card border border-border rounded-xl p-5">
            <h2 className="text-sm font-semibold text-foreground mb-3">Pain points</h2>
            <ul className="space-y-1.5 text-sm">
              {result.pain_points.map((p, i) => (
                <li key={i} className="flex gap-2">
                  <span className="text-red-500">•</span>
                  <span className="text-foreground">{p}</span>
                </li>
              ))}
            </ul>
          </section>

          <section className="bg-card border border-border rounded-xl p-5">
            <h2 className="text-sm font-semibold text-foreground mb-3">Opportunities</h2>
            <ul className="space-y-1.5 text-sm">
              {result.opportunities.map((p, i) => (
                <li key={i} className="flex gap-2">
                  <span className="text-green-500">+</span>
                  <span className="text-foreground">{p}</span>
                </li>
              ))}
            </ul>
          </section>
        </div>
      )}
    </div>
  )
}
