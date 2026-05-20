'use client'

import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import Link from 'next/link'
import { toast } from 'sonner'
import { Building2, ChevronLeft, ChevronRight, RefreshCw, Trash2 } from 'lucide-react'
import { admin, billingInspectorApi } from '@/lib/api-client'
import { BillingTable, type BillingTableColumn } from '../components/BillingTable'

interface TenantRow {
  tenant_id: string
  tenant_name: string
  plan_id: string | null
  plan_name: string | null
  monthly_price_gbp: number
  contacts_count: number
  active_seats: number
  last_invoice_status: string | null
  next_billing_date: string | null
  overage_alerts: string[]
}

interface TenantListResponse {
  items: TenantRow[]
  total: number
  page: number
  page_size: number
}

export default function BillingInspectorTenantsPage() {
  const qc = useQueryClient()
  const [page, setPage] = useState(1)
  const [pageSize] = useState(20)
  const [plan, setPlan] = useState<string>('')
  const [overage, setOverage] = useState<'' | 'any' | 'none'>('')
  const [invoiceStatus, setInvoiceStatus] = useState<string>('')

  const list = useQuery({
    queryKey: ['billing-inspector', 'tenants', page, pageSize, plan, overage, invoiceStatus],
    queryFn: () =>
      billingInspectorApi
        .listTenants({
          page,
          page_size: pageSize,
          plan: plan || undefined,
          overage_state: (overage || undefined) as 'any' | 'none' | undefined,
          invoice_status: invoiceStatus || undefined,
        })
        .then((r) => r.data as TenantListResponse),
  })

  const removeTenant = useMutation({
    mutationFn: (tenantId: string) => admin.deleteTenant(tenantId, true),
    onSuccess: async (res) => {
      toast.success((res.data as { message?: string }).message || 'Tenant deleted')
      await qc.refetchQueries({ queryKey: ['billing-inspector', 'tenants'] })
      qc.invalidateQueries({ queryKey: ['admin', 'tenants'] })
    },
    onError: (e: { response?: { data?: { detail?: string } } }) =>
      toast.error(e?.response?.data?.detail || 'Failed to delete tenant'),
  })

  const rows = list.data?.items ?? []
  const total = list.data?.total ?? 0
  const totalPages = Math.max(1, Math.ceil(total / pageSize))

  const columns: BillingTableColumn<TenantRow>[] = [
    {
      key: 'name',
      header: 'Tenant Name',
      render: (r) => (
        <Link
          href={`/admin/billing-inspector/tenants/${r.tenant_id}`}
          className="font-medium text-amber-300 hover:underline"
        >
          {r.tenant_name}
        </Link>
      ),
    },
    { key: 'plan', header: 'Current Plan', render: (r) => r.plan_name ?? <span className="text-gray-500">—</span> },
    {
      key: 'price',
      header: 'Monthly Price',
      align: 'right',
      render: (r) => `£${r.monthly_price_gbp.toFixed(2)}`,
    },
    {
      key: 'contacts',
      header: 'Contacts',
      align: 'right',
      render: (r) => r.contacts_count,
    },
    { key: 'seats', header: 'Active Seats', align: 'right', render: (r) => r.active_seats },
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
        <div className="inline-flex items-center justify-end gap-1.5">
          <Link
            href={`/admin/billing-inspector/tenants/${r.tenant_id}`}
            className="inline-flex items-center rounded-md border border-gray-700 bg-gray-900 px-2.5 py-1 text-xs text-gray-200 hover:bg-gray-800"
          >
            Inspect
          </Link>
          <button
            type="button"
            disabled={removeTenant.isPending}
            onClick={() => {
              if (
                !confirm(
                  `PERMANENTLY delete "${r.tenant_name}" and all workspace data? This cannot be undone.`,
                )
              )
                return
              removeTenant.mutate(r.tenant_id)
            }}
            className="inline-flex items-center gap-1 rounded-md border border-red-900/50 bg-red-950/40 px-2.5 py-1 text-xs text-red-400 hover:bg-red-950/60 disabled:opacity-50"
          >
            <Trash2 className="h-3 w-3" /> Delete
          </button>
        </div>
      ),
    },
  ]

  return (
    <div className="text-white">
      <div className="mb-6 flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <Building2 className="h-6 w-6 text-amber-400" /> Tenants Billing
          </h1>
          <p className="text-sm text-gray-400 mt-1">
            Inspect each tenant&apos;s plan, usage, and invoice status.
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
        <input
          value={plan}
          onChange={(e) => {
            setPage(1)
            setPlan(e.target.value)
          }}
          placeholder="Filter by plan name"
          className="rounded-md border border-gray-700 bg-gray-950 px-2.5 py-1 text-xs text-gray-200 placeholder:text-gray-600"
        />
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
          {total} tenant{total === 1 ? '' : 's'}
        </span>
      </div>

      <BillingTable
        rows={rows}
        columns={columns}
        rowKey={(r) => r.tenant_id}
        isLoading={list.isLoading}
        isError={list.isError}
        emptyLabel="No tenants match the current filters."
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
