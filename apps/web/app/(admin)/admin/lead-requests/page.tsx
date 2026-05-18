'use client'

import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  CheckCircle2,
  Clock,
  RefreshCw,
  XCircle,
  CheckCheck,
} from 'lucide-react'
import { toast } from 'sonner'

import { admin, type LeadRequestItem } from '@/lib/api-client'

const STATUS_FILTERS = [
  { value: '', label: 'All' },
  { value: 'pending', label: 'Pending' },
  { value: 'approved', label: 'Approved' },
  { value: 'fulfilled', label: 'Fulfilled' },
  { value: 'rejected', label: 'Rejected' },
]

function StatusPill({ status }: { status: string }) {
  const map: Record<string, { label: string; cls: string }> = {
    pending:   { label: 'Pending',   cls: 'bg-amber-500/15 text-amber-300 border-amber-500/30' },
    approved:  { label: 'Approved',  cls: 'bg-blue-500/15 text-blue-300 border-blue-500/30' },
    rejected:  { label: 'Rejected',  cls: 'bg-red-500/15 text-red-300 border-red-500/30' },
    fulfilled: { label: 'Fulfilled', cls: 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30' },
  }
  const t = map[status] || map.pending
  return (
    <span
      className={`inline-flex items-center rounded border px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider ${t.cls}`}
    >
      {t.label}
    </span>
  )
}

function ActionRow({ req }: { req: LeadRequestItem }) {
  const qc = useQueryClient()
  const [approveCount, setApproveCount] = useState<number>(req.requested_count)
  const [adminNotes, setAdminNotes] = useState('')
  const [expanded, setExpanded] = useState(false)

  const invalidate = () => qc.invalidateQueries({ queryKey: ['admin', 'lead-requests'] })

  const approve = useMutation({
    mutationFn: () =>
      admin.approveLeadRequest(req.id, {
        approved_count: approveCount,
        admin_notes: adminNotes || undefined,
      }),
    onSuccess: () => { toast.success('Request approved'); invalidate() },
    onError: (e: any) => toast.error(e?.response?.data?.detail || 'Failed'),
  })

  const reject = useMutation({
    mutationFn: () =>
      admin.rejectLeadRequest(req.id, { admin_notes: adminNotes || undefined }),
    onSuccess: () => { toast.success('Request rejected'); invalidate() },
    onError: (e: any) => toast.error(e?.response?.data?.detail || 'Failed'),
  })

  const fulfill = useMutation({
    mutationFn: () =>
      admin.fulfillLeadRequest(req.id, { admin_notes: adminNotes || undefined }),
    onSuccess: () => { toast.success('Marked as fulfilled'); invalidate() },
    onError: (e: any) => toast.error(e?.response?.data?.detail || 'Failed'),
  })

  const isPending = approve.isPending || reject.isPending || fulfill.isPending

  return (
    <>
      <tr
        className="cursor-pointer hover:bg-gray-800/40"
        onClick={() => setExpanded((v) => !v)}
      >
        <td className="px-4 py-3 font-mono text-xs text-gray-400">{req.tenant_id.slice(0, 8)}…</td>
        <td className="px-4 py-3 text-sm font-medium text-gray-100">{req.requested_count}</td>
        <td className="px-4 py-3 text-xs text-gray-400">{req.month_year}</td>
        <td className="px-4 py-3">
          <StatusPill status={req.status} />
        </td>
        <td className="px-4 py-3 text-xs text-gray-400">{req.tenant_notes || '—'}</td>
        <td className="px-4 py-3 text-xs text-gray-500">
          {new Date(req.created_at).toLocaleDateString('en-GB')}
        </td>
        <td className="px-4 py-3 text-right">
          {req.status === 'pending' && (
            <span className="text-xs text-amber-400">Action needed</span>
          )}
          {req.status === 'approved' && (
            <span className="text-xs text-blue-400">Ready to fulfill</span>
          )}
        </td>
      </tr>

      {expanded && (
        <tr className="bg-gray-950/60">
          <td colSpan={7} className="px-4 py-4">
            <div className="grid gap-4 md:grid-cols-2">
              {req.status === 'pending' && (
                <>
                  <div>
                    <label className="mb-1 block text-xs font-medium text-gray-400">
                      Approved lead count
                    </label>
                    <input
                      type="number"
                      min={0}
                      max={req.requested_count}
                      value={approveCount}
                      onChange={(e) => setApproveCount(Number(e.target.value))}
                      className="w-full rounded-md border border-gray-700 bg-gray-950 px-3 py-2 text-sm text-gray-100"
                    />
                  </div>
                  <div>
                    <label className="mb-1 block text-xs font-medium text-gray-400">
                      Admin notes
                    </label>
                    <input
                      value={adminNotes}
                      onChange={(e) => setAdminNotes(e.target.value)}
                      placeholder="Optional note to tenant"
                      className="w-full rounded-md border border-gray-700 bg-gray-950 px-3 py-2 text-sm text-gray-100"
                    />
                  </div>
                </>
              )}
              {req.admin_notes && (
                <div className="md:col-span-2">
                  <p className="text-xs text-gray-400">
                    Admin notes: <span className="text-gray-200">{req.admin_notes}</span>
                  </p>
                </div>
              )}
            </div>

            <div className="mt-4 flex flex-wrap gap-2">
              {req.status === 'pending' && (
                <>
                  <button
                    type="button"
                    disabled={isPending}
                    onClick={(e) => { e.stopPropagation(); approve.mutate() }}
                    className="inline-flex items-center gap-1.5 rounded-lg border border-emerald-500/40 bg-emerald-500/10 px-3 py-1.5 text-xs font-semibold text-emerald-300 hover:bg-emerald-500/20 disabled:opacity-50"
                  >
                    <CheckCircle2 className="h-3.5 w-3.5" />
                    Approve
                  </button>
                  <button
                    type="button"
                    disabled={isPending}
                    onClick={(e) => { e.stopPropagation(); reject.mutate() }}
                    className="inline-flex items-center gap-1.5 rounded-lg border border-red-500/40 bg-red-500/10 px-3 py-1.5 text-xs font-semibold text-red-300 hover:bg-red-500/20 disabled:opacity-50"
                  >
                    <XCircle className="h-3.5 w-3.5" />
                    Reject
                  </button>
                </>
              )}
              {req.status === 'approved' && (
                <button
                  type="button"
                  disabled={isPending}
                  onClick={(e) => { e.stopPropagation(); fulfill.mutate() }}
                  className="inline-flex items-center gap-1.5 rounded-lg border border-blue-500/40 bg-blue-500/10 px-3 py-1.5 text-xs font-semibold text-blue-300 hover:bg-blue-500/20 disabled:opacity-50"
                >
                  <CheckCheck className="h-3.5 w-3.5" />
                  Mark fulfilled
                </button>
              )}
            </div>
          </td>
        </tr>
      )}
    </>
  )
}

export default function AdminLeadRequestsPage() {
  const [statusFilter, setStatusFilter] = useState('')
  const qc = useQueryClient()

  const { data, isLoading, error, refetch, isFetching } = useQuery({
    queryKey: ['admin', 'lead-requests', statusFilter],
    queryFn: () =>
      admin.listLeadRequests(statusFilter || undefined).then((r) => r.data),
  })

  const pending = data?.filter((r) => r.status === 'pending').length ?? 0

  return (
    <div className="space-y-6">
      <header className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Lead Requests</h1>
          <p className="mt-1 text-gray-400">
            Tenant requests for AI-sourced leads. Review, approve, and mark fulfilled.
          </p>
        </div>
        <div className="flex items-center gap-3">
          {pending > 0 && (
            <span className="rounded-full border border-amber-500/40 bg-amber-500/15 px-3 py-1 text-sm font-semibold text-amber-300">
              {pending} pending action
            </span>
          )}
          <button
            type="button"
            onClick={() => refetch()}
            disabled={isFetching}
            className="inline-flex items-center gap-1.5 rounded-lg border border-gray-700 px-3 py-1.5 text-xs text-gray-300 hover:bg-gray-800"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${isFetching ? 'animate-spin' : ''}`} />
            Refresh
          </button>
        </div>
      </header>

      {/* Status filter tabs */}
      <div className="flex flex-wrap gap-1 rounded-lg border border-gray-800 bg-gray-900 p-1">
        {STATUS_FILTERS.map((f) => (
          <button
            key={f.value}
            type="button"
            onClick={() => setStatusFilter(f.value)}
            className={`rounded-md px-3 py-1.5 text-xs font-semibold transition-colors ${
              statusFilter === f.value
                ? 'bg-amber-500/15 text-amber-300'
                : 'text-gray-400 hover:bg-gray-800 hover:text-white'
            }`}
          >
            {f.label}
          </button>
        ))}
      </div>

      {error && (
        <div className="rounded-xl border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-300">
          Failed to load lead requests.
        </div>
      )}

      <div className="overflow-x-auto rounded-xl border border-gray-800">
        <table className="min-w-[920px] w-full text-sm">
          <thead className="bg-gray-950 text-xs uppercase tracking-wider text-gray-500">
            <tr>
              <th className="px-4 py-3 text-left font-semibold">Tenant</th>
              <th className="px-4 py-3 text-left font-semibold">Count</th>
              <th className="px-4 py-3 text-left font-semibold">Month</th>
              <th className="px-4 py-3 text-left font-semibold">Status</th>
              <th className="px-4 py-3 text-left font-semibold">Notes</th>
              <th className="px-4 py-3 text-left font-semibold">Submitted</th>
              <th className="px-4 py-3 text-right font-semibold"></th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-800">
            {isLoading &&
              [0, 1, 2].map((i) => (
                <tr key={i}>
                  <td colSpan={7} className="px-4 py-4">
                    <div className="h-5 animate-pulse rounded bg-gray-800" />
                  </td>
                </tr>
              ))}
            {!isLoading && data?.length === 0 && (
              <tr>
                <td colSpan={7} className="px-4 py-10 text-center text-sm text-gray-500">
                  No lead requests found.
                </td>
              </tr>
            )}
            {data?.map((req) => (
              <ActionRow key={req.id} req={req} />
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
