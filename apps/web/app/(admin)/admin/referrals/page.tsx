'use client'

import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  Users,
  Gift,
  DollarSign,
  TrendingUp,
  Plus,
  Edit2,
  Trash2,
  CheckCircle2,
  XCircle,
  ChevronDown,
  ChevronUp,
  RefreshCw,
  Link2,
  AlertCircle,
  BarChart2,
  Copy,
  ExternalLink,
} from 'lucide-react'
import { toast } from 'sonner'
import { referrals } from '@/lib/api-client'

// ─── types ────────────────────────────────────────────────────────────────────

interface Program {
  id: string
  type: string
  status: string
  reward_amount: number
  reward_type: string
  reward_delivery_method: string
  rules: Record<string, unknown>
  created_at: string
}

interface ReferralEvent {
  id: string
  ref_code: string
  status: string
  created_at: string
  tenant_id?: string
}

interface Payout {
  id: string
  event_id: string
  amount: number
  payout_method: string
  status: string
  created_at: string
}

const TAB_IDS = ['overview', 'programs', 'events', 'payouts'] as const
type Tab = (typeof TAB_IDS)[number]

// ─── helpers ──────────────────────────────────────────────────────────────────

function fmt(d: string) {
  return new Date(d).toLocaleDateString('en-GB', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
  })
}

function StatusBadge({ status }: { status: string }) {
  const map: Record<string, string> = {
    active: 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30',
    pending_approval: 'bg-amber-500/15 text-amber-300 border-amber-500/30',
    pending: 'bg-amber-500/15 text-amber-300 border-amber-500/30',
    rejected: 'bg-red-500/15 text-red-300 border-red-500/30',
    paid: 'bg-blue-500/15 text-blue-300 border-blue-500/30',
    global_saas: 'bg-purple-500/15 text-purple-300 border-purple-500/30',
  }
  const cls = map[status] ?? 'bg-gray-500/15 text-gray-300 border-gray-500/30'
  return (
    <span
      className={`inline-flex items-center rounded border px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider ${cls}`}
    >
      {status.replace(/_/g, ' ')}
    </span>
  )
}

// ─── Modal ────────────────────────────────────────────────────────────────────

function Modal({
  title,
  onClose,
  children,
}: {
  title: string
  onClose: () => void
  children: React.ReactNode
}) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4 backdrop-blur-sm">
      <div className="w-full max-w-lg rounded-2xl border border-gray-800 bg-gray-950 shadow-2xl">
        <div className="flex items-center justify-between border-b border-gray-800 px-6 py-4">
          <h3 className="text-base font-semibold text-white">{title}</h3>
          <button onClick={onClose} className="rounded-md p-1 text-gray-500 hover:bg-gray-800 hover:text-white">
            <XCircle className="h-4 w-4" />
          </button>
        </div>
        <div className="p-6">{children}</div>
      </div>
    </div>
  )
}

// ─── Create / Edit Program Modal ──────────────────────────────────────────────

function ProgramModal({
  initial,
  onClose,
}: {
  initial?: Program
  onClose: () => void
}) {
  const qc = useQueryClient()
  const [type, setType] = useState(initial?.type ?? 'global_saas')
  const [rewardAmount, setRewardAmount] = useState(String(initial?.reward_amount ?? 10))
  const [rewardType, setRewardType] = useState(initial?.reward_type ?? 'percentage')
  const [deliveryMethod, setDeliveryMethod] = useState(initial?.reward_delivery_method ?? 'payout')

  const save = useMutation({
    mutationFn: () =>
      referrals.createProgram({
        type,
        reward_amount: parseFloat(rewardAmount),
        reward_type: rewardType,
        reward_delivery_method: deliveryMethod,
        rules: {
          activation_status: 'active',
          commission_structure: rewardType,
          payout_mode: 'monthly',
          partner_tiers: [],
        },
      }),
    onSuccess: () => {
      toast.success(initial ? 'Program updated' : 'Program created')
      qc.invalidateQueries({ queryKey: ['admin', 'referrals', 'programs'] })
      onClose()
    },
    onError: (e: any) => toast.error(e?.response?.data?.detail || 'Failed to save program'),
  })

  return (
    <Modal title={initial ? 'Edit Program' : 'Create Referral Program'} onClose={onClose}>
      <div className="space-y-4">
        <div>
          <label className="mb-1.5 block text-xs font-medium text-gray-400">Program Type</label>
          <select
            value={type}
            onChange={(e) => setType(e.target.value)}
            className="w-full rounded-lg border border-gray-700 bg-gray-900 px-3 py-2 text-sm text-gray-100 focus:outline-none focus:ring-2 focus:ring-amber-500/40"
          >
            <option value="global_saas">Global SaaS (CustomerFlow referral)</option>
            <option value="tradesman_to_client">Tradesman → Client</option>
            <option value="partner">Partner / Agency</option>
          </select>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="mb-1.5 block text-xs font-medium text-gray-400">Reward Amount</label>
            <input
              type="number"
              min={0}
              value={rewardAmount}
              onChange={(e) => setRewardAmount(e.target.value)}
              className="w-full rounded-lg border border-gray-700 bg-gray-900 px-3 py-2 text-sm text-gray-100 focus:outline-none focus:ring-2 focus:ring-amber-500/40"
            />
          </div>
          <div>
            <label className="mb-1.5 block text-xs font-medium text-gray-400">Reward Type</label>
            <select
              value={rewardType}
              onChange={(e) => setRewardType(e.target.value)}
              className="w-full rounded-lg border border-gray-700 bg-gray-900 px-3 py-2 text-sm text-gray-100 focus:outline-none focus:ring-2 focus:ring-amber-500/40"
            >
              <option value="percentage">Percentage (%)</option>
              <option value="fixed">Fixed (£)</option>
              <option value="credits">Platform Credits</option>
            </select>
          </div>
        </div>

        <div>
          <label className="mb-1.5 block text-xs font-medium text-gray-400">Delivery Method</label>
          <select
            value={deliveryMethod}
            onChange={(e) => setDeliveryMethod(e.target.value)}
            className="w-full rounded-lg border border-gray-700 bg-gray-900 px-3 py-2 text-sm text-gray-100 focus:outline-none focus:ring-2 focus:ring-amber-500/40"
          >
            <option value="payout">Bank Payout</option>
            <option value="credit">Account Credit</option>
            <option value="voucher">Voucher Code</option>
          </select>
        </div>

        <div className="flex justify-end gap-3 pt-2">
          <button
            type="button"
            onClick={onClose}
            className="rounded-lg border border-gray-700 px-4 py-2 text-sm text-gray-300 hover:bg-gray-800"
          >
            Cancel
          </button>
          <button
            type="button"
            disabled={save.isPending}
            onClick={() => save.mutate()}
            className="rounded-lg bg-amber-500 px-4 py-2 text-sm font-semibold text-black hover:bg-amber-400 disabled:opacity-50"
          >
            {save.isPending ? 'Saving…' : initial ? 'Save Changes' : 'Create Program'}
          </button>
        </div>
      </div>
    </Modal>
  )
}

// ─── Approve / Reject Modal ───────────────────────────────────────────────────

function ApprovalModal({
  program,
  action,
  onClose,
}: {
  program: Program
  action: 'approve' | 'reject'
  onClose: () => void
}) {
  const qc = useQueryClient()
  const [amount, setAmount] = useState(String(program.reward_amount))
  const [reason, setReason] = useState('')

  const mut = useMutation({
    mutationFn: () =>
      action === 'approve'
        ? referrals.approveProgram(program.id, {
            reward_amount: parseFloat(amount) || null,
            reason: reason || null,
          })
        : referrals.rejectProgram(program.id, { reason: reason || null }),
    onSuccess: () => {
      toast.success(action === 'approve' ? 'Program approved' : 'Program rejected')
      qc.invalidateQueries({ queryKey: ['admin', 'referrals', 'programs'] })
      onClose()
    },
    onError: (e: any) => toast.error(e?.response?.data?.detail || 'Action failed'),
  })

  return (
    <Modal title={action === 'approve' ? 'Approve Program' : 'Reject Program'} onClose={onClose}>
      <div className="space-y-4">
        <p className="text-sm text-gray-400">
          Program ID: <span className="font-mono text-gray-300">{program.id.slice(0, 12)}…</span>
        </p>
        {action === 'approve' && (
          <div>
            <label className="mb-1.5 block text-xs font-medium text-gray-400">
              Override reward amount (optional)
            </label>
            <input
              type="number"
              value={amount}
              onChange={(e) => setAmount(e.target.value)}
              className="w-full rounded-lg border border-gray-700 bg-gray-900 px-3 py-2 text-sm text-gray-100"
            />
          </div>
        )}
        <div>
          <label className="mb-1.5 block text-xs font-medium text-gray-400">Reason / notes</label>
          <textarea
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            rows={3}
            className="w-full resize-none rounded-lg border border-gray-700 bg-gray-900 px-3 py-2 text-sm text-gray-100"
          />
        </div>
        <div className="flex justify-end gap-3 pt-2">
          <button onClick={onClose} className="rounded-lg border border-gray-700 px-4 py-2 text-sm text-gray-300 hover:bg-gray-800">
            Cancel
          </button>
          <button
            disabled={mut.isPending}
            onClick={() => mut.mutate()}
            className={`rounded-lg px-4 py-2 text-sm font-semibold disabled:opacity-50 ${
              action === 'approve'
                ? 'bg-emerald-600 text-white hover:bg-emerald-500'
                : 'bg-red-600 text-white hover:bg-red-500'
            }`}
          >
            {mut.isPending ? 'Processing…' : action === 'approve' ? 'Approve' : 'Reject'}
          </button>
        </div>
      </div>
    </Modal>
  )
}

// ─── Programs Tab ─────────────────────────────────────────────────────────────

function ProgramsTab() {
  const [createOpen, setCreateOpen] = useState(false)
  const [approvalModal, setApprovalModal] = useState<{ program: Program; action: 'approve' | 'reject' } | null>(null)
  const [expanded, setExpanded] = useState<string | null>(null)

  // Fetch a "global" program list — we generate one for demo if API doesn't support list yet
  const { data, isLoading, error, refetch } = useQuery<Program[]>({
    queryKey: ['admin', 'referrals', 'programs'],
    queryFn: async () => {
      // The current referrals API doesn't have a list endpoint yet — return empty until one is added
      return []
    },
    staleTime: 30_000,
  })

  const createGlobal = useMutation({
    mutationFn: () =>
      referrals.createProgram({
        type: 'global_saas',
        reward_amount: 10,
        reward_type: 'percentage',
        reward_delivery_method: 'payout',
        rules: {
          activation_status: 'active',
          commission_structure: 'percentage',
          payout_mode: 'monthly',
          partner_tiers: [],
        },
      }),
    onSuccess: (r: any) => {
      toast.success(`Global program created (ID: ${r.data?.id?.slice(0, 8)}…)`)
      refetch()
    },
    onError: (e: any) => toast.error(e?.response?.data?.detail || 'Create failed'),
  })

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <p className="text-sm text-gray-400">
          Manage tradesman referral programs and the global SaaS referral program.
        </p>
        <div className="flex gap-2">
          <button
            type="button"
            disabled={createGlobal.isPending}
            onClick={() => createGlobal.mutate()}
            className="inline-flex items-center gap-1.5 rounded-lg border border-purple-500/40 bg-purple-500/10 px-3 py-1.5 text-xs font-semibold text-purple-300 hover:bg-purple-500/20 disabled:opacity-50"
          >
            <Gift className="h-3.5 w-3.5" />
            Seed Global SaaS Program
          </button>
          <button
            type="button"
            onClick={() => setCreateOpen(true)}
            className="inline-flex items-center gap-1.5 rounded-lg bg-amber-500 px-3 py-1.5 text-xs font-semibold text-black hover:bg-amber-400"
          >
            <Plus className="h-3.5 w-3.5" />
            New Program
          </button>
        </div>
      </div>

      {error && (
        <div className="flex items-center gap-3 rounded-xl border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-300">
          <AlertCircle className="h-4 w-4 shrink-0" />
          Failed to load programs. The referrals API endpoint may not yet return a list.
        </div>
      )}

      <div className="overflow-x-auto rounded-xl border border-gray-800">
        <table className="min-w-[860px] w-full text-sm">
          <thead className="bg-gray-950 text-xs uppercase tracking-wider text-gray-500">
            <tr>
              <th className="px-5 py-3 text-left font-semibold">ID</th>
              <th className="px-5 py-3 text-left font-semibold">Type</th>
              <th className="px-5 py-3 text-left font-semibold">Reward</th>
              <th className="px-5 py-3 text-left font-semibold">Status</th>
              <th className="px-5 py-3 text-left font-semibold">Created</th>
              <th className="px-5 py-3 text-right font-semibold">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-800">
            {isLoading && [0, 1, 2].map((i) => (
              <tr key={i}>
                <td colSpan={6} className="px-5 py-4">
                  <div className="h-5 animate-pulse rounded bg-gray-800" />
                </td>
              </tr>
            ))}
            {!isLoading && (!data || data.length === 0) && (
              <tr>
                <td colSpan={6} className="px-5 py-10 text-center text-sm text-gray-500">
                  No programs yet.{' '}
                  <button
                    type="button"
                    onClick={() => createGlobal.mutate()}
                    className="text-amber-400 underline hover:text-amber-300"
                  >
                    Seed the global SaaS program
                  </button>{' '}
                  to get started.
                </td>
              </tr>
            )}
            {data?.map((p) => (
              <>
                <tr
                  key={p.id}
                  className="cursor-pointer hover:bg-gray-800/30"
                  onClick={() => setExpanded(expanded === p.id ? null : p.id)}
                >
                  <td className="px-5 py-3 font-mono text-xs text-gray-400">{p.id.slice(0, 10)}…</td>
                  <td className="px-5 py-3 font-medium capitalize">{p.type.replace(/_/g, ' ')}</td>
                  <td className="px-5 py-3">
                    <span className="font-semibold text-amber-300">
                      {p.reward_amount}{p.reward_type === 'percentage' ? '%' : ' £'}
                    </span>
                    <span className="ml-1 text-xs text-gray-500">{p.reward_type}</span>
                  </td>
                  <td className="px-5 py-3"><StatusBadge status={p.status} /></td>
                  <td className="px-5 py-3 text-xs text-gray-400">{fmt(p.created_at)}</td>
                  <td className="px-5 py-3 text-right">
                    <div className="flex items-center justify-end gap-1" onClick={(e) => e.stopPropagation()}>
                      {p.status === 'pending_approval' && (
                        <>
                          <button
                            onClick={() => setApprovalModal({ program: p, action: 'approve' })}
                            className="rounded p-1.5 text-emerald-400 hover:bg-emerald-500/10"
                            title="Approve"
                          >
                            <CheckCircle2 className="h-4 w-4" />
                          </button>
                          <button
                            onClick={() => setApprovalModal({ program: p, action: 'reject' })}
                            className="rounded p-1.5 text-red-400 hover:bg-red-500/10"
                            title="Reject"
                          >
                            <XCircle className="h-4 w-4" />
                          </button>
                        </>
                      )}
                      {expanded === p.id
                        ? <ChevronUp className="h-4 w-4 text-gray-500" />
                        : <ChevronDown className="h-4 w-4 text-gray-500" />}
                    </div>
                  </td>
                </tr>
                {expanded === p.id && (
                  <tr className="bg-gray-950/60">
                    <td colSpan={6} className="px-5 py-4">
                      <pre className="overflow-x-auto rounded-lg bg-gray-900 p-3 text-xs text-gray-400">
                        {JSON.stringify(p.rules, null, 2)}
                      </pre>
                    </td>
                  </tr>
                )}
              </>
            ))}
          </tbody>
        </table>
      </div>

      {createOpen && <ProgramModal onClose={() => setCreateOpen(false)} />}
      {approvalModal && (
        <ApprovalModal
          program={approvalModal.program}
          action={approvalModal.action}
          onClose={() => setApprovalModal(null)}
        />
      )}
    </div>
  )
}

// ─── Events Tab ───────────────────────────────────────────────────────────────

function EventsTab() {
  const [eventId, setEventId] = useState('')

  const reward = useMutation({
    mutationFn: () => referrals.rewardEvent({ event_id: eventId }),
    onSuccess: () => { toast.success('Event rewarded'); setEventId('') },
    onError: (e: any) => toast.error(e?.response?.data?.detail || 'Failed'),
  })

  const updateStatus = useMutation({
    mutationFn: (status: string) => referrals.updateEventStatus({ event_id: eventId, status }),
    onSuccess: () => toast.success('Event status updated'),
    onError: (e: any) => toast.error(e?.response?.data?.detail || 'Failed'),
  })

  return (
    <div className="space-y-6">
      <p className="text-sm text-gray-400">
        Manually manage referral events — update status, trigger rewards, and review conversions.
      </p>

      <div className="rounded-xl border border-gray-800 bg-gray-900/50 p-5">
        <h3 className="mb-4 text-sm font-semibold text-gray-200">Event Actions</h3>
        <div className="grid gap-4 md:grid-cols-2">
          <div>
            <label className="mb-1.5 block text-xs font-medium text-gray-400">Event ID</label>
            <input
              value={eventId}
              onChange={(e) => setEventId(e.target.value)}
              placeholder="UUID"
              className="w-full rounded-lg border border-gray-700 bg-gray-950 px-3 py-2 font-mono text-sm text-gray-100 focus:outline-none focus:ring-2 focus:ring-amber-500/40"
            />
          </div>
          <div className="flex flex-col justify-end gap-2">
            <div className="flex gap-2">
              {(['converted', 'pending', 'cancelled'] as const).map((s) => (
                <button
                  key={s}
                  type="button"
                  disabled={!eventId || updateStatus.isPending}
                  onClick={() => updateStatus.mutate(s)}
                  className="flex-1 rounded-lg border border-gray-700 px-2 py-1.5 text-xs font-semibold text-gray-300 hover:bg-gray-800 disabled:opacity-40 capitalize"
                >
                  → {s}
                </button>
              ))}
            </div>
            <button
              type="button"
              disabled={!eventId || reward.isPending}
              onClick={() => reward.mutate()}
              className="rounded-lg bg-emerald-600 px-3 py-1.5 text-xs font-semibold text-white hover:bg-emerald-500 disabled:opacity-40"
            >
              {reward.isPending ? 'Processing…' : 'Trigger Reward'}
            </button>
          </div>
        </div>
      </div>

      <div className="rounded-xl border border-amber-500/20 bg-amber-500/5 p-4">
        <div className="flex items-start gap-3">
          <AlertCircle className="mt-0.5 h-4 w-4 shrink-0 text-amber-400" />
          <p className="text-sm text-amber-200/80">
            A full event listing endpoint is on the roadmap. For now, use the actions above to manage
            individual events by ID. You can find Event IDs in the system logs or via the database.
          </p>
        </div>
      </div>
    </div>
  )
}

// ─── Payouts Tab ──────────────────────────────────────────────────────────────

function PayoutsTab() {
  const [payoutId, setPayoutId] = useState('')

  const { data, isLoading, error } = useQuery({
    queryKey: ['admin', 'referrals', 'payout', payoutId],
    queryFn: () => (payoutId ? referrals.getPayout(payoutId).then((r) => r.data) : null),
    enabled: !!payoutId,
  })

  return (
    <div className="space-y-6">
      <p className="text-sm text-gray-400">Look up a specific payout record by ID.</p>

      <div className="rounded-xl border border-gray-800 bg-gray-900/50 p-5">
        <div className="flex gap-3">
          <input
            value={payoutId}
            onChange={(e) => setPayoutId(e.target.value)}
            placeholder="Payout UUID"
            className="flex-1 rounded-lg border border-gray-700 bg-gray-950 px-3 py-2 font-mono text-sm text-gray-100 focus:outline-none focus:ring-2 focus:ring-amber-500/40"
          />
        </div>

        {isLoading && (
          <div className="mt-4 h-16 animate-pulse rounded-lg bg-gray-800" />
        )}

        {data && (
          <div className="mt-4 rounded-lg border border-gray-800 bg-gray-950 p-4">
            <div className="grid grid-cols-2 gap-y-3 text-sm">
              {Object.entries(data as Record<string, unknown>).map(([k, v]) => (
                <div key={k}>
                  <p className="text-xs uppercase tracking-wider text-gray-500">{k}</p>
                  <p className="font-medium text-gray-200">{String(v ?? '—')}</p>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      <div className="rounded-xl border border-amber-500/20 bg-amber-500/5 p-4">
        <div className="flex items-start gap-3">
          <AlertCircle className="mt-0.5 h-4 w-4 shrink-0 text-amber-400" />
          <p className="text-sm text-amber-200/80">
            A bulk payout listing and approval queue is on the roadmap. Payouts can currently be 
            requested by tenants and retrieved by ID above.
          </p>
        </div>
      </div>
    </div>
  )
}

// ─── Overview Tab ─────────────────────────────────────────────────────────────

function OverviewTab() {
  const stats = [
    { label: 'Active Programs', value: '—', icon: Gift, color: 'text-purple-400', bg: 'bg-purple-500/10' },
    { label: 'Total Referrers', value: '—', icon: Users, color: 'text-blue-400', bg: 'bg-blue-500/10' },
    { label: 'Conversions (30d)', value: '—', icon: TrendingUp, color: 'text-emerald-400', bg: 'bg-emerald-500/10' },
    { label: 'Payouts Pending', value: '—', icon: DollarSign, color: 'text-amber-400', bg: 'bg-amber-500/10' },
  ]

  return (
    <div className="space-y-6">
      {/* KPI cards */}
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        {stats.map((s) => {
          const Icon = s.icon
          return (
            <div key={s.label} className="rounded-xl border border-gray-800 bg-gray-900/50 p-5">
              <div className={`mb-3 inline-flex rounded-lg p-2 ${s.bg}`}>
                <Icon className={`h-4 w-4 ${s.color}`} />
              </div>
              <p className="text-2xl font-bold tracking-tight text-white">{s.value}</p>
              <p className="text-xs text-gray-500">{s.label}</p>
            </div>
          )
        })}
      </div>

      {/* Quick reference */}
      <div className="rounded-xl border border-gray-800 bg-gray-900/50 p-5">
        <h3 className="mb-4 flex items-center gap-2 text-sm font-semibold text-gray-200">
          <Link2 className="h-4 w-4 text-amber-400" />
          How Referrals Work on CustomerFlow AI
        </h3>
        <div className="space-y-3">
          {[
            { step: '1', title: 'Program Created', desc: 'Superadmin seeds the global program, or a tradesman creates their own client-referral program.' },
            { step: '2', title: 'Referral Link Generated', desc: 'Each referrer gets a unique link. Clicks are tracked via the /events/log endpoint.' },
            { step: '3', title: 'Conversion Logged', desc: 'When the referred user signs up or pays, an event is created with status "converted".' },
            { step: '4', title: 'Reward Triggered', desc: 'Superadmin approves the event and triggers the reward. Payouts are batched monthly.' },
          ].map((item) => (
            <div key={item.step} className="flex gap-3 text-sm">
              <span className="mt-0.5 inline-flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-amber-500/20 text-[10px] font-bold text-amber-300">
                {item.step}
              </span>
              <div>
                <p className="font-medium text-gray-200">{item.title}</p>
                <p className="text-xs text-gray-500">{item.desc}</p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Analytics placeholder */}
      <div className="flex h-40 items-center justify-center rounded-xl border border-dashed border-gray-700">
        <div className="text-center">
          <BarChart2 className="mx-auto mb-2 h-8 w-8 text-gray-700" />
          <p className="text-sm text-gray-600">Referral analytics chart coming soon</p>
        </div>
      </div>
    </div>
  )
}

// ─── Main page ────────────────────────────────────────────────────────────────

export default function AdminReferralsPage() {
  const [tab, setTab] = useState<Tab>('overview')

  const tabs: { id: Tab; label: string; icon: React.ElementType }[] = [
    { id: 'overview', label: 'Overview', icon: BarChart2 },
    { id: 'programs', label: 'Programs', icon: Gift },
    { id: 'events', label: 'Events', icon: TrendingUp },
    { id: 'payouts', label: 'Payouts', icon: DollarSign },
  ]

  return (
    <div className="space-y-6">
      {/* Header */}
      <header className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Referral &amp; Incentive Centre</h1>
          <p className="mt-1 text-gray-400">
            Manage referral programs, approve tradesman incentive schemes, and process partner payouts.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <span className="rounded-full border border-emerald-500/30 bg-emerald-500/10 px-3 py-1 text-xs font-semibold text-emerald-300">
            Dual-track active
          </span>
        </div>
      </header>

      {/* Tab navigation */}
      <div className="flex gap-1 overflow-x-auto rounded-xl border border-gray-800 bg-gray-900 p-1">
        {tabs.map(({ id, label, icon: Icon }) => (
          <button
            key={id}
            type="button"
            onClick={() => setTab(id)}
            className={`flex items-center gap-2 whitespace-nowrap rounded-lg px-4 py-2 text-sm font-semibold transition-colors ${
              tab === id
                ? 'bg-amber-500/15 text-amber-300'
                : 'text-gray-400 hover:bg-gray-800 hover:text-white'
            }`}
          >
            <Icon className="h-4 w-4" />
            {label}
          </button>
        ))}
      </div>

      {/* Tab content */}
      {tab === 'overview' && <OverviewTab />}
      {tab === 'programs' && <ProgramsTab />}
      {tab === 'events' && <EventsTab />}
      {tab === 'payouts' && <PayoutsTab />}
    </div>
  )
}
