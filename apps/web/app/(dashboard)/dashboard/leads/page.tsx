'use client'

import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  leads,
  type LeadQuota,
  type LeadRequestItem,
  type TrialLeadStatus,
  type LeadSourceCatalog,
} from '@/lib/api-client'
import { formatDate } from '@/lib/utils'
import { toast } from 'sonner'
import {
  AlertCircle,
  ChevronLeft,
  ChevronRight,
  Inbox,
  Loader2,
  Send,
  X,
  CheckCircle2,
  Clock,
  XCircle,
} from 'lucide-react'

// ── Lead score badge ─────────────────────────────────────────────────────────
function LeadScoreBadge({
  score,
  label,
  reason,
}: {
  score?: number | null
  label?: string | null
  reason?: string | null
}) {
  if (score == null) return <span className="text-xs text-gray-300">—</span>
  const tier = (label || '').toLowerCase()
  const colour =
    tier === 'hot' || score >= 80
      ? 'bg-red-50 text-red-700 border-red-200'
      : tier === 'warm' || score >= 50
      ? 'bg-amber-50 text-amber-800 border-amber-200'
      : 'bg-brand-forest-800 text-brand-teal-100/70 border-brand-forest-700'
  return (
    <span
      title={reason || ''}
      className={`inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-xs font-semibold ${colour}`}
    >
      {score}
      {label && <span className="font-normal capitalize">· {label}</span>}
    </span>
  )
}

// ── Request status badge ──────────────────────────────────────────────────────
function RequestStatusBadge({ status }: { status: string }) {
  const map: Record<string, { label: string; className: string; Icon: any }> = {
    pending:   { label: 'Pending',   className: 'bg-amber-50 text-amber-700 border-amber-200',    Icon: Clock },
    approved:  { label: 'Approved',  className: 'bg-brand-teal-400/20 text-brand-teal-100 border-brand-teal-300/30',       Icon: CheckCircle2 },
    rejected:  { label: 'Rejected',  className: 'bg-red-50 text-red-700 border-red-200',          Icon: XCircle },
    fulfilled: { label: 'Fulfilled', className: 'bg-emerald-50 text-emerald-700 border-emerald-200', Icon: CheckCircle2 },
  }
  const t = map[status] || map.pending
  const { label, className, Icon } = t
  return (
    <span className={`inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-xs font-semibold ${className}`}>
      <Icon className="h-3 w-3" />
      {label}
    </span>
  )
}

// ── Quota banner ─────────────────────────────────────────────────────────────
function QuotaBanner({
  quota,
  onRequest,
}: {
  quota: LeadQuota
  onRequest: () => void
}) {
  const used = quota.requests_this_month
  const total = quota.plan_quota
  const pct = total > 0 ? Math.round((used / total) * 100) : 0

  if (total === 0) {
    return (
      <div className="flex items-start gap-3 rounded-xl border border-amber-300/40 bg-amber-950/50 px-4 py-3 text-sm text-amber-100">
        <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
        <div>
          <span className="font-semibold">Lead requests not included in your plan.</span>{' '}
          Upgrade to request AI-sourced leads each month.
        </div>
      </div>
    )
  }

  return (
    <div className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-brand-forest-700 bg-brand-forest-900 px-4 py-3 shadow-sm">
      <div className="space-y-1">
        <p className="text-sm font-semibold text-white">
          Lead requests — {quota.month_year}
        </p>
        <div className="flex items-center gap-3">
          <div className="h-2 w-48 overflow-hidden rounded-full bg-brand-forest-700">
            <div
              className="h-full rounded-full bg-brand-teal-300 transition-all"
              style={{ width: `${Math.min(100, pct)}%` }}
            />
          </div>
          <p className="text-xs text-brand-teal-100/75">
            {used} of {total} used · {quota.remaining} remaining
          </p>
        </div>
      </div>
      <button
        type="button"
        disabled={quota.remaining === 0}
        onClick={onRequest}
        className="inline-flex items-center gap-2 rounded-lg bg-brand-forest-700 px-4 py-2 text-sm font-semibold text-brand-forest-foreground hover:bg-brand-forest-800 disabled:cursor-not-allowed disabled:opacity-50"
      >
        <Send className="h-4 w-4" />
        Request Leads
      </button>
    </div>
  )
}

// ── Request modal ─────────────────────────────────────────────────────────────
function RequestLeadsModal({
  quota,
  onClose,
}: {
  quota: LeadQuota
  onClose: () => void
}) {
  const qc = useQueryClient()
  const [count, setCount] = useState(Math.min(quota.remaining, quota.plan_quota))
  const [notes, setNotes] = useState('')

  const submit = useMutation({
    mutationFn: () =>
      leads.submitRequest({ requested_count: count, tenant_notes: notes || null }),
    onSuccess: () => {
      toast.success('Lead request submitted — the team will review shortly.')
      qc.invalidateQueries({ queryKey: ['leads', 'quota'] })
      qc.invalidateQueries({ queryKey: ['leads', 'requests'] })
      onClose()
    },
    onError: (err: any) =>
      toast.error(err?.response?.data?.detail || 'Failed to submit request'),
  })

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div className="w-full max-w-md rounded-2xl border border-border bg-card shadow-2xl">
        <div className="flex items-center justify-between border-b border-border/50 px-6 py-4">
          <div>
            <h2 className="text-lg font-bold text-foreground">Request Leads</h2>
            <p className="mt-0.5 text-sm text-muted-foreground">
              {quota.remaining} request{quota.remaining !== 1 ? 's' : ''} remaining this month
            </p>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="rounded-md p-1.5 text-gray-400 hover:bg-gray-100"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <div className="space-y-4 px-6 py-5">
          <div>
            <label className="mb-1.5 block text-sm font-medium text-foreground/80">
              Number of leads to request
            </label>
            <input
              type="number"
              min={1}
              max={quota.remaining}
              value={count}
              onChange={(e) => setCount(Number(e.target.value))}
              className="w-full rounded-lg border border-border bg-background px-3 py-2 text-sm focus:border-brand-forest-400 focus:outline-none focus:ring-1 focus:ring-brand-forest-400/30"
            />
            <p className="mt-1 text-xs text-gray-400">
              Your plan allows up to {quota.plan_quota} per month.
            </p>
          </div>

          <div>
            <label className="mb-1.5 block text-sm font-medium text-foreground/80">
              Notes for our team{' '}
              <span className="font-normal text-gray-400">(optional)</span>
            </label>
            <textarea
              rows={3}
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="e.g. Plumbing enquiries in London, homeowners only"
              className="w-full rounded-lg border border-border bg-background px-3 py-2 text-sm focus:border-brand-forest-400 focus:outline-none focus:ring-1 focus:ring-brand-forest-400/30"
            />
          </div>
        </div>

        <div className="flex justify-end gap-2 border-t border-border/50 px-6 py-4">
          <button
            type="button"
            onClick={onClose}
            className="rounded-lg border border-border px-4 py-2 text-sm text-muted-foreground hover:bg-brand-forest-50"
          >
            Cancel
          </button>
          <button
            type="button"
            disabled={count < 1 || count > quota.remaining || submit.isPending}
            onClick={() => submit.mutate()}
            className="inline-flex items-center gap-2 rounded-lg bg-brand-forest-700 px-4 py-2 text-sm font-semibold text-brand-forest-foreground hover:bg-brand-forest-800 disabled:opacity-50"
          >
            {submit.isPending && <Loader2 className="h-4 w-4 animate-spin" />}
            Submit request
          </button>
        </div>
      </div>
    </div>
  )
}

// ── Request history ───────────────────────────────────────────────────────────
function RequestHistory({ requests }: { requests: LeadRequestItem[] }) {
  if (requests.length === 0) return null
  return (
    <section className="rounded-xl border border-brand-forest-800 bg-brand-forest-950">
      <div className="border-b border-brand-forest-800 px-5 py-3">
        <h3 className="text-sm font-semibold text-white">Your lead request history</h3>
      </div>
      <div className="divide-y divide-brand-forest-800">
        {requests.map((r) => (
          <div key={r.id} className="flex flex-wrap items-center justify-between gap-2 px-5 py-3">
            <div>
              <p className="text-sm font-medium text-white">
                {r.requested_count} leads · {r.month_year}
              </p>
              {r.tenant_notes && (
                <p className="mt-0.5 text-xs text-brand-teal-100/60">{r.tenant_notes}</p>
              )}
              {r.admin_notes && (
                <p className="mt-0.5 text-xs text-brand-teal-100">Admin: {r.admin_notes}</p>
              )}
            </div>
            <div className="flex items-center gap-3">
              {r.approved_count != null && r.status === 'approved' && (
                <span className="text-xs text-muted-foreground">{r.approved_count} approved</span>
              )}
              <RequestStatusBadge status={r.status} />
              <span className="text-xs text-brand-teal-100/60">{formatDate(r.created_at)}</span>
            </div>
          </div>
        ))}
      </div>
    </section>
  )
}

function TrialLeadsBanner({ trial }: { trial: TrialLeadStatus }) {
  if (!trial.in_trial) return null
  return (
    <div className="rounded-xl border border-brand-teal-400/30 bg-brand-teal-400/10 p-4">
      <p className="text-sm font-semibold text-white">
        Free lead trial — day {trial.trial_day} of {trial.trial_days_total}
      </p>
      <p className="mt-1 text-xs text-brand-teal-100/80">
        We auto-assign up to {trial.leads_per_day} leads per day matched to your trade and postcode.
        Today: {trial.delivered_today}/{trial.leads_per_day} delivered ({trial.remaining_today} remaining).
        Ends {new Date(trial.trial_ends_at).toLocaleDateString('en-GB')}.
      </p>
      {trial.trial_day >= 6 && (
        <p className="mt-2 text-xs text-amber-200">
          Auto-assignment ends soon. Upgrade to keep daily matched leads — check your email for details.
        </p>
      )}
    </div>
  )
}

function LeadSourcesCatalog({ catalog }: { catalog: LeadSourceCatalog }) {
  if (!catalog.sources?.length) return null
  return (
    <details className="rounded-xl border border-brand-forest-800 bg-brand-forest-950">
      <summary className="cursor-pointer px-5 py-3 text-sm font-semibold text-white">
        Lead sources for {catalog.trade_label} ({catalog.sources.length} platforms)
      </summary>
      <div className="divide-y divide-brand-forest-800 border-t border-brand-forest-800 max-h-64 overflow-y-auto">
        {catalog.sources.map((s, i) => (
          <div key={s.id || i} className="px-5 py-3 text-xs">
            <div className="flex flex-wrap items-center gap-2">
              <span className="font-medium text-brand-teal-100">{s.name}</span>
              <span className="rounded bg-brand-forest-800 px-1.5 py-0.5 text-brand-teal-100/70">
                {s.source_platform}
              </span>
              {s.is_catalog_default && (
                <span className="text-brand-teal-100/50">default</span>
              )}
            </div>
            <p className="mt-1 break-all text-brand-teal-100/60">{s.url_pattern}</p>
            {s.postcode_prefix && (
              <p className="mt-0.5 text-brand-teal-100/50">Geo: {s.postcode_prefix}</p>
            )}
          </div>
        ))}
      </div>
    </details>
  )
}

// ── Main page ─────────────────────────────────────────────────────────────────
export default function LeadsPage() {
  const [page, setPage] = useState(1)
  const [showModal, setShowModal] = useState(false)
  const qc = useQueryClient()

  const { data, isLoading } = useQuery({
    queryKey: ['leads', { page }],
    queryFn: () => leads.list({ page, page_size: 25 }).then((r) => r.data),
  })

  const { data: quota } = useQuery({
    queryKey: ['leads', 'quota'],
    queryFn: () => leads.getQuota().then((r) => r.data),
    retry: false,
  })

  const { data: requests } = useQuery({
    queryKey: ['leads', 'requests'],
    queryFn: () => leads.listRequests().then((r) => r.data),
    retry: false,
  })

  const { data: trial } = useQuery({
    queryKey: ['leads', 'trial-status'],
    queryFn: () => leads.trialStatus().then((r) => r.data),
    retry: false,
  })

  const { data: catalog } = useQuery({
    queryKey: ['leads', 'source-catalog'],
    queryFn: () => leads.sourceCatalog().then((r) => r.data),
    retry: false,
  })

  const convertMutation = useMutation({
    mutationFn: (id: string) => leads.convert(id),
    onSuccess: () => {
      toast.success('Lead converted to deal in pipeline!')
      qc.invalidateQueries({ queryKey: ['leads'] })
      qc.invalidateQueries({ queryKey: ['pipeline'] })
    },
    onError: () => toast.error('Failed to convert lead'),
  })

  return (
    <div className="space-y-5">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Leads</h1>
          <p className="text-sm text-muted-foreground">
            All incoming enquiries from your landing pages, forms, and referrals
          </p>
        </div>
        <span className="text-sm text-muted-foreground">{data?.total ?? 0} total</span>
      </div>

      {trial && <TrialLeadsBanner trial={trial} />}
      {catalog && <LeadSourcesCatalog catalog={catalog} />}

      {/* Quota banner */}
      {quota && (
        <QuotaBanner quota={quota} onRequest={() => setShowModal(true)} />
      )}

      {/* Lead table */}
      {isLoading ? (
        <div className="flex items-center justify-center py-20">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-brand-forest-700 border-t-transparent" />
        </div>
      ) : (
        <>
        <div className="space-y-3 md:hidden">
          {data?.items?.length === 0 && (
            <div className="rounded-xl border border-brand-forest-800 bg-brand-forest-950 px-4 py-10 text-center">
              <Inbox className="mx-auto mb-3 h-8 w-8 text-brand-teal-300/70" />
              <p className="text-sm text-brand-teal-100/60">
                No leads yet. Share your public form link or request leads above.
              </p>
            </div>
          )}
          {data?.items?.map((lead: any) => (
            <article key={lead.id} className="rounded-xl border border-brand-forest-800 bg-brand-forest-950 p-4 shadow-sm">
              <div className="flex items-start justify-between gap-3">
                <div className="min-w-0">
                  <h3 className="truncate font-semibold text-white">
                    {lead.first_name} {lead.last_name}
                  </h3>
                  <p className="mt-0.5 truncate text-xs text-brand-teal-100/70">
                    {lead.phone || lead.email || 'No contact supplied'}
                  </p>
                </div>
                <LeadScoreBadge score={lead.score} label={lead.score_label} reason={lead.score_reason} />
              </div>
              <div className="mt-3 grid grid-cols-2 gap-3 text-xs">
                <div>
                  <p className="text-brand-teal-100/50">Service</p>
                  <p className="mt-0.5 truncate text-brand-teal-50">{lead.service_needed || '—'}</p>
                </div>
                <div>
                  <p className="text-brand-teal-100/50">Source</p>
                  <p className="mt-0.5 truncate text-brand-teal-50">{lead.source}</p>
                </div>
                <div>
                  <p className="text-brand-teal-100/50">Date</p>
                  <p className="mt-0.5 text-brand-teal-50">{formatDate(lead.created_at)}</p>
                </div>
                <div>
                  <p className="text-brand-teal-100/50">Status</p>
                  <p className="mt-0.5 capitalize text-brand-teal-50">{lead.status}</p>
                </div>
              </div>
              {lead.status === 'new' && (
                <button
                  onClick={() => convertMutation.mutate(lead.id)}
                  disabled={convertMutation.isPending}
                  className="mt-4 w-full rounded-lg bg-brand-forest-700 px-3 py-2 text-xs font-semibold text-brand-forest-foreground hover:bg-brand-forest-800 disabled:opacity-50"
                >
                  Add to Pipeline
                </button>
              )}
            </article>
          ))}
          {(data?.total ?? 0) > 25 && (
            <div className="flex items-center justify-between rounded-xl border border-brand-forest-800 bg-brand-forest-950 px-4 py-3">
              <button
                disabled={page === 1}
                onClick={() => setPage((p) => p - 1)}
                className="inline-flex items-center gap-1 rounded-lg border border-brand-forest-700 px-3 py-1.5 text-xs text-brand-teal-100/70 hover:bg-brand-forest-900 disabled:opacity-40"
              >
                <ChevronLeft className="h-3.5 w-3.5" /> Previous
              </button>
              <span className="text-xs text-brand-teal-100/60">Page {page}</span>
              <button
                disabled={(data?.items?.length ?? 0) < 25}
                onClick={() => setPage((p) => p + 1)}
                className="inline-flex items-center gap-1 rounded-lg border border-brand-forest-700 px-3 py-1.5 text-xs text-brand-teal-100/70 hover:bg-brand-forest-900 disabled:opacity-40"
              >
                Next <ChevronRight className="h-3.5 w-3.5" />
              </button>
            </div>
          )}
        </div>
        <div className="hidden overflow-x-auto rounded-xl border border-brand-forest-800 bg-brand-forest-950 shadow-sm md:block">
          <table className="min-w-[920px] w-full text-sm">
            <thead className="border-b border-brand-forest-800 bg-brand-forest-900">
              <tr>
                {['Name', 'Contact', 'Service', 'Source', 'AI Score', 'Date', 'Status', ''].map(
                  (h) => (
                    <th
                      key={h}
                      className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wide text-brand-teal-100/75"
                    >
                      {h}
                    </th>
                  ),
                )}
              </tr>
            </thead>
            <tbody className="divide-y divide-brand-forest-800">
              {data?.items?.length === 0 && (
                <tr>
                  <td colSpan={8} className="px-4 py-12 text-center">
                    <Inbox className="mx-auto mb-3 h-8 w-8 text-brand-teal-300/70" />
                    <p className="text-brand-teal-100/60">
                      No leads yet. Share your public form link or request leads above.
                    </p>
                  </td>
                </tr>
              )}
              {data?.items?.map((lead: any) => (
                <tr key={lead.id} className="hover:bg-brand-forest-900">
                  <td className="px-4 py-3 font-medium text-white">
                    {lead.first_name} {lead.last_name}
                  </td>
                  <td className="px-4 py-3 text-brand-teal-100/70">{lead.phone || lead.email || '—'}</td>
                  <td className="px-4 py-3 text-brand-teal-100/70">{lead.service_needed || '—'}</td>
                  <td className="px-4 py-3">
                    <span className="rounded bg-brand-forest-800 px-2 py-0.5 text-xs text-brand-teal-100/75">
                      {lead.source}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <LeadScoreBadge
                      score={lead.score}
                      label={lead.score_label}
                      reason={lead.score_reason}
                    />
                  </td>
                  <td className="px-4 py-3 text-brand-teal-100/70">{formatDate(lead.created_at)}</td>
                  <td className="px-4 py-3">
                    <span
                      className={`rounded-full px-2 py-0.5 text-xs font-medium ${
                        lead.status === 'new'
                          ? 'bg-brand-teal-400/20 text-brand-teal-100 ring-1 ring-brand-teal-300/30'
                          : lead.status === 'in_crm'
                          ? 'bg-green-50 text-green-700'
                          : 'bg-gray-100 text-muted-foreground'
                      }`}
                    >
                      {lead.status}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    {lead.status === 'new' && (
                      <button
                        onClick={() => convertMutation.mutate(lead.id)}
                        disabled={convertMutation.isPending}
                        className="rounded-lg bg-brand-forest-700 px-3 py-1.5 text-xs text-brand-forest-foreground hover:bg-brand-forest-800 disabled:opacity-50"
                      >
                        Add to Pipeline
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          {/* Pagination */}
          {(data?.total ?? 0) > 25 && (
            <div className="flex items-center justify-between border-t border-border/50 px-5 py-3">
              <button
                disabled={page === 1}
                onClick={() => setPage((p) => p - 1)}
                className="inline-flex items-center gap-1 rounded-lg border border-brand-forest-700 px-3 py-1.5 text-xs text-brand-teal-100/70 hover:bg-brand-forest-900 disabled:opacity-40"
              >
                <ChevronLeft className="h-3.5 w-3.5" /> Previous
              </button>
              <span className="text-xs text-brand-teal-100/60">Page {page}</span>
              <button
                disabled={(data?.items?.length ?? 0) < 25}
                onClick={() => setPage((p) => p + 1)}
                className="inline-flex items-center gap-1 rounded-lg border border-brand-forest-700 px-3 py-1.5 text-xs text-brand-teal-100/70 hover:bg-brand-forest-900 disabled:opacity-40"
              >
                Next <ChevronRight className="h-3.5 w-3.5" />
              </button>
            </div>
          )}
        </div>
        </>
      )}

      {/* Request history */}
      {requests && <RequestHistory requests={requests} />}

      {/* Request modal */}
      {showModal && quota && (
        <RequestLeadsModal quota={quota} onClose={() => setShowModal(false)} />
      )}
    </div>
  )
}
