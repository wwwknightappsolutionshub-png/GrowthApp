'use client'

import { use } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  ArrowLeft,
  Loader2,
  Mail,
  MessageSquare,
  Pause,
  Phone,
  Play,
  Trash2,
  Users,
} from 'lucide-react'
import { outreach } from '@/lib/api-client'

type Campaign = {
  id: string
  name: string
  description: string | null
  kind: string
  channels: string[]
  status: string
  audience: { segment_id?: string; filter?: unknown }
  steps: {
    channel: 'sms' | 'email' | 'whatsapp'
    subject?: string | null
    body: string
    delay_hours: number
    condition: string
    label?: string | null
  }[]
  enrolled_count: number
  sent_count: number
  replied_count: number
}

type Stats = {
  campaign_id: string
  enrolled: number
  active: number
  sent: number
  replied: number
  unsubscribed: number
  completed: number
  reply_rate_pct: number
  unsub_rate_pct: number
}

const CHANNEL_ICON = { sms: Phone, email: Mail, whatsapp: MessageSquare } as const

export default function CampaignDetailPage({
  params,
}: {
  params: Promise<{ id: string }>
}) {
  const { id } = use(params)
  const router = useRouter()
  const qc = useQueryClient()

  const { data: campaign, isLoading } = useQuery<Campaign>({
    queryKey: ['outreach-campaign', id],
    queryFn: () => outreach.get(id).then((r) => r.data),
  })
  const { data: stats } = useQuery<Stats>({
    queryKey: ['outreach-campaign-stats', id],
    queryFn: () => outreach.stats(id).then((r) => r.data),
    refetchInterval: 15_000,
  })

  const invalidate = () => {
    qc.invalidateQueries({ queryKey: ['outreach-campaign', id] })
    qc.invalidateQueries({ queryKey: ['outreach-campaign-stats', id] })
    qc.invalidateQueries({ queryKey: ['outreach-campaigns'] })
  }

  const launch = useMutation({ mutationFn: () => outreach.launch(id), onSuccess: invalidate })
  const pause = useMutation({ mutationFn: () => outreach.pause(id), onSuccess: invalidate })
  const resume = useMutation({ mutationFn: () => outreach.resume(id), onSuccess: invalidate })
  const remove = useMutation({
    mutationFn: () => outreach.remove(id),
    onSuccess: () => router.push('/dashboard/outreach'),
  })

  if (isLoading || !campaign) {
    return <div className="py-20 text-center text-muted-foreground text-sm">Loading campaign...</div>
  }

  const canLaunch = campaign.status === 'draft' || campaign.status === 'scheduled'

  return (
    <div className="space-y-6">
      <Link
        href="/dashboard/outreach"
        className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground"
      >
        <ArrowLeft className="w-4 h-4" /> Back to campaigns
      </Link>

      <header className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-semibold">{campaign.name}</h1>
          {campaign.description && (
            <p className="text-sm text-muted-foreground mt-1">{campaign.description}</p>
          )}
          <div className="flex items-center gap-2 mt-3 text-xs">
            <span className="rounded-full bg-gray-100 px-2 py-0.5 capitalize">
              {campaign.status}
            </span>
            {campaign.channels.map((c) => (
              <span key={c} className="rounded-full bg-blue-50 text-blue-700 px-2 py-0.5 capitalize">
                {c}
              </span>
            ))}
            {campaign.kind === 'winback' && (
              <span className="rounded-full bg-amber-50 text-amber-700 px-2 py-0.5">Win-back</span>
            )}
          </div>
        </div>
        <div className="flex items-center gap-2">
          {canLaunch && (
            <button
              onClick={() => launch.mutate()}
              disabled={launch.isPending}
              className="inline-flex items-center gap-1.5 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
            >
              {launch.isPending ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Play className="w-4 h-4" />
              )}
              Launch
            </button>
          )}
          {campaign.status === 'running' && (
            <button
              onClick={() => pause.mutate()}
              className="inline-flex items-center gap-1.5 rounded-lg border bg-white px-4 py-2 text-sm font-medium text-foreground/80 hover:bg-gray-50"
            >
              <Pause className="w-4 h-4" /> Pause
            </button>
          )}
          {campaign.status === 'paused' && (
            <button
              onClick={() => resume.mutate()}
              className="inline-flex items-center gap-1.5 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
            >
              <Play className="w-4 h-4" /> Resume
            </button>
          )}
          {campaign.status === 'draft' && (
            <button
              onClick={() => {
                if (confirm('Delete this draft?')) remove.mutate()
              }}
              className="inline-flex items-center gap-1.5 rounded-lg border border-red-200 bg-white px-3 py-2 text-sm text-red-600 hover:bg-red-50"
            >
              <Trash2 className="w-4 h-4" />
            </button>
          )}
        </div>
      </header>

      <section className="grid gap-3 sm:grid-cols-5">
        <StatCard label="Enrolled" value={stats?.enrolled ?? campaign.enrolled_count} icon={<Users className="w-4 h-4" />} />
        <StatCard label="Active" value={stats?.active ?? 0} />
        <StatCard label="Sent" value={stats?.sent ?? campaign.sent_count} />
        <StatCard label="Replied" value={stats?.replied ?? campaign.replied_count} />
        <StatCard label="Reply rate" value={`${stats?.reply_rate_pct ?? 0}%`} />
      </section>

      <section>
        <h2 className="text-sm font-semibold uppercase tracking-wide text-muted-foreground mb-3">
          Sequence ({campaign.steps.length} step{campaign.steps.length === 1 ? '' : 's'})
        </h2>
        <ol className="space-y-3">
          {campaign.steps.map((step, idx) => {
            const Icon = CHANNEL_ICON[step.channel] || Mail
            return (
              <li key={idx} className="rounded-xl border bg-white p-5">
                <header className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-3">
                    <div className="w-7 h-7 rounded-full bg-blue-50 text-blue-700 grid place-items-center text-sm font-semibold">
                      {idx + 1}
                    </div>
                    <div className="text-sm font-medium flex items-center gap-1.5">
                      <Icon className="w-4 h-4 text-muted-foreground" />
                      {step.label || `Step ${idx + 1}`}
                    </div>
                  </div>
                  <div className="flex items-center gap-2 text-xs text-muted-foreground">
                    {idx > 0 && <span>+{step.delay_hours}h after previous</span>}
                    {step.condition !== 'always' && (
                      <span className="rounded bg-amber-50 text-amber-700 px-2 py-0.5 capitalize">
                        {step.condition.replace('_', ' ')}
                      </span>
                    )}
                  </div>
                </header>
                {step.subject && (
                  <p className="text-sm font-medium mb-1">{step.subject}</p>
                )}
                <p className="text-sm whitespace-pre-wrap text-foreground/80 leading-relaxed bg-gray-50 rounded p-3">
                  {step.body}
                </p>
              </li>
            )
          })}
        </ol>
      </section>
    </div>
  )
}

function StatCard({
  label,
  value,
  icon,
}: {
  label: string
  value: number | string
  icon?: React.ReactNode
}) {
  return (
    <div className="rounded-xl border bg-white p-4">
      <div className="text-xs text-muted-foreground uppercase tracking-wide flex items-center gap-1">
        {icon} {label}
      </div>
      <div className="text-2xl font-semibold mt-1">{value}</div>
    </div>
  )
}
