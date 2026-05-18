'use client'

import { useState } from 'react'
import Link from 'next/link'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  ArrowRight,
  Loader2,
  Megaphone,
  Pause,
  Play,
  Plus,
  RotateCcw,
  Sparkles,
  Trash2,
  Users,
} from 'lucide-react'
import { outreach, type OutreachChannel } from '@/lib/api-client'
import { formatDistanceToNow } from 'date-fns'

type Campaign = {
  id: string
  name: string
  description: string | null
  kind: 'sequence' | 'broadcast' | 'winback'
  channels: string[]
  status: 'draft' | 'scheduled' | 'running' | 'paused' | 'completed'
  enrolled_count: number
  sent_count: number
  replied_count: number
  unsubscribed_count: number
  steps: { channel: string; body: string }[]
  started_at: string | null
  created_at: string
}

const STATUS_TONE: Record<string, string> = {
  draft: 'bg-gray-100 text-foreground/80',
  scheduled: 'bg-blue-50 text-blue-700',
  running: 'bg-green-50 text-green-700',
  paused: 'bg-amber-50 text-amber-700',
  completed: 'bg-gray-100 text-muted-foreground',
}

export default function OutreachListPage() {
  const qc = useQueryClient()
  const { data, isLoading } = useQuery<Campaign[]>({
    queryKey: ['outreach-campaigns'],
    queryFn: () => outreach.list().then((r) => r.data),
  })

  const launch = useMutation({
    mutationFn: (id: string) => outreach.launch(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['outreach-campaigns'] }),
  })
  const pause = useMutation({
    mutationFn: (id: string) => outreach.pause(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['outreach-campaigns'] }),
  })
  const resume = useMutation({
    mutationFn: (id: string) => outreach.resume(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['outreach-campaigns'] }),
  })
  const remove = useMutation({
    mutationFn: (id: string) => outreach.remove(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['outreach-campaigns'] }),
  })

  const [winbackOpen, setWinbackOpen] = useState(false)

  return (
    <div className="space-y-6">
      <header className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold flex items-center gap-2">
            <Megaphone className="w-6 h-6 text-blue-600" /> Outreach Campaigns
          </h1>
          <p className="text-sm text-muted-foreground mt-1">
            Multi-channel sequences across SMS, email and WhatsApp. AI drafts each step.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setWinbackOpen(true)}
            className="inline-flex items-center gap-1.5 rounded-lg border bg-card px-3 py-2 text-sm font-medium text-foreground/80 hover:bg-gray-50"
          >
            <RotateCcw className="w-4 h-4" /> Win-back preset
          </button>
          <Link
            href="/dashboard/outreach/new"
            className="inline-flex items-center gap-1.5 rounded-lg bg-blue-600 px-3 py-2 text-sm font-medium text-white hover:bg-blue-700"
          >
            <Plus className="w-4 h-4" /> New campaign
          </Link>
        </div>
      </header>

      {winbackOpen && <WinbackModal onClose={() => setWinbackOpen(false)} />}

      {isLoading ? (
        <div className="flex items-center justify-center py-20 text-muted-foreground">
          <Loader2 className="w-5 h-5 animate-spin mr-2" /> Loading...
        </div>
      ) : !data?.length ? (
        <EmptyState />
      ) : (
        <ul className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {data.map((c) => {
            const replyRate = c.sent_count ? (c.replied_count / c.sent_count) * 100 : 0
            return (
              <li key={c.id} className="rounded-xl border bg-card p-5 shadow-sm">
                <div className="flex items-start justify-between mb-3">
                  <div>
                    <Link
                      href={`/dashboard/outreach/${c.id}`}
                      className="font-semibold hover:underline"
                    >
                      {c.name}
                    </Link>
                    <p className="text-xs text-muted-foreground mt-0.5 line-clamp-2">
                      {c.description || `${c.steps.length} step${c.steps.length === 1 ? '' : 's'}`}
                    </p>
                  </div>
                  <span
                    className={`rounded-full px-2 py-0.5 text-xs font-medium capitalize ${
                      STATUS_TONE[c.status] || STATUS_TONE.draft
                    }`}
                  >
                    {c.status}
                  </span>
                </div>

                <div className="flex flex-wrap items-center gap-1.5 mb-3">
                  {c.channels.map((ch) => (
                    <span key={ch} className="rounded bg-blue-50 px-1.5 py-0.5 text-xs text-blue-700 capitalize">
                      {ch}
                    </span>
                  ))}
                  {c.kind === 'winback' && (
                    <span className="rounded bg-amber-50 px-1.5 py-0.5 text-xs text-amber-700">
                      Win-back
                    </span>
                  )}
                </div>

                <dl className="grid grid-cols-3 gap-2 text-center mb-4">
                  <KPI label="Enrolled" value={c.enrolled_count} icon={<Users className="w-3.5 h-3.5" />} />
                  <KPI label="Sent" value={c.sent_count} />
                  <KPI label="Reply" value={`${replyRate.toFixed(0)}%`} />
                </dl>

                <div className="flex items-center justify-between text-xs text-muted-foreground">
                  <span>
                    {c.started_at
                      ? `Started ${formatDistanceToNow(new Date(c.started_at))} ago`
                      : `Created ${formatDistanceToNow(new Date(c.created_at))} ago`}
                  </span>
                  <div className="flex gap-1">
                    {(c.status === 'draft' || c.status === 'scheduled') && (
                      <ActionBtn
                        onClick={() => launch.mutate(c.id)}
                        icon={<Play className="w-3.5 h-3.5" />}
                        tone="primary"
                        title="Launch"
                      />
                    )}
                    {c.status === 'running' && (
                      <ActionBtn
                        onClick={() => pause.mutate(c.id)}
                        icon={<Pause className="w-3.5 h-3.5" />}
                        title="Pause"
                      />
                    )}
                    {c.status === 'paused' && (
                      <ActionBtn
                        onClick={() => resume.mutate(c.id)}
                        icon={<Play className="w-3.5 h-3.5" />}
                        tone="primary"
                        title="Resume"
                      />
                    )}
                    {c.status === 'draft' && (
                      <ActionBtn
                        onClick={() => {
                          if (confirm(`Delete "${c.name}"?`)) remove.mutate(c.id)
                        }}
                        icon={<Trash2 className="w-3.5 h-3.5" />}
                        tone="danger"
                        title="Delete"
                      />
                    )}
                  </div>
                </div>
              </li>
            )
          })}
        </ul>
      )}
    </div>
  )
}

function EmptyState() {
  return (
    <div className="rounded-xl border bg-card py-16 flex flex-col items-center gap-3 text-muted-foreground">
      <Megaphone className="w-10 h-10 text-gray-300" />
      <p className="text-sm">No campaigns yet.</p>
      <Link
        href="/dashboard/outreach/new"
        className="inline-flex items-center gap-1.5 text-sm font-medium text-blue-600 hover:text-blue-700"
      >
        Build your first sequence <ArrowRight className="w-4 h-4" />
      </Link>
    </div>
  )
}

function KPI({ label, value, icon }: { label: string; value: number | string; icon?: React.ReactNode }) {
  return (
    <div className="rounded-md bg-gray-50 p-2">
      <div className="text-[10px] uppercase tracking-wide text-muted-foreground flex items-center justify-center gap-1">
        {icon} {label}
      </div>
      <div className="text-sm font-semibold mt-0.5">{value}</div>
    </div>
  )
}

function ActionBtn({
  onClick,
  icon,
  title,
  tone,
}: {
  onClick: () => void
  icon: React.ReactNode
  title: string
  tone?: 'primary' | 'danger'
}) {
  const colour =
    tone === 'primary'
      ? 'bg-blue-600 text-white hover:bg-blue-700'
      : tone === 'danger'
        ? 'text-red-600 hover:bg-red-50 border-red-100'
        : 'text-muted-foreground hover:bg-gray-50'
  return (
    <button
      onClick={onClick}
      title={title}
      className={`inline-flex items-center gap-1 rounded border px-2 py-1 text-xs font-medium transition-colors ${colour}`}
    >
      {icon}
    </button>
  )
}

function WinbackModal({ onClose }: { onClose: () => void }) {
  const qc = useQueryClient()
  const [days, setDays] = useState(90)
  const [channel, setChannel] = useState<OutreachChannel>('email')
  const [offer, setOffer] = useState('We have a special £20 off your next service to welcome you back.')
  const mutation = useMutation({
    mutationFn: () => outreach.winback({ inactive_days: days, channel, offer }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['outreach-campaigns'] })
      onClose()
    },
  })

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-brand-forest-950/55 p-4 backdrop-blur-sm">
      <div className="w-full max-w-lg overflow-hidden rounded-2xl border border-brand-forest-200 bg-card shadow-2xl">
        <header className="flex items-start justify-between gap-4 border-b border-brand-forest-100 bg-gradient-to-br from-brand-forest-50 via-white to-brand-teal-50 p-6">
          <div className="flex gap-3">
            <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-brand-forest-700 text-brand-forest-foreground shadow-brand">
              <Sparkles className="h-5 w-5" />
            </div>
            <div>
              <p className="text-xs font-semibold uppercase tracking-widest text-brand-forest-700/80">
                AI Outreach Preset
              </p>
              <h2 className="mt-1 text-xl font-bold tracking-tight text-brand-forest-950">
                Generate win-back campaign
              </h2>
              <p className="mt-1 text-sm text-brand-forest-800/75">
                Re-engage inactive customers with a branded offer across email, SMS, or WhatsApp.
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="rounded-full p-1 text-brand-forest-700/60 transition hover:bg-white hover:text-brand-forest-950"
            aria-label="Close win-back campaign dialog"
          >
            <span className="text-2xl leading-none">×</span>
          </button>
        </header>

        <div className="space-y-5 p-6 text-sm">
          <div>
            <label className="text-xs font-semibold text-brand-forest-800 uppercase tracking-wide">
              Inactive for at least
            </label>
            <div className="flex items-center gap-2 mt-1">
              <input
                type="number"
                min={14}
                max={730}
                value={days}
                onChange={(e) => setDays(parseInt(e.target.value || '90', 10))}
                className="w-28 rounded-lg border border-border bg-background px-3 py-2 text-sm font-semibold text-foreground shadow-sm focus:border-brand-forest-400 focus:outline-none focus:ring-2 focus:ring-brand-forest-400/20"
              />
              <span className="text-muted-foreground">days</span>
            </div>
          </div>

          <div>
            <label className="text-xs font-semibold text-brand-forest-800 uppercase tracking-wide">
              Channel
            </label>
            <div className="mt-2 grid grid-cols-3 gap-2 text-xs">
              {(['email', 'sms', 'whatsapp'] as OutreachChannel[]).map((c) => (
                <button
                  key={c}
                  onClick={() => setChannel(c)}
                  className={`rounded-lg border px-2 py-2.5 capitalize transition-colors ${
                    channel === c
                      ? 'border-brand-forest-500 bg-brand-forest-50 text-brand-forest-800 font-semibold shadow-sm'
                      : 'border-border bg-background text-muted-foreground hover:border-brand-forest-300 hover:bg-brand-forest-50/50 hover:text-brand-forest-800'
                  }`}
                >
                  {c}
                </button>
              ))}
            </div>
          </div>

          <div>
            <label className="text-xs font-semibold text-brand-forest-800 uppercase tracking-wide">
              Your offer
            </label>
            <textarea
              value={offer}
              onChange={(e) => setOffer(e.target.value)}
              rows={3}
              className="mt-2 w-full resize-none rounded-lg border border-border bg-background px-3 py-2 text-sm text-foreground shadow-sm focus:border-brand-forest-400 focus:outline-none focus:ring-2 focus:ring-brand-forest-400/20"
            />
          </div>
        </div>

        <div className="flex items-center justify-end gap-2 border-t border-border bg-background/60 px-6 py-4">
          <button
            onClick={onClose}
            className="rounded-lg px-4 py-2 text-sm font-semibold text-muted-foreground transition hover:bg-brand-forest-50 hover:text-brand-forest-800"
          >
            Cancel
          </button>
          <button
            onClick={() => mutation.mutate()}
            disabled={mutation.isPending}
            className="inline-flex items-center gap-1.5 rounded-lg bg-brand-forest-700 px-4 py-2 text-sm font-semibold text-brand-forest-foreground shadow-brand transition hover:bg-brand-forest-800 disabled:opacity-50"
          >
            {mutation.isPending ? <Loader2 className="w-4 h-4 animate-spin" /> : <Sparkles className="w-4 h-4" />}
            Create draft
          </button>
        </div>
      </div>
    </div>
  )
}
