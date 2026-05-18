'use client'

import { useEffect, useState } from 'react'
import { BellRing, Loader2, RefreshCw } from 'lucide-react'
import { toast } from 'sonner'

import { admin } from '@/lib/api-client'
import { cn } from '@/lib/utils'

const METRIC_LABELS: Record<string, string> = {
  missed_leads: 'Stale new leads (24h+)',
  missed_messages: 'Open conversations',
  missed_calls: 'Missed-call leads (new)',
  missed_reviews: 'Stale review requests (7d+)',
  missed_bookings: 'Past bookings not closed',
  overdue_invoices: 'Overdue / past-due invoices',
}

const METRIC_SHORT: Record<string, string> = {
  missed_leads: 'Stale leads',
  missed_messages: 'Open inbox',
  missed_calls: 'Missed calls',
  missed_reviews: 'Stale reviews',
  missed_bookings: 'Bookings',
  overdue_invoices: 'Invoices',
}

interface Metrics {
  missed_leads: number
  missed_messages: number
  missed_calls: number
  missed_reviews: number
  missed_bookings: number
  overdue_invoices: number
}

interface Row {
  tenant_id: string
  name: string
  slug: string
  email: string | null
  is_active: boolean
  metrics: Metrics
  flags: string[]
  severity: string
}

export default function TenantHealthPage() {
  const [rows, setRows] = useState<Row[]>([])
  const [loading, setLoading] = useState(true)
  const [reminding, setReminding] = useState<string | null>(null)

  async function load() {
    setLoading(true)
    try {
      const res = await admin.listTenantHealth()
      setRows(res.data as Row[])
    } catch (e) {
      toast.error('Could not load tenant health')
      console.error(e)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    void load()
  }, [])

  async function remind(tenantId: string) {
    const note = window.prompt('Optional note to include in the reminder (leave blank for default):') ?? ''
    setReminding(tenantId)
    try {
      const res = await admin.remindTenant(tenantId, note.trim() ? { note: note.trim() } : undefined)
      const data = res.data as { owners_emailed?: number; flags?: string[] }
      toast.success(
        `Reminder sent. In-app notification posted; ${data.owners_emailed ?? 0} owner email(s) attempted.`,
      )
      await load()
    } catch (e) {
      toast.error('Reminder failed')
      console.error(e)
    } finally {
      setReminding(null)
    }
  }

  return (
    <div>
      <header className="mb-6 flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold text-white">Tenant pulse</h1>
          <p className="mt-1 max-w-3xl text-sm text-gray-400">
            Flags per active tenant: stale leads, open message threads, missed-call captures still open, review
            requests waiting, bookings not marked complete, and invoices past due. Send a gentle nudge — owners get
            email (best-effort) and every member sees an in-app notification.
          </p>
        </div>
        <button
          type="button"
          onClick={() => void load()}
          disabled={loading}
          className="inline-flex items-center gap-2 rounded-md border border-gray-700 bg-gray-900 px-3 py-2 text-sm text-white hover:bg-gray-800 disabled:opacity-50"
        >
          <RefreshCw className={cn('h-4 w-4', loading && 'animate-spin')} />
          Refresh
        </button>
      </header>

      {loading ? (
        <div className="flex justify-center py-16 text-gray-500">
          <Loader2 className="h-8 w-8 animate-spin" />
        </div>
      ) : rows.length === 0 ? (
        <p className="text-sm text-gray-500">No active tenants.</p>
      ) : (
        <div className="overflow-x-auto rounded-lg border border-gray-800">
          <table className="w-full min-w-[880px] text-left text-sm">
            <thead className="border-b border-gray-800 bg-gray-900/80 text-xs uppercase tracking-wide text-gray-500">
              <tr>
                <th className="px-4 py-3">Tenant</th>
                <th className="px-2 py-3 text-center">Severity</th>
                {Object.keys(METRIC_LABELS).map((k) => (
                  <th
                    key={k}
                    title={METRIC_LABELS[k]}
                    className="px-2 py-3 text-center font-normal text-[10px] text-gray-500"
                  >
                    {METRIC_SHORT[k]}
                  </th>
                ))}
                <th className="px-4 py-3 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-800/80">
              {rows.map((r) => (
                <tr key={r.tenant_id} className="bg-gray-950/30 hover:bg-gray-900/40">
                  <td className="px-4 py-3">
                    <div className="font-medium text-white">{r.name}</div>
                    <div className="font-mono text-xs text-gray-500">{r.slug}</div>
                  </td>
                  <td className="px-2 py-3 text-center">
                    <span
                      className={cn(
                        'inline-flex rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase',
                        r.severity === 'critical' && 'bg-rose-500/20 text-rose-300',
                        r.severity === 'warn' && 'bg-amber-500/20 text-amber-200',
                        r.severity === 'ok' && 'bg-emerald-500/15 text-emerald-300/90',
                      )}
                    >
                      {r.severity}
                    </span>
                  </td>
                  {Object.keys(METRIC_LABELS).map((k) => (
                    <td key={k} className="px-2 py-3 text-center tabular-nums text-gray-300">
                      {r.metrics[k as keyof Metrics] ?? 0}
                    </td>
                  ))}
                  <td className="px-4 py-3 text-right">
                    <button
                      type="button"
                      disabled={reminding === r.tenant_id}
                      onClick={() => void remind(r.tenant_id)}
                      className="inline-flex items-center gap-1.5 rounded-md border border-amber-500/40 bg-amber-500/10 px-2.5 py-1.5 text-xs font-semibold text-amber-200 hover:bg-amber-500/20 disabled:opacity-50"
                    >
                      {reminding === r.tenant_id ? (
                        <Loader2 className="h-3.5 w-3.5 animate-spin" />
                      ) : (
                        <BellRing className="h-3.5 w-3.5" />
                      )}
                      Nudge
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
