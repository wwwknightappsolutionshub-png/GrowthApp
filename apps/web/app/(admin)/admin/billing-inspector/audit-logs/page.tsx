'use client'

import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { ChevronLeft, ChevronRight, FileSearch, RefreshCw } from 'lucide-react'
import { billingInspectorApi } from '@/lib/api-client'
import { AuditLogTable, type AuditRow } from '../components/AuditLogTable'

type Type = 'plan_change' | 'overage_flag' | 'invoice_event' | 'payment_failure'

interface AuditResponse {
  items: AuditRow[]
  total: number
  page: number
  page_size: number
}

export default function BillingInspectorAuditLogsPage() {
  const [page, setPage] = useState(1)
  const [pageSize] = useState(50)
  const [type, setType] = useState<'' | Type>('')

  const q = useQuery({
    queryKey: ['billing-inspector', 'audit-logs', page, pageSize, type],
    queryFn: () =>
      billingInspectorApi
        .auditLogs({ page, page_size: pageSize, type: (type || undefined) as Type | undefined })
        .then((r) => r.data as AuditResponse),
  })

  const rows = q.data?.items ?? []
  const total = q.data?.total ?? 0
  const totalPages = Math.max(1, Math.ceil(total / pageSize))

  return (
    <div className="text-white">
      <div className="mb-6 flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <FileSearch className="h-6 w-6 text-amber-400" /> Billing Audit Logs
          </h1>
          <p className="text-sm text-gray-400 mt-1">
            All billing-relevant events across tenants and freelancers.
          </p>
        </div>
        <button
          onClick={() => q.refetch()}
          className="inline-flex items-center gap-1.5 rounded-md border border-gray-700 bg-gray-900 px-3 py-1.5 text-xs text-gray-300 hover:bg-gray-800"
        >
          <RefreshCw className={`h-3.5 w-3.5 ${q.isFetching ? 'animate-spin' : ''}`} /> Refresh
        </button>
      </div>

      <div className="mb-3 flex flex-wrap items-center gap-2 rounded-lg border border-gray-800 bg-gray-900 p-3">
        <select
          value={type}
          onChange={(e) => {
            setPage(1)
            setType(e.target.value as '' | Type)
          }}
          className="rounded-md border border-gray-700 bg-gray-950 px-2.5 py-1 text-xs text-gray-200"
        >
          <option value="">All types</option>
          <option value="plan_change">Plan change</option>
          <option value="overage_flag">Overage flag</option>
          <option value="invoice_event">Invoice event</option>
          <option value="payment_failure">Payment failure</option>
        </select>
        <span className="ml-auto text-xs text-gray-500">{total} event{total === 1 ? '' : 's'}</span>
      </div>

      <AuditLogTable rows={rows} isLoading={q.isLoading} isError={q.isError} />

      <div className="mt-3 flex items-center justify-end gap-2 text-xs text-gray-400">
        <button
          disabled={page <= 1}
          onClick={() => setPage((p) => Math.max(1, p - 1))}
          className="inline-flex items-center gap-1 rounded-md border border-gray-700 bg-gray-900 px-2 py-1 disabled:opacity-40"
        >
          <ChevronLeft className="h-3.5 w-3.5" /> Prev
        </button>
        <span>
          Page {page} / {totalPages}
        </span>
        <button
          disabled={page >= totalPages}
          onClick={() => setPage((p) => p + 1)}
          className="inline-flex items-center gap-1 rounded-md border border-gray-700 bg-gray-900 px-2 py-1 disabled:opacity-40"
        >
          Next <ChevronRight className="h-3.5 w-3.5" />
        </button>
      </div>
    </div>
  )
}
