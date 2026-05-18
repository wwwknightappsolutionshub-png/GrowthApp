'use client'

import { useQuery } from '@tanstack/react-query'
import { FreelancerDashboard } from '@/components/freelancer/FreelancerDashboard'
import {
  reputation,
  leads,
  crm,
  money,
  rbac,
  tasks,
  auth,
} from '@/lib/api-client'
import { formatCurrency } from '@/lib/utils'
import {
  ArrowRight,
  Calendar,
  CheckCircle2,
  ListTodo,
  PoundSterling,
  Sparkles,
  Star,
  Target,
  TrendingUp,
} from 'lucide-react'
import Link from 'next/link'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { motion } from 'framer-motion'

type RbacMe = { role: string; permissions: string[] }
type MeForDashboard = { user_type?: 'tenant' | 'freelancer'; full_name?: string }

export default function DashboardPage() {
  const { data: meRbac, isLoading: rbacLoading } = useQuery<RbacMe>({
    queryKey: ['rbac-me'],
    queryFn: () => rbac.me().then((r) => r.data),
    retry: false,
  })

  const { data: me, isLoading: meLoading } = useQuery<MeForDashboard>({
    queryKey: ['me'],
    queryFn: () => auth.me().then((r) => r.data as MeForDashboard),
    retry: false,
  })

  if (rbacLoading || meLoading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="animate-spin w-6 h-6 border-4 border-primary border-t-transparent rounded-full" />
      </div>
    )
  }

  // Freelancers see the portfolio dashboard (pie charts + tool grid scoped to active client).
  if (me?.user_type === 'freelancer') {
    return <FreelancerDashboard fullName={me?.full_name ?? ''} />
  }

  const role = meRbac?.role || 'staff'

  if (role === 'owner' || role === 'admin') {
    return <OwnerDashboard role={role} />
  }
  if (role === 'manager') {
    return <ManagerDashboard />
  }
  return <StaffDashboard />
}

/* ── Owner / Admin dashboard ─────────────────────────────────────────────── */

function OwnerDashboard({ role }: { role: string }) {
  const { data: repData } = useQuery({
    queryKey: ['reputation-dashboard'],
    queryFn: () => reputation.dashboard().then((r) => r.data),
  })
  const { data: leadsData } = useQuery({
    queryKey: ['leads', { page: 1, page_size: 5 }],
    queryFn: () => leads.list({ page: 1, page_size: 5 }).then((r) => r.data),
  })
  const { data: pipelineData } = useQuery({
    queryKey: ['pipeline'],
    queryFn: () => crm.pipeline().then((r) => r.data),
  })
  const { data: moneyData } = useQuery({
    queryKey: ['money-dashboard-30'],
    queryFn: () => money.dashboard(30).then((r) => r.data),
  })

  const totalDeals = pipelineData?.total_deals ?? 0
  const totalValue = pipelineData?.total_value_pence ?? 0
  const bookedCount = pipelineData?.columns?.Booked?.length ?? 0
  const revenue30d = moneyData?.headline?.revenue_30d_pence ?? 0
  const outstanding = moneyData?.headline?.outstanding_pence ?? 0

  return (
    <div className="space-y-6">
      <header className="flex items-end justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-2xl font-bold">Owner dashboard</h1>
          <p className="text-muted-foreground text-sm mt-1">
            The whole business at a glance. You can drill into anything you see.
          </p>
        </div>
        <Badge variant="secondary" className="capitalize">{role}</Badge>
      </header>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Revenue (30d)"
          value={formatCurrency(revenue30d)}
          subtitle={`${formatCurrency(outstanding)} outstanding`}
          icon={PoundSterling}
          tone="success"
        />
        <StatCard
          title="Pipeline value"
          value={formatCurrency(totalValue)}
          subtitle={`${totalDeals} active deals`}
          icon={TrendingUp}
          tone="info"
        />
        <StatCard
          title="New leads"
          value={leadsData?.total ?? 0}
          subtitle="Total in system"
          icon={Target}
          tone="primary"
        />
        <StatCard
          title="Avg rating"
          value={repData?.avg_rating ?? '—'}
          subtitle={`${repData?.total_reviews ?? 0} reviews`}
          icon={Star}
          tone="warning"
        />
      </div>

      <div className="grid gap-4 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle>Recent leads</CardTitle>
            <Link
              href="/dashboard/leads"
              className="text-sm text-primary hover:underline inline-flex items-center gap-1"
            >
              View all <ArrowRight className="w-3 h-3" />
            </Link>
          </CardHeader>
          <CardContent>
            {!leadsData?.items?.length ? (
              <p className="py-6 text-center text-muted-foreground text-sm">
                No leads yet. Share your landing page to get started.
              </p>
            ) : (
              <ul className="divide-y divide-border -mx-6">
                {leadsData.items.map((lead: { id: string; first_name: string; last_name?: string; service_needed?: string; source: string; status: string; score?: number; score_label?: string }) => (
                  <li
                    key={lead.id}
                    className="px-6 py-3 flex items-center justify-between"
                  >
                    <div>
                      <p className="text-sm font-medium">
                        {lead.first_name} {lead.last_name}
                      </p>
                      <p className="text-xs text-muted-foreground">
                        {lead.service_needed || 'General enquiry'} · {lead.source}
                      </p>
                    </div>
                    <div className="flex items-center gap-2">
                      {lead.score != null && (
                        <Badge variant={lead.score >= 80 ? 'destructive' : lead.score >= 50 ? 'warning' : 'secondary'}>
                          {lead.score}
                        </Badge>
                      )}
                      <Badge variant={lead.status === 'new' ? 'default' : 'outline'}>
                        {lead.status}
                      </Badge>
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>This week</CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="space-y-3 text-sm">
              <li className="flex items-center justify-between">
                <span className="text-muted-foreground flex items-center gap-2">
                  <Calendar className="w-4 h-4" /> Booked jobs
                </span>
                <span className="font-semibold">{bookedCount}</span>
              </li>
              <li className="flex items-center justify-between">
                <span className="text-muted-foreground flex items-center gap-2">
                  <Sparkles className="w-4 h-4" /> Active deals
                </span>
                <span className="font-semibold">{totalDeals}</span>
              </li>
              <li className="flex items-center justify-between">
                <span className="text-muted-foreground flex items-center gap-2">
                  <Star className="w-4 h-4" /> Total reviews
                </span>
                <span className="font-semibold">{repData?.total_reviews ?? 0}</span>
              </li>
            </ul>
            <div className="border-t border-border mt-4 pt-3 space-y-2">
              <ActionLink href="/dashboard/outreach">Build outreach campaign</ActionLink>
              <ActionLink href="/dashboard/landing-pages/new">Generate landing page</ActionLink>
              <ActionLink href="/dashboard/assistant">Ask the AI Assistant</ActionLink>
            </div>
          </CardContent>
        </Card>
      </div>

      <QuickActions
        items={[
          { href: '/dashboard/money', label: 'Money intelligence', desc: 'Revenue, cashflow, upsells', tone: 'success' },
          { href: '/dashboard/crm', label: 'Pipeline', desc: 'Manage your deals', tone: 'info' },
          { href: '/dashboard/settings/usage', label: 'AI usage', desc: 'Track AI spend & quota', tone: 'primary' },
        ]}
      />
    </div>
  )
}

/* ── Manager dashboard ───────────────────────────────────────────────────── */

function ManagerDashboard() {
  const { data: pipelineData } = useQuery({
    queryKey: ['pipeline'],
    queryFn: () => crm.pipeline().then((r) => r.data),
  })
  const { data: leadsData } = useQuery({
    queryKey: ['leads', { page: 1, page_size: 5 }],
    queryFn: () => leads.list({ page: 1, page_size: 5 }).then((r) => r.data),
  })

  return (
    <div className="space-y-6">
      <header className="flex items-end justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-2xl font-bold">Manager dashboard</h1>
          <p className="text-muted-foreground text-sm mt-1">
            Pipeline health, team workload, and today's leads.
          </p>
        </div>
        <Badge variant="secondary">Manager</Badge>
      </header>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <StatCard
          title="Open deals"
          value={pipelineData?.total_deals ?? 0}
          icon={TrendingUp}
          tone="info"
        />
        <StatCard
          title="New leads"
          value={leadsData?.total ?? 0}
          icon={Target}
          tone="primary"
        />
        <StatCard
          title="Booked"
          value={pipelineData?.columns?.Booked?.length ?? 0}
          icon={Calendar}
          tone="success"
        />
      </div>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle>Top of the pipeline</CardTitle>
          <Link
            href="/dashboard/crm"
            className="text-sm text-primary hover:underline inline-flex items-center gap-1"
          >
            Open pipeline <ArrowRight className="w-3 h-3" />
          </Link>
        </CardHeader>
        <CardContent>
          <PipelineMini pipelineData={pipelineData} />
        </CardContent>
      </Card>

      <QuickActions
        items={[
          { href: '/dashboard/tasks', label: 'Team tasks', desc: 'Kanban board' },
          { href: '/dashboard/outreach', label: 'Outreach', desc: 'Campaigns + win-back' },
          { href: '/dashboard/auto-replies', label: 'AI replies', desc: 'Approve drafts' },
        ]}
      />
    </div>
  )
}

/* ── Staff dashboard ─────────────────────────────────────────────────────── */

function StaffDashboard() {
  const { data: me } = useQuery({
    queryKey: ['auth-me'],
    queryFn: () => auth.me().then((r) => r.data),
  })
  const userId = (me as { id?: string } | undefined)?.id

  const { data: myTasks } = useQuery({
    queryKey: ['my-tasks', userId],
    queryFn: () =>
      tasks.list({ assigned_user_id: userId, page_size: 50 }).then((r) => r.data),
    enabled: !!userId,
  })

  type Task = { id: string; title: string; status: string; due_at: string | null; priority?: string }
  const allItems = (myTasks?.items as Task[] | undefined) || []
  const board = allItems.filter((t) => t.status === 'todo' || t.status === 'doing')
  const todo = board.filter((t) => t.status === 'todo')
  const doing = board.filter((t) => t.status === 'doing')

  return (
    <div className="space-y-6">
      <header className="flex items-end justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-2xl font-bold">Today's work</h1>
          <p className="text-muted-foreground text-sm mt-1">
            Tasks assigned to you. Tick them off as you go.
          </p>
        </div>
        <Badge variant="secondary">Staff</Badge>
      </header>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <StatCard title="To do" value={todo.length} icon={ListTodo} tone="primary" />
        <StatCard title="In progress" value={doing.length} icon={Sparkles} tone="info" />
      </div>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle>My tasks</CardTitle>
          <Link
            href="/dashboard/tasks"
            className="text-sm text-primary hover:underline inline-flex items-center gap-1"
          >
            Open Kanban <ArrowRight className="w-3 h-3" />
          </Link>
        </CardHeader>
        <CardContent>
          {board.length === 0 ? (
            <p className="py-6 text-center text-muted-foreground text-sm flex flex-col items-center gap-2">
              <CheckCircle2 className="w-10 h-10 text-success" />
              You're all caught up. Lovely.
            </p>
          ) : (
            <ul className="divide-y divide-border -mx-6">
              {board.map((t) => (
                <li key={t.id} className="px-6 py-3 flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium">{t.title}</p>
                    {t.due_at && (
                      <p className="text-xs text-muted-foreground">
                        Due {new Date(t.due_at).toLocaleString('en-GB', { day: 'numeric', month: 'short' })}
                      </p>
                    )}
                  </div>
                  <Badge variant={t.status === 'doing' ? 'default' : 'outline'}>{t.status}</Badge>
                </li>
              ))}
            </ul>
          )}
        </CardContent>
      </Card>
    </div>
  )
}

/* ── Shared primitives ───────────────────────────────────────────────────── */

const TONE_BG: Record<string, string> = {
  primary: 'bg-primary text-primary-foreground',
  success: 'bg-success text-success-foreground',
  warning: 'bg-warning text-warning-foreground',
  info: 'bg-blue-500 text-white dark:bg-blue-600',
}

function StatCard({
  title,
  value,
  subtitle,
  icon: Icon,
  tone,
}: {
  title: string
  value: string | number
  subtitle?: string
  icon: React.ComponentType<{ className?: string }>
  tone: 'primary' | 'success' | 'warning' | 'info'
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25, ease: 'easeOut' }}
    >
      <Card>
        <CardContent className="p-6">
          <div className="flex items-center justify-between mb-4">
            <p className="text-sm font-medium text-muted-foreground">{title}</p>
            <div className={`p-2 rounded-lg ${TONE_BG[tone]}`}>
              <Icon className="w-5 h-5" />
            </div>
          </div>
          <p className="text-3xl font-bold">{value}</p>
          {subtitle && <p className="text-sm text-muted-foreground mt-1">{subtitle}</p>}
        </CardContent>
      </Card>
    </motion.div>
  )
}

function ActionLink({ href, children }: { href: string; children: React.ReactNode }) {
  return (
    <Link
      href={href}
      className="text-sm text-foreground hover:text-primary flex items-center justify-between group"
    >
      <span>{children}</span>
      <ArrowRight className="w-3.5 h-3.5 opacity-0 group-hover:opacity-100 transition-opacity" />
    </Link>
  )
}

function QuickActions({
  items,
}: {
  items: { href: string; label: string; desc: string; tone?: string }[]
}) {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
      {items.map((a) => (
        <Link key={a.href} href={a.href}>
          <Card className="hover:shadow-md transition-shadow cursor-pointer h-full">
            <CardContent className="p-5">
              <p className="font-semibold text-sm">{a.label}</p>
              <p className="text-xs text-muted-foreground mt-1">{a.desc}</p>
            </CardContent>
          </Card>
        </Link>
      ))}
    </div>
  )
}

function PipelineMini({ pipelineData }: { pipelineData: { columns?: Record<string, unknown[]> } | undefined }) {
  const cols = pipelineData?.columns || {}
  const entries = Object.entries(cols).slice(0, 4)
  if (!entries.length) {
    return (
      <p className="py-6 text-center text-muted-foreground text-sm">
        No deals yet. Convert a lead to start your pipeline.
      </p>
    )
  }
  return (
    <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
      {entries.map(([name, items]) => (
        <div key={name} className="rounded-md bg-muted/50 p-3">
          <p className="text-xs uppercase tracking-wide text-muted-foreground">{name}</p>
          <p className="text-2xl font-bold mt-1">{(items as unknown[]).length}</p>
        </div>
      ))}
    </div>
  )
}
