'use client'

import { useQuery } from '@tanstack/react-query'
import Link from 'next/link'
import { useParams } from 'next/navigation'
import { AlertTriangle, ArrowLeft, Building2, RefreshCw } from 'lucide-react'
import { billingInspectorApi } from '@/lib/api-client'
import { UsageGraph } from '../../components/UsageGraph'
import { AuditLogTable, type AuditRow } from '../../components/AuditLogTable'
import { BillingTable, type BillingTableColumn } from '../../components/BillingTable'

interface TenantProfile {
  tenant: {
    id: string
    name: string
    slug: string
    business_type: string
    email: string | null
    phone: string | null
    postcode: string
    is_active: boolean
    created_at: string | null
  }
  current_plan: {
    id: string
    name: string
    monthly_price_gbp: number
    max_users: number | null
    max_leads_per_month: number | null
    ai_lead_requests_per_month: number | null
  } | null
  usage: {
    seats: { used: number; limit: number | null }
    contacts: { used: number; limit: number | null }
  }
  subscription: {
    id: string
    status: string
    current_period_start: string | null
    current_period_end: string | null
    stripe_customer_id: string | null
    stripe_subscription_id: string | null
  } | null
  payment_method: string | null
  invoice_history: Array<{
    id: string
    amount_pence: number
    currency: string
    status: string
    period_start: string | null
    period_end: string | null
    invoice_pdf_url: string | null
    created_at: string | null
  }>
  overage_details: {
    alerts: string[]
    contacts: { used: number; limit: number | null; over: boolean }
    seats: { used: number; limit: number | null; over: boolean }
  }
  audit_trail: Array<{
    id: string
    action: string
    resource: string
    resource_id: string | null
    metadata: Record<string, unknown>
    created_at: string | null
  }>
  plan_alignment: {
    current_plan_id: string | null
    current_plan_name: string | null
    recommended_plan_id: string | null
    recommended_plan_name: string | null
    aligned: boolean
    reason: string | null
  }
}

function fmtPence(p: number): string {
  return `£${(p / 100).toFixed(2)}`
}

export default function TenantBillingProfilePage() {
  const { id } = useParams<{ id: string }>()
  const q = useQuery({
    queryKey: ['billing-inspector', 'tenant', id],
    queryFn: () => billingInspectorApi.tenantProfile(id).then((r) => r.data as TenantProfile),
    enabled: Boolean(id),
  })

  const invoiceCols: BillingTableColumn<TenantProfile['invoice_history'][number]>[] = [
    {
      key: 'id',
      header: 'Invoice',
      render: (i) => (
        <Link
          href={`/admin/billing-inspector/invoices/${i.id}`}
          className="font-mono text-xs text-amber-300 hover:underline"
        >
          {i.id.slice(0, 8)}…
        </Link>
      ),
    },
    { key: 'amount', header: 'Amount', align: 'right', render: (i) => fmtPence(i.amount_pence) },
    { key: 'status', header: 'Status', render: (i) => i.status },
    {
      key: 'period',
      header: 'Period',
      render: (i) => (
        <span className="text-xs text-gray-300">
          {i.period_start ? new Date(i.period_start).toLocaleDateString() : '—'} →{' '}
          {i.period_end ? new Date(i.period_end).toLocaleDateString() : '—'}
        </span>
      ),
    },
    {
      key: 'created',
      header: 'Created',
      render: (i) => (
        <span className="text-xs text-gray-400">
          {i.created_at ? new Date(i.created_at).toLocaleDateString() : '—'}
        </span>
      ),
    },
  ]

  const auditRows: AuditRow[] = (q.data?.audit_trail ?? []).map((a) => ({
    id: a.id,
    timestamp: a.created_at,
    type: a.action.toLowerCase().includes('plan')
      ? 'plan_change'
      : a.action.toLowerCase().includes('invoice')
      ? 'invoice_event'
      : a.action.toLowerCase().includes('overage')
      ? 'overage_flag'
      : 'other',
    entity_type: 'tenant',
    entity_id: q.data?.tenant.id ?? null,
    entity_name: q.data?.tenant.name ?? null,
    description: `${a.action} on ${a.resource}`,
    metadata: a.metadata,
  }))

  return (
    <div className="text-white">
      <div className="mb-4">
        <Link
          href="/admin/billing-inspector/tenants"
          className="inline-flex items-center gap-1.5 text-xs text-gray-400 hover:text-gray-200"
        >
          <ArrowLeft className="h-3.5 w-3.5" /> Back to tenants
        </Link>
      </div>

      <div className="mb-6 flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <Building2 className="h-6 w-6 text-amber-400" />
            {q.data?.tenant.name ?? 'Tenant'}
          </h1>
          {q.data ? (
            <p className="text-sm text-gray-400 mt-1">
              {q.data.tenant.business_type} · {q.data.tenant.postcode} · {q.data.tenant.email ?? '—'}
            </p>
          ) : null}
        </div>
        <button
          onClick={() => q.refetch()}
          className="inline-flex items-center gap-1.5 rounded-md border border-gray-700 bg-gray-900 px-3 py-1.5 text-xs text-gray-300 hover:bg-gray-800"
        >
          <RefreshCw className={`h-3.5 w-3.5 ${q.isFetching ? 'animate-spin' : ''}`} /> Recalculate Usage
        </button>
      </div>

      {q.isLoading ? (
        <div className="rounded-lg border border-gray-800 bg-gray-900 p-10 text-center text-gray-500">
          Loading tenant profile…
        </div>
      ) : q.isError ? (
        <div className="rounded-lg border border-red-900 bg-red-950/40 p-10 text-center text-red-300">
          Could not load tenant profile.
        </div>
      ) : q.data ? (
        <div className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
            <div className="rounded-lg border border-gray-800 bg-gray-900 p-5">
              <div className="text-[10px] uppercase tracking-widest text-gray-500 mb-3">Current plan</div>
              {q.data.current_plan ? (
                <>
                  <div className="text-lg font-semibold">{q.data.current_plan.name}</div>
                  <div className="mt-1 text-sm text-gray-400">
                    £{q.data.current_plan.monthly_price_gbp.toFixed(2)} / month
                  </div>
                  <div className="mt-3 text-xs text-gray-500">
                    Seats {q.data.current_plan.max_users ?? '∞'} · Leads/mo{' '}
                    {q.data.current_plan.max_leads_per_month ?? '∞'} · AI lead requests/mo{' '}
                    {q.data.current_plan.ai_lead_requests_per_month ?? 0}
                  </div>
                </>
              ) : (
                <div className="text-sm text-gray-500">No plan assigned.</div>
              )}
            </div>

            <div className="rounded-lg border border-gray-800 bg-gray-900 p-5">
              <div className="text-[10px] uppercase tracking-widest text-gray-500 mb-3">Usage vs plan</div>
              <UsageGraph
                rows={[
                  { label: 'Seats', used: q.data.usage.seats.used, limit: q.data.usage.seats.limit },
                  {
                    label: 'Contacts',
                    used: q.data.usage.contacts.used,
                    limit: q.data.usage.contacts.limit,
                  },
                ]}
              />
            </div>

            <div className="rounded-lg border border-gray-800 bg-gray-900 p-5">
              <div className="flex items-center justify-between mb-3">
                <div className="text-[10px] uppercase tracking-widest text-gray-500">Plan alignment</div>
                {q.data.plan_alignment.aligned ? (
                  <span className="rounded-full bg-emerald-500/15 px-2 py-0.5 text-[10px] uppercase text-emerald-300">
                    Aligned
                  </span>
                ) : (
                  <span className="rounded-full bg-amber-500/15 px-2 py-0.5 text-[10px] uppercase text-amber-300">
                    Review
                  </span>
                )}
              </div>
              <div className="text-sm text-gray-300">
                Current: <strong>{q.data.plan_alignment.current_plan_name ?? '—'}</strong>
              </div>
              <div className="text-sm text-gray-300">
                Recommended: <strong>{q.data.plan_alignment.recommended_plan_name ?? '—'}</strong>
              </div>
              {q.data.plan_alignment.reason ? (
                <div className="mt-2 text-xs text-gray-500">{q.data.plan_alignment.reason}</div>
              ) : null}
            </div>
          </div>

          <div className="rounded-lg border border-gray-800 bg-gray-900 p-5">
            <div className="flex items-center justify-between mb-3">
              <h2 className="text-sm font-semibold uppercase tracking-widest text-gray-400">
                Overage calculation
              </h2>
              {q.data.overage_details.alerts.length ? (
                <AlertTriangle className="h-3.5 w-3.5 text-amber-400" />
              ) : null}
            </div>
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <div className="text-[10px] uppercase tracking-widest text-gray-500">Contacts</div>
                <div className="text-white">
                  {q.data.overage_details.contacts.used} /{' '}
                  {q.data.overage_details.contacts.limit ?? '∞'}{' '}
                  {q.data.overage_details.contacts.over ? (
                    <span className="ml-1 text-amber-300">over</span>
                  ) : null}
                </div>
              </div>
              <div>
                <div className="text-[10px] uppercase tracking-widest text-gray-500">Seats</div>
                <div className="text-white">
                  {q.data.overage_details.seats.used} / {q.data.overage_details.seats.limit ?? '∞'}{' '}
                  {q.data.overage_details.seats.over ? (
                    <span className="ml-1 text-amber-300">over</span>
                  ) : null}
                </div>
              </div>
            </div>
            {q.data.overage_details.alerts.length ? (
              <div className="mt-3 flex flex-wrap gap-1">
                {q.data.overage_details.alerts.map((a) => (
                  <span
                    key={a}
                    className="inline-flex items-center rounded-full bg-amber-500/15 px-2 py-0.5 text-[10px] text-amber-300"
                  >
                    {a}
                  </span>
                ))}
              </div>
            ) : null}
          </div>

          <div className="rounded-lg border border-gray-800 bg-gray-900 p-5">
            <div className="text-[10px] uppercase tracking-widest text-gray-500 mb-2">
              Payment method on file
            </div>
            <div className="text-sm text-gray-200">{q.data.payment_method ?? '—'}</div>
            {q.data.subscription ? (
              <div className="mt-2 text-xs text-gray-500">
                Subscription · {q.data.subscription.status} · Period{' '}
                {q.data.subscription.current_period_start
                  ? new Date(q.data.subscription.current_period_start).toLocaleDateString()
                  : '—'}{' '}
                →{' '}
                {q.data.subscription.current_period_end
                  ? new Date(q.data.subscription.current_period_end).toLocaleDateString()
                  : '—'}
              </div>
            ) : null}
          </div>

          <div>
            <h2 className="text-sm font-semibold uppercase tracking-widest text-gray-400 mb-2">
              Invoice history
            </h2>
            <BillingTable
              rows={q.data.invoice_history}
              columns={invoiceCols}
              rowKey={(r) => r.id}
              emptyLabel="No invoices on file."
            />
          </div>

          <div>
            <h2 className="text-sm font-semibold uppercase tracking-widest text-gray-400 mb-2">
              Internal usage audit trail
            </h2>
            <AuditLogTable rows={auditRows} />
          </div>
        </div>
      ) : null}
    </div>
  )
}
