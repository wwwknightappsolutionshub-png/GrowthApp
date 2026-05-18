'use client'

export interface UsageGraphRow {
  label: string
  used: number
  limit: number | null
}

function pct(used: number, limit: number | null): number {
  if (!limit) return 0
  return Math.min(100, Math.round((used / limit) * 100))
}

function barTone(used: number, limit: number | null): string {
  if (!limit) return 'bg-gray-700'
  const r = used / limit
  if (r >= 1) return 'bg-red-500'
  if (r >= 0.8) return 'bg-amber-500'
  return 'bg-emerald-500'
}

export function UsageGraph({ rows }: { rows: UsageGraphRow[] }) {
  if (!rows.length) return null
  return (
    <div className="space-y-3">
      {rows.map((r) => (
        <div key={r.label}>
          <div className="flex items-center justify-between text-xs text-gray-400">
            <span className="font-medium uppercase tracking-wider">{r.label}</span>
            <span className="tabular-nums">
              {r.used} / {r.limit ?? '∞'}
              {r.limit ? <span className="ml-2 text-gray-500">({pct(r.used, r.limit)}%)</span> : null}
            </span>
          </div>
          <div className="mt-1 h-2 w-full overflow-hidden rounded-full bg-gray-800">
            <div
              className={`h-full ${barTone(r.used, r.limit)} transition-all`}
              style={{ width: `${pct(r.used, r.limit)}%` }}
            />
          </div>
        </div>
      ))}
    </div>
  )
}
