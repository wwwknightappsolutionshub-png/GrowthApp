'use client'

import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { GitBranch, Sparkles } from 'lucide-react'
import { marketer } from '@/lib/api-client'
import { toast } from 'sonner'

interface FunnelStep {
  stage: string
  goal: string
  asset: string
  headline: string
  cta: string
  channel: string
}

interface FunnelResult {
  funnel_type: string
  steps: FunnelStep[]
  ai_notes: string
}

const FUNNEL_TYPES = [
  { id: 'lead_generation', label: 'Lead generation' },
  { id: 'ecommerce', label: 'E-commerce' },
  { id: 'high_ticket', label: 'High-ticket / B2B' },
]

const STAGE_COLORS: Record<string, string> = {
  Landing: 'bg-blue-100 text-blue-700',
  'Lead Magnet': 'bg-purple-100 text-purple-700',
  Nurture: 'bg-amber-100 text-amber-700',
  Offer: 'bg-green-100 text-green-700',
  Upsell: 'bg-pink-100 text-pink-700',
}

export default function FunnelBuilderPage() {
  const [funnelType, setFunnelType] = useState('lead_generation')
  const [result, setResult] = useState<FunnelResult | null>(null)

  const buildMut = useMutation({
    mutationFn: () => marketer.createFunnel({ funnel_type: funnelType }),
    onSuccess: (res) => {
      if (!res.data?.ok) {
        toast.error(res.data?.error || 'Failed to build funnel')
        return
      }
      setResult({
        funnel_type: res.data.funnel_type,
        steps: res.data.steps,
        ai_notes: res.data.ai_notes,
      })
      toast.success('Funnel blueprint generated')
    },
    onError: () => toast.error('Failed to build funnel'),
  })

  return (
    <div className="space-y-6 max-w-5xl">
      <div>
        <h1 className="text-2xl font-bold text-foreground flex items-center gap-2">
          <GitBranch className="h-6 w-6 text-primary" /> Funnel Builder
        </h1>
        <p className="text-sm text-muted-foreground mt-1">
          Generate a 5-stage funnel blueprint — Landing → Lead Magnet → Nurture → Offer → Upsell —
          tailored to your funnel type.
        </p>
      </div>

      <div className="bg-card border border-border rounded-xl p-6 space-y-4">
        <div>
          <label className="block text-sm font-medium mb-2">Funnel type</label>
          <div className="flex flex-wrap gap-2">
            {FUNNEL_TYPES.map((t) => (
              <button
                key={t.id}
                onClick={() => setFunnelType(t.id)}
                className={`px-4 py-2 rounded-lg text-sm font-semibold border ${
                  funnelType === t.id
                    ? 'bg-primary/10 text-primary border-primary/40'
                    : 'bg-card text-muted-foreground border-border hover:border-foreground/30'
                }`}
              >
                {t.label}
              </button>
            ))}
          </div>
        </div>
        <button
          onClick={() => buildMut.mutate()}
          disabled={buildMut.isPending}
          className="flex items-center gap-2 rounded-lg bg-primary px-5 py-3 text-sm font-semibold text-primary-foreground hover:bg-primary/90 disabled:opacity-60"
        >
          <Sparkles className="h-4 w-4" />
          {buildMut.isPending ? 'Generating…' : 'Build funnel'}
        </button>
      </div>

      {result && (
        <>
          <div className="bg-muted/40 border border-border rounded-xl p-4 text-sm">
            <div className="text-xs uppercase tracking-wider text-muted-foreground mb-1">
              AI notes
            </div>
            <p className="text-foreground">{result.ai_notes}</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-5 gap-3">
            {result.steps.map((s, i) => (
              <div
                key={`${s.stage}-${i}`}
                className="bg-card border border-border rounded-xl p-4 flex flex-col"
              >
                <div
                  className={`inline-block self-start px-2 py-0.5 rounded text-xs font-semibold mb-3 ${
                    STAGE_COLORS[s.stage] || 'bg-muted text-muted-foreground'
                  }`}
                >
                  {i + 1}. {s.stage}
                </div>
                <h3 className="text-sm font-semibold text-foreground mb-1">{s.headline}</h3>
                <p className="text-xs text-muted-foreground mb-3">{s.goal}</p>
                <div className="mt-auto space-y-1 text-xs">
                  <div>
                    <span className="text-muted-foreground">Asset: </span>
                    <span className="text-foreground">{s.asset}</span>
                  </div>
                  <div>
                    <span className="text-muted-foreground">CTA: </span>
                    <span className="text-primary font-semibold">{s.cta}</span>
                  </div>
                  <div>
                    <span className="text-muted-foreground">Channel: </span>
                    <span className="text-foreground font-mono">{s.channel}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  )
}
