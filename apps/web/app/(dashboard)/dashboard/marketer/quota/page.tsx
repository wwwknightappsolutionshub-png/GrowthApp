'use client'

import { useQuery } from '@tanstack/react-query'
import { Gauge, RefreshCw } from 'lucide-react'
import { marketer } from '@/lib/api-client'

interface QuotaSummary {
  tenant_id: string
  max_reports_per_month: number
  used_reports: number
  remaining: number
}

export default function QuotaSummaryPage() {
  const { data, isLoading, refetch, isRefetching } = useQuery({
    queryKey: ['marketer', 'quota'],
    queryFn: () => marketer.quotas().then((r) => r.data as QuotaSummary),
  })

  const max = data?.max_reports_per_month ?? 0
  const used = data?.used_reports ?? 0
  const remaining = data?.remaining ?? 0
  const pct = max > 0 ? Math.min(100, Math.round((used / max) * 100)) : 0

  return (
    <div className="space-y-6 max-w-3xl">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-foreground flex items-center gap-2">
            <Gauge className="h-6 w-6 text-primary" /> Monthly Quota
          </h1>
          <p className="text-sm text-muted-foreground mt-1">
            How many Marketer Tools reports you've used this month and what's left.
          </p>
        </div>
        <button
          onClick={() => refetch()}
          className="flex items-center gap-2 rounded-lg bg-muted px-3 py-2 text-sm hover:bg-muted/70"
        >
          <RefreshCw className={`h-4 w-4 ${isRefetching ? 'animate-spin' : ''}`} /> Refresh
        </button>
      </div>

      {isLoading ? (
        <div className="text-muted-foreground">Loading…</div>
      ) : (
        <>
          <div className="grid grid-cols-3 gap-3">
            {[
              ['Used', used, 'text-foreground'],
              ['Remaining', remaining, remaining === 0 ? 'text-red-600' : 'text-green-600'],
              ['Monthly cap', max, 'text-foreground'],
            ].map(([label, val, color]) => (
              <div
                key={label as string}
                className="bg-card border border-border rounded-xl p-4"
              >
                <div className="text-xs uppercase tracking-wider text-muted-foreground">
                  {label}
                </div>
                <div className={`text-3xl font-bold mt-1 ${color as string}`}>
                  {val as number}
                </div>
              </div>
            ))}
          </div>

          <div className="bg-card border border-border rounded-xl p-6">
            <div className="flex items-center justify-between text-sm mb-2">
              <span className="font-semibold text-foreground">Usage this month</span>
              <span className="font-mono text-muted-foreground">
                {used} / {max} ({pct}%)
              </span>
            </div>
            <div className="h-3 rounded-full bg-muted overflow-hidden">
              <div
                className={`h-full rounded-full transition-all ${
                  pct >= 100
                    ? 'bg-red-500'
                    : pct >= 80
                      ? 'bg-amber-500'
                      : 'bg-primary'
                }`}
                style={{ width: `${pct}%` }}
              />
            </div>
            {pct >= 100 ? (
              <p className="text-xs text-red-600 mt-3">
                You've hit your monthly quota. Upgrade your plan or wait until next month.
              </p>
            ) : pct >= 80 ? (
              <p className="text-xs text-amber-600 mt-3">
                You're approaching your monthly cap. Consider upgrading if you need headroom.
              </p>
            ) : (
              <p className="text-xs text-muted-foreground mt-3">
                Use your quota across funnel builder, audience research, and competitor scans.
              </p>
            )}
          </div>

          <div className="bg-muted/40 border border-border rounded-xl p-4 text-xs text-muted-foreground">
            <strong>How it counts:</strong> Each funnel blueprint, audience research report, or
            competitor scan you generate uses 1 unit from your monthly quota. Your cap resets at
            the start of every month and is set by your subscription plan.
          </div>
        </>
      )}
    </div>
  )
}
