'use client'

import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { AlertTriangle, Sparkles } from 'lucide-react'
import { usage } from '@/lib/api-client'

type UsageBreakdown = {
  purpose: string
  calls: number
  input_tokens: number
  output_tokens: number
  cost_pence: number
}

type UsageRollup = {
  tenant_id: string
  period_start: string
  period_end: string
  plan: string | null
  quota_pence: number
  used_pence: number
  used_pct: number
  over_quota: boolean
  total_calls: number
  breakdown: UsageBreakdown[]
}

const fmtCost = (p: number) => (p / 100).toLocaleString('en-GB', { style: 'currency', currency: 'GBP' })

export default function UsagePage() {
  const [days, setDays] = useState(30)
  const { data, isLoading } = useQuery<UsageRollup>({
    queryKey: ['usage-me', days],
    queryFn: () => usage.me(days).then((r) => r.data),
  })

  if (isLoading || !data) {
    return <div className="py-20 text-center text-muted-foreground text-sm">Loading...</div>
  }

  const usedPct = data.quota_pence ? Math.min(100, (data.used_pence / data.quota_pence) * 100) : 0

  return (
    <div className="space-y-6">
      <header className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold flex items-center gap-2">
            <Sparkles className="w-6 h-6 text-blue-600" /> AI Usage
          </h1>
          <p className="text-sm text-muted-foreground mt-1">
            AI spend and call volume across all features for the {days}-day window.
          </p>
        </div>
        <select
          value={days}
          onChange={(e) => setDays(parseInt(e.target.value, 10))}
          className="rounded-lg border px-3 py-2 text-sm"
        >
          <option value={7}>Last 7 days</option>
          <option value={30}>Last 30 days</option>
          <option value={90}>Last 90 days</option>
        </select>
      </header>

      {data.over_quota && (
        <div className="rounded-xl border-l-4 border-amber-500 bg-amber-50 p-4 flex items-start gap-3">
          <AlertTriangle className="w-5 h-5 text-amber-600 mt-0.5" />
          <div>
            <p className="text-sm font-semibold text-amber-900">
              You're over your monthly AI quota
            </p>
            <p className="text-sm text-amber-800">
              CustomerFlow AI is automatically falling back to your local model. Upgrade your plan
              for unlimited cloud AI.
            </p>
          </div>
        </div>
      )}

      <div className="grid gap-4 sm:grid-cols-3">
        <Stat label="Plan" value={data.plan || 'No plan'} />
        <Stat label="Spent (30d)" value={fmtCost(data.used_pence)} />
        <Stat
          label="Quota"
          value={data.quota_pence ? fmtCost(data.quota_pence) : 'Unlimited'}
        />
      </div>

      {data.quota_pence > 0 && (
        <div>
          <div className="flex items-center justify-between text-xs text-muted-foreground mb-1">
            <span>{data.used_pct}% used</span>
            <span>{fmtCost(data.used_pence)} of {fmtCost(data.quota_pence)}</span>
          </div>
          <div className="h-3 rounded-full bg-gray-100 overflow-hidden">
            <div
              className={`h-full transition-all ${
                data.over_quota ? 'bg-red-500' : usedPct > 80 ? 'bg-amber-500' : 'bg-blue-600'
              }`}
              style={{ width: `${usedPct}%` }}
            />
          </div>
        </div>
      )}

      <section className="rounded-xl border bg-white">
        <header className="px-5 py-3 border-b flex items-center justify-between">
          <h2 className="text-sm font-semibold text-foreground/80">Breakdown by feature</h2>
          <span className="text-xs text-muted-foreground">{data.total_calls.toLocaleString()} total calls</span>
        </header>
        {data.breakdown.length === 0 ? (
          <p className="px-5 py-10 text-sm text-center text-gray-400">
            No AI calls in this period yet.
          </p>
        ) : (
          <div className="overflow-x-auto">
          <table className="min-w-[720px] w-full text-sm">
            <thead className="bg-gray-50 text-xs uppercase tracking-wide text-muted-foreground">
              <tr>
                <th className="text-left px-5 py-2 font-medium">Feature</th>
                <th className="text-right px-5 py-2 font-medium">Calls</th>
                <th className="text-right px-5 py-2 font-medium">Input tokens</th>
                <th className="text-right px-5 py-2 font-medium">Output tokens</th>
                <th className="text-right px-5 py-2 font-medium">Cost</th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {data.breakdown.map((b) => (
                <tr key={b.purpose}>
                  <td className="px-5 py-2.5 font-medium capitalize">
                    {b.purpose.replace(/_/g, ' ')}
                  </td>
                  <td className="px-5 py-2.5 text-right">{b.calls.toLocaleString()}</td>
                  <td className="px-5 py-2.5 text-right">{b.input_tokens.toLocaleString()}</td>
                  <td className="px-5 py-2.5 text-right">{b.output_tokens.toLocaleString()}</td>
                  <td className="px-5 py-2.5 text-right font-semibold">{fmtCost(b.cost_pence)}</td>
                </tr>
              ))}
            </tbody>
          </table>
          </div>
        )}
      </section>
    </div>
  )
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl border bg-card p-5">
      <p className="text-xs text-muted-foreground uppercase tracking-wide">{label}</p>
      <p className="text-2xl font-semibold mt-1">{value}</p>
    </div>
  )
}
