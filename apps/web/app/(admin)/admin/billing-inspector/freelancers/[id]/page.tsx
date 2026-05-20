'use client'

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import Link from 'next/link'
import { useParams, useRouter } from 'next/navigation'
import { toast } from 'sonner'
import { ArrowLeft, Briefcase, RefreshCw, Trash2 } from 'lucide-react'
import { admin, billingInspectorApi } from '@/lib/api-client'
import { AuditLogTable, type AuditRow } from '../../components/AuditLogTable'

interface FreelancerProfile {
  freelancer: {
    id: string
    full_name: string
    email: string
    phone: string | null
    managed_clients_signup: number | null
    created_at: string | null
  }
  managed_clients_count: number
  auto_calculated_plan: {
    tier: '1-50' | '51-100' | '>100'
    calculated_price_gbp: number
    override_price_gbp: number | null
    effective_price_gbp: number
    calculation_source: string
  } | null
  auto_upgrade_logic: {
    tier_1_50_gbp: number
    tier_51_100_gbp: number
    tier_over_100_base_gbp: number
    per_extra_client_gbp: number
    notes: string
  }
  invoice_history: unknown[]
  payment_method: string | null
  usage_records: Array<{
    id: string
    action: string
    resource: string
    metadata: Record<string, unknown>
    created_at: string | null
  }>
}

export default function FreelancerBillingProfilePage() {
  const { id } = useParams<{ id: string }>()
  const router = useRouter()
  const qc = useQueryClient()
  const q = useQuery({
    queryKey: ['billing-inspector', 'freelancer', id],
    queryFn: () => billingInspectorApi.freelancerProfile(id).then((r) => r.data as FreelancerProfile),
    enabled: Boolean(id),
  })

  const auditRows: AuditRow[] = (q.data?.usage_records ?? []).map((a) => ({
    id: a.id,
    timestamp: a.created_at,
    type: a.action.toLowerCase().includes('plan')
      ? 'plan_change'
      : a.action.toLowerCase().includes('invoice')
      ? 'invoice_event'
      : a.action.toLowerCase().includes('overage')
      ? 'overage_flag'
      : 'other',
    entity_type: 'freelancer',
    entity_id: q.data?.freelancer.id ?? null,
    entity_name: q.data?.freelancer.full_name ?? null,
    description: `${a.action} on ${a.resource}`,
    metadata: a.metadata,
  }))

  return (
    <div className="text-white">
      <div className="mb-4">
        <Link
          href="/admin/billing-inspector/freelancers"
          className="inline-flex items-center gap-1.5 text-xs text-gray-400 hover:text-gray-200"
        >
          <ArrowLeft className="h-3.5 w-3.5" /> Back to freelancers
        </Link>
      </div>

      <div className="mb-6 flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <Briefcase className="h-6 w-6 text-amber-400" />
            {q.data?.freelancer.full_name ?? 'Freelancer'}
          </h1>
          {q.data ? (
            <p className="text-sm text-gray-400 mt-1">
              {q.data.freelancer.email} · joined{' '}
              {q.data.freelancer.created_at
                ? new Date(q.data.freelancer.created_at).toLocaleDateString()
                : '—'}
            </p>
          ) : null}
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => q.refetch()}
            className="inline-flex items-center gap-1.5 rounded-md border border-gray-700 bg-gray-900 px-3 py-1.5 text-xs text-gray-300 hover:bg-gray-800"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${q.isFetching ? 'animate-spin' : ''}`} /> Refresh
          </button>
          {q.data ? (
            <button
              type="button"
              disabled={removeFreelancer.isPending}
              onClick={() => {
                if (
                  !confirm(
                    `Delete freelancer "${q.data!.freelancer.full_name}"? They will lose sign-in access and managed clients will be archived.`,
                  )
                )
                  return
                removeFreelancer.mutate()
              }}
              className="inline-flex items-center gap-1.5 rounded-md border border-red-900/50 bg-red-950/40 px-3 py-1.5 text-xs text-red-400 hover:bg-red-950/60 disabled:opacity-50"
            >
              <Trash2 className="h-3.5 w-3.5" /> Delete
            </button>
          ) : null}
        </div>
      </div>

      {q.isLoading ? (
        <div className="rounded-lg border border-gray-800 bg-gray-900 p-10 text-center text-gray-500">
          Loading freelancer profile…
        </div>
      ) : q.isError ? (
        <div className="rounded-lg border border-red-900 bg-red-950/40 p-10 text-center text-red-300">
          Could not load freelancer profile.
        </div>
      ) : q.data ? (
        <div className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
            <div className="rounded-lg border border-gray-800 bg-gray-900 p-5">
              <div className="text-[10px] uppercase tracking-widest text-gray-500 mb-3">Managed clients</div>
              <div className="text-3xl font-bold tabular-nums">{q.data.managed_clients_count}</div>
              {q.data.freelancer.managed_clients_signup != null ? (
                <div className="mt-1 text-xs text-gray-500">
                  At signup: {q.data.freelancer.managed_clients_signup}
                </div>
              ) : null}
            </div>

            <div className="rounded-lg border border-gray-800 bg-gray-900 p-5">
              <div className="text-[10px] uppercase tracking-widest text-gray-500 mb-3">Auto-computed plan</div>
              {q.data.auto_calculated_plan ? (
                <>
                  <div className="text-sm text-gray-300">
                    Tier: <strong>{q.data.auto_calculated_plan.tier}</strong>
                  </div>
                  <div className="text-sm text-gray-300">
                    Calculated: <strong>£{q.data.auto_calculated_plan.calculated_price_gbp.toFixed(2)}</strong>
                  </div>
                  <div className="text-sm text-gray-300">
                    Override:{' '}
                    <strong>
                      {q.data.auto_calculated_plan.override_price_gbp != null
                        ? `£${q.data.auto_calculated_plan.override_price_gbp.toFixed(2)}`
                        : '—'}
                    </strong>
                  </div>
                  <div className="mt-2 flex items-center justify-between">
                    <span className="text-xs text-gray-500">Effective</span>
                    <span className="text-lg font-bold tabular-nums">
                      £{q.data.auto_calculated_plan.effective_price_gbp.toFixed(2)}
                    </span>
                  </div>
                  <div className="mt-1 text-[10px] uppercase tracking-widest text-gray-500">
                    Source: {q.data.auto_calculated_plan.calculation_source}
                  </div>
                </>
              ) : (
                <div className="text-sm text-gray-500">No billing snapshot.</div>
              )}
            </div>

            <div className="rounded-lg border border-gray-800 bg-gray-900 p-5">
              <div className="text-[10px] uppercase tracking-widest text-gray-500 mb-3">
                Auto-upgrade logic
              </div>
              <ul className="text-xs text-gray-300 space-y-1">
                <li>1–50 clients · £{q.data.auto_upgrade_logic.tier_1_50_gbp}/month</li>
                <li>51–100 clients · £{q.data.auto_upgrade_logic.tier_51_100_gbp}/month</li>
                <li>
                  &gt;100 clients · base £{q.data.auto_upgrade_logic.tier_over_100_base_gbp} + £
                  {q.data.auto_upgrade_logic.per_extra_client_gbp}/extra client
                </li>
              </ul>
              <div className="mt-3 text-[11px] text-gray-500">{q.data.auto_upgrade_logic.notes}</div>
            </div>
          </div>

          <div className="rounded-lg border border-gray-800 bg-gray-900 p-5">
            <div className="text-[10px] uppercase tracking-widest text-gray-500 mb-2">Payment method</div>
            <div className="text-sm text-gray-300">{q.data.payment_method ?? '—'}</div>
          </div>

          <div>
            <h2 className="text-sm font-semibold uppercase tracking-widest text-gray-400 mb-2">
              Invoice history
            </h2>
            {q.data.invoice_history.length === 0 ? (
              <div className="rounded-lg border border-gray-800 bg-gray-900 p-6 text-center text-sm text-gray-500">
                No invoices on file for freelancers (invoicing flow runs separately).
              </div>
            ) : (
              <pre className="overflow-auto rounded-lg border border-gray-800 bg-gray-950 p-3 text-[11px] text-gray-300">
                {JSON.stringify(q.data.invoice_history, null, 2)}
              </pre>
            )}
          </div>

          <div>
            <h2 className="text-sm font-semibold uppercase tracking-widest text-gray-400 mb-2">
              Verifiable usage records
            </h2>
            <AuditLogTable rows={auditRows} />
          </div>
        </div>
      ) : null}
    </div>
  )
}
