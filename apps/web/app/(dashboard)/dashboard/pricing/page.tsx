'use client'

import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import { BadgePoundSterling, Check, Edit2, Info, TrendingUp } from 'lucide-react'
import { freelancerBilling } from '@/lib/api-client'

interface MyBilling {
  user_id: string
  estimated_client_count: number
  calculated_price_gbp: number
  override_price_gbp: number | null
  effective_price_gbp: number
  calculation_source: 'auto' | 'manual'
  tier: '1-50' | '51-100' | '>100'
  next_tier_threshold: number | null
  next_tier_price_gbp: number | null
}

export default function FreelancerPricingPage() {
  const qc = useQueryClient()
  const billing = useQuery<MyBilling>({
    queryKey: ['freelancer-billing-me'],
    queryFn: () => freelancerBilling.me().then((r) => r.data as MyBilling),
    retry: false,
  })

  const [editing, setEditing] = useState(false)
  const [draft, setDraft] = useState('')

  const update = useMutation({
    mutationFn: (count: number) => freelancerBilling.updateClientCount(count),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['freelancer-billing-me'] })
      toast.success('Client count updated — plan recalculated.')
      setEditing(false)
      setDraft('')
    },
    onError: (err: any) => {
      toast.error(err?.response?.data?.detail || 'Could not update.')
    },
  })

  if (billing.isLoading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="animate-spin w-8 h-8 border-4 border-primary border-t-transparent rounded-full" />
      </div>
    )
  }

  if (billing.isError) {
    return (
      <div className="rounded-lg border border-amber-300 bg-amber-50 p-6 text-sm text-amber-900">
        Pricing is only available for freelancer accounts. If you believe this is an error,
        contact support.
      </div>
    )
  }

  const me = billing.data!

  return (
    <div className="max-w-4xl space-y-6">
      <div>
        <h1 className="font-display text-2xl font-bold tracking-tight text-foreground flex items-center gap-2">
          <BadgePoundSterling className="h-6 w-6 text-brand-forest-700" />
          Your CustomerFlow Plan
        </h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Your plan is calculated automatically from how many clients you manage on CustomerFlow.
          Update your client estimate anytime — we&apos;ll recalculate immediately.
        </p>
      </div>

      {/* Hero: effective price */}
      <div className="rounded-xl border border-brand-forest-700 bg-gradient-to-br from-brand-forest-950 via-brand-forest-900 to-brand-teal-900 p-6 shadow-sm">
        <div className="flex flex-wrap items-end justify-between gap-4">
          <div>
            <div className="text-[10px] uppercase tracking-widest text-brand-teal-100/80">
              Your monthly price
            </div>
            <div className="mt-1 flex items-baseline gap-2">
              <span className="font-display text-5xl font-bold text-white tabular-nums">
                £{me.effective_price_gbp.toFixed(2)}
              </span>
              <span className="text-sm text-brand-teal-100/75">/ month</span>
            </div>
            <div className="mt-2 flex flex-wrap items-center gap-2">
              <span className="inline-flex items-center rounded-full bg-brand-teal-400/20 px-2.5 py-0.5 text-[11px] font-medium text-brand-teal-100 ring-1 ring-brand-teal-300/30">
                Tier {me.tier}
              </span>
              <span
                className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-[11px] font-medium ${
                  me.calculation_source === 'manual'
                    ? 'bg-amber-400/20 text-amber-100 ring-1 ring-amber-300/30'
                    : 'bg-brand-forest-700 text-brand-forest-foreground ring-1 ring-brand-forest-300/20'
                }`}
              >
                {me.calculation_source === 'manual'
                  ? 'Manual override (set by Admin)'
                  : 'Auto-calculated'}
              </span>
            </div>
          </div>

          <div className="text-right">
            <div className="text-[10px] uppercase tracking-widest text-brand-teal-100/75">
              Clients you manage
            </div>
            {!editing ? (
              <div className="flex items-center justify-end gap-2 mt-1">
                <span className="font-display text-3xl font-bold tabular-nums text-white">
                  {me.estimated_client_count}
                </span>
                <button
                  onClick={() => {
                    setEditing(true)
                    setDraft(String(me.estimated_client_count))
                  }}
                  className="text-xs text-brand-teal-100 hover:text-white hover:underline flex items-center gap-1"
                >
                  <Edit2 className="h-3 w-3" /> edit
                </button>
              </div>
            ) : (
              <div className="flex items-center justify-end gap-2 mt-1">
                <input
                  type="number"
                  min={0}
                  value={draft}
                  onChange={(e) => setDraft(e.target.value)}
                  className="w-20 h-9 rounded-md border border-brand-forest-600 bg-brand-forest-950/70 px-2 text-right text-base text-white focus:border-brand-teal-300 focus:outline-none focus:ring-2 focus:ring-brand-teal-300/20"
                />
                <button
                  onClick={() => {
                    const n = Number(draft)
                    if (Number.isNaN(n) || n < 0) {
                      toast.error('Enter a non-negative number')
                      return
                    }
                    update.mutate(n)
                  }}
                  disabled={update.isPending}
                  className="rounded-md bg-brand-forest-700 px-3 py-1 text-xs font-semibold text-brand-forest-foreground hover:bg-brand-forest-800"
                >
                  {update.isPending ? 'Saving…' : 'Save'}
                </button>
                <button
                  onClick={() => {
                    setEditing(false)
                    setDraft('')
                  }}
                  className="text-xs text-brand-teal-100/75 hover:text-white"
                >
                  Cancel
                </button>
              </div>
            )}
          </div>
        </div>

        {/* Auto vs Override callout */}
        {me.override_price_gbp !== null && (
          <div className="mt-4 rounded-md border border-amber-300/40 bg-amber-950/50 px-3 py-2 text-xs text-amber-100 flex items-start gap-2">
            <Info className="h-3.5 w-3.5 mt-0.5 shrink-0" />
            <div>
              Your effective price is currently a manual override of £
              {me.override_price_gbp.toFixed(2)} (auto-calculated would be £
              {me.calculated_price_gbp.toFixed(2)}). Override is set by CustomerFlow staff —
              contact support if you have questions.
            </div>
          </div>
        )}
      </div>

      {/* Tier ladder */}
      <div className="rounded-xl border border-border bg-card p-5">
        <h2 className="text-sm font-semibold uppercase tracking-widest text-muted-foreground mb-4">
          Pricing tiers
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          <TierTile
            tier="1-50"
            current={me.tier === '1-50'}
            label="Starter portfolio"
            price="£50/mo"
            sub="Flat rate"
            range="1 – 50 clients"
          />
          <TierTile
            tier="51-100"
            current={me.tier === '51-100'}
            label="Growing portfolio"
            price="£40/mo"
            sub="Better rate at scale"
            range="51 – 100 clients"
          />
          <TierTile
            tier=">100"
            current={me.tier === '>100'}
            label="Agency-scale"
            price="£40 + £5/extra"
            sub="No upper cap"
            range="100+ clients"
          />
        </div>

        {me.next_tier_threshold && me.next_tier_price_gbp !== null && (
          <div className="mt-4 flex items-center gap-2 text-xs text-muted-foreground">
            <TrendingUp className="h-3.5 w-3.5 text-brand-forest-700" />
            <span>
              At {me.next_tier_threshold} clients, your auto-calculated price would be £
              {me.next_tier_price_gbp.toFixed(2)}/month.
            </span>
          </div>
        )}
      </div>

      {/* Whats included */}
      <div className="rounded-xl border border-border bg-card p-5">
        <h2 className="text-sm font-semibold uppercase tracking-widest text-muted-foreground mb-3">
          What&apos;s included
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-sm">
          {[
            'Unlimited managed clients (per the tier above)',
            'CRM, automations, outreach, reviews per client',
            'AI Social posting on behalf of each client',
            'Analytics and reports per client + portfolio',
            'WhatsApp + SMS messaging',
            'Marketer tools (funnel, audience, competitor)',
            'Priority email support',
            '14-day free trial — cancel anytime',
          ].map((item) => (
            <div key={item} className="flex items-start gap-2">
              <Check className="h-4 w-4 mt-0.5 shrink-0 text-brand-forest-600" />
              <span className="text-foreground/90">{item}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}


function TierTile({
  tier,
  current,
  label,
  price,
  sub,
  range,
}: {
  tier: string
  current: boolean
  label: string
  price: string
  sub: string
  range: string
}) {
  return (
    <div
      className={`rounded-lg border p-4 transition-shadow ${
        current
          ? 'border-brand-forest-700 bg-brand-forest-900 text-white shadow-sm'
          : 'border-border bg-card'
      }`}
    >
      <div className="flex items-center justify-between">
        <span
          className={`text-[10px] uppercase tracking-widest ${
            current ? 'text-brand-teal-100/75' : 'text-muted-foreground'
          }`}
        >
          Tier {tier}
        </span>
        {current && (
          <span className="rounded-full bg-brand-teal-400/20 px-2 py-0.5 text-[10px] font-semibold uppercase text-brand-teal-100 ring-1 ring-brand-teal-300/30">
            Your tier
          </span>
        )}
      </div>
      <h3 className={`mt-1 text-base font-semibold ${current ? 'text-white' : 'text-foreground'}`}>
        {label}
      </h3>
      <div className={`mt-2 font-display text-2xl font-bold ${current ? 'text-white' : 'text-foreground'}`}>
        {price}
      </div>
      <div className={`text-xs mt-0.5 ${current ? 'text-brand-teal-100/75' : 'text-muted-foreground'}`}>
        {sub}
      </div>
      <div
        className={`mt-3 text-[11px] uppercase tracking-widest ${
          current ? 'text-brand-teal-100/70' : 'text-muted-foreground/80'
        }`}
      >
        {range}
      </div>
    </div>
  )
}
