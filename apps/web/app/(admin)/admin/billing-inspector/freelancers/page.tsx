'use client'

import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import Link from 'next/link'
import { Briefcase, ChevronLeft, ChevronRight, RefreshCw } from 'lucide-react'
import { billingInspectorApi } from '@/lib/api-client'
import { BillingTable, type BillingTableColumn } from '../components/BillingTable'

interface FreelancerRow {
  user_id: string
  freelancer_name: string
  email: string
  managed_clients: number
  auto_plan_tier: '1-50' | '51-100' | '>100'
  calculated_price_gbp: number | null
  override_price_gbp: number | null
  monthly_price_gbp: number | null
  calculation_source: string | null
  last_invoice_status: string | null
  next_billing_date: string | null
  overage_alerts: string[]
}

interface FreelancerListResponse {
  items: FreelancerRow[]
  total: number
  page: number
  page_size: number
}

export default function BillingInspectorFreelancersPage() {
  const [page, setPage] = useState(1)
  const [pageSize] = useState(20)
  const [plan, setPlan] = useState<'' | '1-50' | '51-100' | '>100'>('')
  const [overage, setOverage] = useState<'' | 'any' | 'none'>('')
  const [invoiceStatus, setInvoiceStatus] = useState<string>('')

  const list = useQuery({
    queryKey: ['billing-inspector', 'freelancers', page, pageSize, plan, overage, invoiceStatus],
    queryFn: () =>
      billingInspectorApi
        .listFreelancers({
          page,
          page_size: pageSize,
          plan: (plan || undefined) as '1-50' | '51-100' | '>100' | undefined,
          overage_state: (overage || undefined) as 'any' | 'none' | undefined,
          invoice_status: invoiceStatus || undefined,
        })
        .then((r) => r.data as FreelancerListResponse),
  })

  const rows = list.data?.items ?? []
  const total = list.data?.total ?? 0
  const totalPages = Math.max(1, Math.ceil(total / pageSize))

  const columns: BillingTableColumn<FreelancerRow>[] = [
    {
      key: 'name',
      header: 'Freelancer Name',
      render: (r) => (
        <Link
          href={`/admin/billing-inspector/freelancers/${r.user_id}`}
          className="font-medium text-amber-300 hover:underline"
        >
          {r.freelancer_name}
        </Link>
      ),
    },
    {
      key: 'tier',
      header: 'Auto Tier',
      render: (r) => (
        <span className="inline-flex items-center rounded-full bg-gray-800 px-2 py-0.5 text-[10px] uppercase tracking-widest text-gray-300">
          {r.auto_plan_tier}
        </span>
      ),
    },
    { key: 'clients', header: 'Managed Clients', align: 'right', render: (r) => r.managed_clients },
    {
      key: 'price',
      header: 'Monthly Price',
      align: 'right',
      render: (r) => (r.monthly_price_gbp != null ? `£${r.monthly_price_gbp.toFixed(2)}` : '—'),
    },
    {
      key: 'source',
      header: 'Source',
      render: (r) =>
        r.calculation_source ? (
          <span
            className={`inline-flex items-center rounded-full px-2 py-0.5 text-[10px] uppercase tracking-widest ${
              r.calculation_source === 'manual'
                ? 'bg-amber-500/15 text-amber-300'
                : 'bg-emerald-500/15 text-emerald-300'
            }`}
          >
            {r.calculation_source}
          </span>
        ) : (
          <span className="text-xs text-gray-500">—</span>
        ),
    },
    {
      key: 'invoice',
      header: 'Last Invoice',
      render: (r) =>
        r.last_invoice_status ? (
          <span className="inline-flex items-center rounded-full bg-gray-800 px-2 py-0.5 text-[10px] uppercase tracking-widest text-gray-300">
            {r.last_invoice_status}
          </span>
        ) : (
          <span className="text-gray-500">—</span>
        ),
    },
    {
      key: 'next',
      header: 'Next Billing',
      render: (r) =>
        r.next_billing_date ? new Date(r.next_billing_date).toLocaleDateString() : <span className="text-gray-500">—</span>,
    },
    {
      key: 'alerts',
      header: 'Overage Alerts',
      render: (r) =>
        r.overage_alerts.length ? (
          <div className="flex flex-wrap gap-1">
            {r.overage_alerts.map((a) => (
              <span
                key={a}
                className="inline-flex items-center rounded-full bg-amber-500/15 px-2 py-0.5 text-[10px] text-amber-300"
              >
                {a}
              </span>
            ))}
          </div>
        ) : (
          <span className="text-xs text-gray-500">none</span>
        ),
    },
    {
      key: 'actions',
      header: 'Actions',
      align: 'right',
      render: (r) => (
        <Link
          href={`/admin/billing-inspector/freelancers/${r.user_id}`}
          className="inline-flex items-center rounded-md border border-gray-700 bg-gray-900 px-2.5 py-1 text-xs text-gray-200 hover:bg-gray-800"
        >
          Inspect
        </Link>
      ),
    },
  ]

  return (
    <div className="text-white">
      <div className="mb-6 flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <Briefcase className="h-6 w-6 text-amber-400" /> Freelancers Billing
          </h1>
          <p className="text-sm text-gray-400 mt-1">
            Auto-calculated tiers based on managed client count. Manual overrides visible in the source column.
          </p>
        </div>
        <button
          onClick={() => list.refetch()}
          className="inline-flex items-center gap-1.5 rounded-md border border-gray-700 bg-gray-900 px-3 py-1.5 text-xs text-gray-300 hover:bg-gray-800"
        >
          <RefreshCw className={`h-3.5 w-3.5 ${list.isFetching ? 'animate-spin' : ''}`} /> Refresh
        </button>
      </div>

      <div className="mb-3 flex flex-wrap items-center gap-2 rounded-lg border border-gray-800 bg-gray-900 p-3">
        <select
          value={plan}
          onChange={(e) => {
            setPage(1)
            setPlan(e.target.value as '' | '1-50' | '51-100' | '>100')
          }}
          className="rounded-md border border-gray-700 bg-gray-950 px-2.5 py-1 text-xs text-gray-200"
        >
          <option value="">Tier: any</option>
          <option value="1-50">1–50</option>
          <option value="51-100">51–100</option>
          <option value=">100">&gt;100</option>
        </select>
        <select
          value={overage}
          onChange={(e) => {
            setPage(1)
            setOverage(e.target.value as '' | 'any' | 'none')
          }}
          className="rounded-md border border-gray-700 bg-gray-950 px-2.5 py-1 text-xs text-gray-200"
        >
          <option value="">Overage: any</option>
          <option value="any">Overage: only with alerts</option>
          <option value="none">Overage: only clean</option>
        </select>
        <input
          value={invoiceStatus}
          onChange={(e) => {
            setPage(1)
            setInvoiceStatus(e.target.value)
          }}
          placeholder="Invoice status filter"
          className="rounded-md border border-gray-700 bg-gray-950 px-2.5 py-1 text-xs text-gray-200 placeholder:text-gray-600"
        />
        <span className="ml-auto text-xs text-gray-500">
          {total} freelancer{total === 1 ? '' : 's'}
        </span>
      </div>

      <BillingTable
        rows={rows}
        columns={columns}
        rowKey={(r) => r.user_id}
        isLoading={list.isLoading}
        isError={list.isError}
        emptyLabel="No freelancers match the current filters."
      />

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
