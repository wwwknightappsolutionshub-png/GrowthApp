'use client'

import { useQuery } from '@tanstack/react-query'
import Link from 'next/link'
import { AlertTriangle, BarChart3, FileSearch, RefreshCw, Users } from 'lucide-react'
import { billingInspectorApi } from '@/lib/api-client'
import { BillingSummaryCards, type OverviewData } from './components/BillingSummaryCards'

function fmtPence(p: number): string {
  return `£${(p / 100).toFixed(2)}`
}

export default function BillingInspectorOverviewPage() {
  const overview = useQuery({
    queryKey: ['billing-inspector', 'overview'],
    queryFn: () => billingInspectorApi.overview().then((r) => r.data as OverviewData),
  })

  return (
    <div className="text-white">
      <div className="mb-6 flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <BarChart3 className="h-6 w-6 text-amber-400" /> Billing Inspector — Overview
          </h1>
          <p className="text-sm text-gray-400 mt-1">
            Global billing posture across all tenants and freelancers. Read-only oversight.
          </p>
        </div>
        <button
          onClick={() => overview.refetch()}
          className="inline-flex items-center gap-1.5 rounded-md border border-gray-700 bg-gray-900 px-3 py-1.5 text-xs text-gray-300 hover:bg-gray-800"
        >
          <RefreshCw className={`h-3.5 w-3.5 ${overview.isFetching ? 'animate-spin' : ''}`} />
          Refresh Billing Snapshot
        </button>
      </div>

      <BillingSummaryCards data={overview.data} />

      <div className="mt-6 grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div className="rounded-lg border border-gray-800 bg-gray-900 p-5">
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-sm font-semibold uppercase tracking-widest text-gray-400">
              Recent payment failures
            </h2>
            <span className="text-[10px] text-gray-500">Latest 5</span>
          </div>
          {overview.isLoading ? (
            <div className="text-sm text-gray-500">Loading…</div>
          ) : overview.data?.recent_payment_failures.length ? (
            <ul className="divide-y divide-gray-800">
              {overview.data.recent_payment_failures.map((f) => (
                <li key={f.invoice_id} className="py-2 flex items-center justify-between gap-3">
                  <Link
                    href={`/admin/billing-inspector/invoices/${f.invoice_id}`}
                    className="font-mono text-xs text-amber-400 hover:underline"
                  >
                    {f.invoice_id.slice(0, 8)}…
                  </Link>
                  <span className="text-xs text-gray-400">{f.status}</span>
                  <span className="ml-auto text-sm tabular-nums">{fmtPence(f.amount_pence)}</span>
                </li>
              ))}
            </ul>
          ) : (
            <div className="text-sm text-gray-500">No recent payment failures.</div>
          )}
        </div>

        <div className="rounded-lg border border-gray-800 bg-gray-900 p-5">
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-sm font-semibold uppercase tracking-widest text-gray-400">
              Global overage alerts
            </h2>
            <AlertTriangle className="h-3.5 w-3.5 text-amber-400" />
          </div>
          {overview.isLoading ? (
            <div className="text-sm text-gray-500">Loading…</div>
          ) : overview.data?.global_overage_alerts.length ? (
            <ul className="divide-y divide-gray-800">
              {overview.data.global_overage_alerts.slice(0, 10).map((a, i) => (
                <li key={`${a.entity_id}-${i}`} className="py-2 flex items-center justify-between gap-3">
                  <Link
                    href={
                      a.entity_type === 'tenant'
                        ? `/admin/billing-inspector/tenants/${a.entity_id}`
                        : `/admin/billing-inspector/freelancers/${a.entity_id}`
                    }
                    className="text-sm text-amber-300 hover:underline"
                  >
                    {a.entity_name}
                  </Link>
                  <span className="text-[10px] uppercase tracking-widest text-gray-500">
                    {a.flag}
                  </span>
                </li>
              ))}
            </ul>
          ) : (
            <div className="text-sm text-gray-500">No overage alerts globally.</div>
          )}
        </div>
      </div>

      <div className="mt-6 grid grid-cols-1 md:grid-cols-3 gap-3">
        <Link
          href="/admin/billing-inspector/tenants"
          className="rounded-lg border border-gray-800 bg-gray-900 p-4 hover:bg-gray-800 flex items-center gap-3"
        >
          <Users className="h-5 w-5 text-amber-400" />
          <div>
            <div className="text-sm font-semibold text-white">Tenants list</div>
            <div className="text-xs text-gray-500">Plan, seats, contacts, invoice state.</div>
          </div>
        </Link>
        <Link
          href="/admin/billing-inspector/freelancers"
          className="rounded-lg border border-gray-800 bg-gray-900 p-4 hover:bg-gray-800 flex items-center gap-3"
        >
          <Users className="h-5 w-5 text-amber-400" />
          <div>
            <div className="text-sm font-semibold text-white">Freelancers list</div>
            <div className="text-xs text-gray-500">Auto-calculated tiers + overrides.</div>
          </div>
        </Link>
        <Link
          href="/admin/billing-inspector/audit-logs"
          className="rounded-lg border border-gray-800 bg-gray-900 p-4 hover:bg-gray-800 flex items-center gap-3"
        >
          <FileSearch className="h-5 w-5 text-amber-400" />
          <div>
            <div className="text-sm font-semibold text-white">Audit logs</div>
            <div className="text-xs text-gray-500">Plan changes, overages, invoice events.</div>
          </div>
        </Link>
      </div>
    </div>
  )
}
