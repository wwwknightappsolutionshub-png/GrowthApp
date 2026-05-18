'use client'

import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { Copy, Loader2, Megaphone, Sparkles, Wand2 } from 'lucide-react'
import { ai } from '@/lib/api-client'

type Platform = 'google' | 'facebook' | 'instagram' | 'tiktok'
type Objective = 'leads' | 'sales' | 'awareness'

type Variant = {
  headline: string
  description: string
  primary_text?: string | null
  cta?: string | null
  image_brief?: string | null
}

type AdsResponse = {
  platform: Platform
  variants: Variant[]
  provider: string
  model: string
}

export default function AdsPage() {
  const [platform, setPlatform] = useState<Platform>('google')
  const [objective, setObjective] = useState<Objective>('leads')
  const [audience, setAudience] = useState('Homeowners aged 30-55 within a 15-mile radius')
  const [offer, setOffer] = useState('Free quote within 24 hours, fixed prices, fully insured')
  const [tone, setTone] = useState('professional and confident')
  const [variantCount, setVariantCount] = useState(3)

  const mutation = useMutation<{ data: AdsResponse }, Error>({
    mutationFn: () =>
      ai.generateAds({
        platform,
        objective,
        audience,
        offer,
        tone,
        variant_count: variantCount,
      }),
  })

  return (
    <div className="space-y-6">
      <header className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold flex items-center gap-2">
            <Megaphone className="w-6 h-6 text-blue-600" /> AI Ads Generator
          </h1>
          <p className="text-sm text-muted-foreground mt-1">
            Generate platform-tuned ad copy variants and image briefs in seconds.
          </p>
        </div>
      </header>

      <div className="grid gap-6 lg:grid-cols-3">
        {/* Input panel */}
        <section className="lg:col-span-1 rounded-xl border bg-card p-5 space-y-4">
          <div>
            <label className="text-xs font-medium text-foreground/80 uppercase tracking-wide">
              Platform
            </label>
            <div className="mt-1 grid grid-cols-4 gap-1 text-xs">
              {(['google', 'facebook', 'instagram', 'tiktok'] as Platform[]).map((p) => (
                <button
                  key={p}
                  onClick={() => setPlatform(p)}
                  className={`px-2 py-2 rounded-md capitalize border transition-colors ${
                    platform === p
                      ? 'border-blue-600 bg-blue-50 text-blue-700 font-medium'
                      : 'border-border hover:bg-gray-50'
                  }`}
                >
                  {p}
                </button>
              ))}
            </div>
          </div>

          <div>
            <label className="text-xs font-medium text-foreground/80 uppercase tracking-wide">
              Objective
            </label>
            <select
              value={objective}
              onChange={(e) => setObjective(e.target.value as Objective)}
              className="mt-1 w-full rounded-md border px-3 py-2 text-sm"
            >
              <option value="leads">Generate leads</option>
              <option value="sales">Drive sales</option>
              <option value="awareness">Brand awareness</option>
            </select>
          </div>

          <Field label="Target audience" value={audience} onChange={setAudience} multiline rows={3} />
          <Field label="Offer / value proposition" value={offer} onChange={setOffer} multiline rows={3} />
          <Field label="Tone of voice" value={tone} onChange={setTone} />

          <div>
            <label className="text-xs font-medium text-foreground/80 uppercase tracking-wide">
              Variants
            </label>
            <input
              type="number"
              min={1}
              max={5}
              value={variantCount}
              onChange={(e) => setVariantCount(parseInt(e.target.value || '3', 10))}
              className="mt-1 w-full rounded-md border px-3 py-2 text-sm"
            />
          </div>

          <button
            onClick={() => mutation.mutate()}
            disabled={mutation.isPending || !audience.trim() || !offer.trim()}
            className="w-full inline-flex items-center justify-center gap-2 rounded-lg bg-blue-600 px-4 py-2.5 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
          >
            {mutation.isPending ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Wand2 className="w-4 h-4" />
            )}
            Generate ads
          </button>

          {mutation.isError && (
            <p className="text-xs text-red-600">
              {(mutation.error as Error)?.message || 'Generation failed'}
            </p>
          )}
        </section>

        {/* Results */}
        <section className="lg:col-span-2 space-y-4">
          {mutation.data ? (
            <>
              <div className="text-xs text-muted-foreground flex items-center gap-2">
                <Sparkles className="w-4 h-4" />
                Generated by {mutation.data.data.provider}/{mutation.data.data.model}
              </div>
              {mutation.data.data.variants.map((v, i) => (
                <VariantCard key={i} variant={v} index={i + 1} platform={platform} />
              ))}
            </>
          ) : (
            <div className="rounded-xl border bg-card p-12 text-center text-muted-foreground text-sm">
              Configure your ad brief and click <strong>Generate ads</strong>.
            </div>
          )}
        </section>
      </div>
    </div>
  )
}

function Field({
  label,
  value,
  onChange,
  multiline,
  rows,
}: {
  label: string
  value: string
  onChange: (v: string) => void
  multiline?: boolean
  rows?: number
}) {
  return (
    <div>
      <label className="text-xs font-medium text-foreground/80 uppercase tracking-wide">
        {label}
      </label>
      {multiline ? (
        <textarea
          value={value}
          onChange={(e) => onChange(e.target.value)}
          rows={rows || 2}
          className="mt-1 w-full rounded-md border px-3 py-2 text-sm"
        />
      ) : (
        <input
          value={value}
          onChange={(e) => onChange(e.target.value)}
          className="mt-1 w-full rounded-md border px-3 py-2 text-sm"
        />
      )}
    </div>
  )
}

function VariantCard({
  variant,
  index,
  platform,
}: {
  variant: Variant
  index: number
  platform: Platform
}) {
  const copy = (text: string) => navigator.clipboard.writeText(text)
  const full = [variant.headline, variant.description, variant.primary_text]
    .filter(Boolean)
    .join('\n\n')

  return (
    <article className="rounded-xl border bg-card p-5 shadow-sm space-y-3">
      <div className="flex items-center justify-between">
        <span className="text-xs font-semibold uppercase tracking-wide text-blue-700">
          Variant {index}
        </span>
        <button
          onClick={() => copy(full)}
          className="inline-flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground"
        >
          <Copy className="w-3.5 h-3.5" /> Copy all
        </button>
      </div>
      <div>
        <div className="text-xs text-muted-foreground mb-1">Headline ({variant.headline.length} chars)</div>
        <h3 className="text-lg font-semibold leading-tight">{variant.headline}</h3>
      </div>
      <div>
        <div className="text-xs text-muted-foreground mb-1">
          Description ({variant.description.length} chars)
        </div>
        <p className="text-sm">{variant.description}</p>
      </div>
      {variant.primary_text && platform !== 'google' && (
        <div>
          <div className="text-xs text-muted-foreground mb-1">Primary text</div>
          <p className="text-sm whitespace-pre-wrap">{variant.primary_text}</p>
        </div>
      )}
      {(variant.cta || variant.image_brief) && (
        <div className="grid sm:grid-cols-2 gap-3 pt-2 border-t">
          {variant.cta && (
            <div>
              <div className="text-xs text-muted-foreground mb-1">CTA</div>
              <p className="text-sm font-medium">{variant.cta}</p>
            </div>
          )}
          {variant.image_brief && (
            <div>
              <div className="text-xs text-muted-foreground mb-1">Image brief</div>
              <p className="text-sm italic text-foreground/80">{variant.image_brief}</p>
            </div>
          )}
        </div>
      )}
    </article>
  )
}
