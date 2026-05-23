'use client'

import { useMemo } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { useQuery } from '@tanstack/react-query'
import {
  ArrowRight,
  BadgePoundSterling,
  Bot,
  Briefcase,
  Calendar,
  GitBranch,
  Globe,
  Megaphone,
  MessageSquare,
  Palette,
  PhoneCall,
  PieChart as PieIcon,
  Plus,
  Radar,
  Sparkles,
  Star,
  Target,
  TrendingUp,
  Users,
  Zap,
} from 'lucide-react'
import {
  Cell,
  Legend,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
} from 'recharts'
import { freelancerBilling, freelancerClients } from '@/lib/api-client'
import { useActiveClient } from '@/lib/freelancer-context'

interface PortfolioSummary {
  total_clients: number
  active_clients: number
  by_business_type: Record<string, number>
  by_social_platforms: Record<string, number>
  activity_per_client: { client_id: string; client_name: string; score: number }[]
}

interface MyBilling {
  estimated_client_count: number
  effective_price_gbp: number
  tier: string
}

interface ClientListItem {
  id: string
  name: string
  is_active: boolean
  social_handles: Record<string, string>
}

const ACTIVITY_COLORS = ['#0d9488', '#22c55e', '#f59e0b', '#6366f1', '#ec4899', '#0284c7', '#a855f7', '#84cc16']
const TIER_COLORS = ['#16a34a', '#0891b2', '#7c3aed', '#db2777', '#ea580c', '#facc15', '#f87171', '#94a3b8']

export function FreelancerDashboard({ fullName }: { fullName: string }) {
  const router = useRouter()
  const { activeId, setActiveId } = useActiveClient()

  const portfolio = useQuery<PortfolioSummary>({
    queryKey: ['freelancer-portfolio'],
    queryFn: () => freelancerClients.portfolio().then((r) => r.data as PortfolioSummary),
  })

  const clients = useQuery<ClientListItem[]>({
    queryKey: ['freelancer-clients'],
    queryFn: () => freelancerClients.list().then((r) => r.data as ClientListItem[]),
  })

  const myBilling = useQuery<MyBilling>({
    queryKey: ['freelancer-billing-me'],
    queryFn: () => freelancerBilling.me().then((r) => r.data as MyBilling),
    retry: false,
  })

  const firstName = fullName.split(' ')[0] || 'there'

  const activityData = useMemo(() => {
    const list = portfolio.data?.activity_per_client ?? []
    if (list.length === 0) return []
    // Sort by score desc, cap at top 7 then bucket the rest into "Other"
    const sorted = [...list].sort((a, b) => b.score - a.score)
    const top = sorted.slice(0, 7)
    const rest = sorted.slice(7)
    const restSum = rest.reduce((s, r) => s + r.score, 0)
    return [
      ...top.map((r) => ({ name: r.client_name, value: r.score })),
      ...(restSum > 0 ? [{ name: 'Other', value: restSum }] : []),
    ]
  }, [portfolio.data])

  const tierMixData = useMemo(() => {
    const types = portfolio.data?.by_business_type ?? {}
    return Object.entries(types)
      .map(([name, value]) => ({ name: name.charAt(0).toUpperCase() + name.slice(1), value }))
      .sort((a, b) => b.value - a.value)
  }, [portfolio.data])

  const stats = useMemo(() => {
    return {
      total: portfolio.data?.total_clients ?? 0,
      active: portfolio.data?.active_clients ?? 0,
      socialLinked: Object.values(portfolio.data?.by_social_platforms ?? {}).reduce(
        (a, b) => a + b,
        0,
      ),
      monthly: myBilling.data?.effective_price_gbp ?? 0,
    }
  }, [portfolio.data, myBilling.data])

  const activeClient = clients.data?.find((c) => c.id === activeId) ?? null

  return (
    <div className="space-y-6">
      {/* Greeting */}
      <div>
        <h1 className="font-display text-2xl font-bold tracking-tight text-foreground">
          Welcome back, {firstName}.
        </h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Your freelancer portfolio at a glance. Switch into any client to run their tools.
        </p>
      </div>

      {/* KPI cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <KpiCard label="Total clients" value={stats.total} icon={Briefcase} />
        <KpiCard label="Active" value={stats.active} icon={Users} />
        <KpiCard label="Social pages linked" value={stats.socialLinked} icon={Sparkles} />
        <KpiCard
          label="Monthly billing"
          value={`£${stats.monthly.toFixed(0)}`}
          icon={BadgePoundSterling}
          accent
        />
      </div>

      {/* Active client switcher */}
      <div className="rounded-xl border border-border bg-card p-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <div className="text-[10px] uppercase tracking-widest text-muted-foreground">
              Active client context
            </div>
            <div className="mt-0.5 text-base font-semibold text-foreground">
              {activeClient ? activeClient.name : 'No client selected'}
            </div>
            <p className="text-xs text-muted-foreground mt-0.5">
              The tools below will operate inside this client&apos;s workspace. Switch anytime.
            </p>
          </div>
          <div className="flex items-center gap-2">
            <select
              value={activeId ?? ''}
              onChange={(e) => setActiveId(e.target.value || null)}
              className="h-9 rounded-md border border-input bg-background px-3 text-sm"
            >
              <option value="">— No active client —</option>
              {(clients.data ?? [])
                .filter((c) => c.is_active)
                .map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.name}
                  </option>
                ))}
            </select>
            <Link
              href="/dashboard/clients"
              className="inline-flex items-center gap-1 rounded-md border border-input bg-background px-3 py-1.5 text-xs hover:bg-muted"
            >
              All clients <ArrowRight className="h-3 w-3" />
            </Link>
            <button
              onClick={() => router.push('/dashboard/clients')}
              className="inline-flex items-center gap-1 rounded-md bg-brand-forest-700 px-3 py-1.5 text-xs font-semibold text-brand-forest-foreground hover:bg-brand-forest-800"
            >
              <Plus className="h-3 w-3" /> Add client
            </button>
          </div>
        </div>
      </div>

      {/* Pie charts row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <PieCard
          title="Activity per client"
          subtitle="Distribution of activity across your portfolio (more linked socials = more weight)"
          data={activityData}
          colors={ACTIVITY_COLORS}
          emptyHint="Add clients with social pages to see your activity split."
        />
        <PieCard
          title="Client mix by industry"
          subtitle="Portfolio breakdown by business / service type"
          data={tierMixData}
          colors={TIER_COLORS}
          emptyHint="Add clients to see your portfolio mix."
        />
      </div>

      {/* Tools grid — scoped to active client */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <h2 className="font-display text-lg font-semibold tracking-tight text-foreground">
            Tools {activeClient ? `for ${activeClient.name}` : '(select a client first)'}
          </h2>
          {activeClient && (
            <Link
              href={`/dashboard/clients/${activeClient.id}`}
              className="text-xs text-brand-teal-700 hover:underline"
            >
              Open full {activeClient.name.split(' ')[0]} workspace →
            </Link>
          )}
        </div>
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 xl:grid-cols-5 gap-3">
          {TOOL_GRID.map((tool) => {
            const Icon = tool.icon
            return (
              <Link
                key={tool.href}
                href={tool.href}
                className="group rounded-lg border border-border bg-card p-3 hover:border-brand-forest-400 hover:shadow-sm transition-all"
              >
                <div className="rounded-md bg-brand-forest-100 p-2 w-fit text-brand-forest-700 group-hover:bg-brand-forest-200 transition-colors">
                  <Icon className="h-4 w-4" />
                </div>
                <h3 className="mt-2 text-sm font-semibold text-foreground">{tool.label}</h3>
                <p className="text-[11px] text-muted-foreground leading-snug mt-0.5">
                  {tool.description}
                </p>
              </Link>
            )
          })}
        </div>
      </div>
    </div>
  )
}


function KpiCard({
  label,
  value,
  icon: Icon,
  accent,
}: {
  label: string
  value: string | number
  icon: React.ComponentType<{ className?: string }>
  accent?: boolean
}) {
  return (
    <div
      className={`rounded-lg border p-4 ${
        accent
          ? 'border-brand-forest-300 bg-gradient-to-br from-brand-forest-50 to-brand-teal-50'
          : 'border-border bg-card'
      }`}
    >
      <div className="flex items-center justify-between">
        <span className="text-[10px] uppercase tracking-widest text-muted-foreground">
          {label}
        </span>
        <Icon className="h-4 w-4 text-brand-forest-600" />
      </div>
      <div className="mt-1 text-2xl font-bold tabular-nums text-foreground">{value}</div>
    </div>
  )
}


function PieCard({
  title,
  subtitle,
  data,
  colors,
  emptyHint,
}: {
  title: string
  subtitle: string
  data: { name: string; value: number }[]
  colors: string[]
  emptyHint: string
}) {
  return (
    <div className="rounded-xl border border-border bg-card p-4">
      <div className="flex items-center gap-2 mb-1">
        <PieIcon className="h-4 w-4 text-brand-forest-600" />
        <h3 className="font-semibold text-foreground">{title}</h3>
      </div>
      <p className="text-xs text-muted-foreground mb-3">{subtitle}</p>
      {data.length === 0 ? (
        <div className="h-[260px] flex items-center justify-center text-xs text-muted-foreground/70 text-center px-6">
          {emptyHint}
        </div>
      ) : (
        <div className="h-[260px]">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={data}
                dataKey="value"
                nameKey="name"
                cx="50%"
                cy="50%"
                outerRadius="80%"
                innerRadius="45%"
                paddingAngle={2}
                label={({ name, percent }) =>
                  `${name} (${((percent ?? 0) * 100).toFixed(0)}%)`
                }
                labelLine={false}
              >
                {data.map((_, i) => (
                  <Cell key={i} fill={colors[i % colors.length]} />
                ))}
              </Pie>
              <Tooltip />
              <Legend verticalAlign="bottom" height={24} wrapperStyle={{ fontSize: 11 }} />
            </PieChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  )
}


interface ToolDef {
  href: string
  label: string
  description: string
  icon: React.ComponentType<{ className?: string }>
}

const TOOL_GRID: ToolDef[] = [
  { href: '/dashboard/clients', label: 'Clients', description: 'Manage your portfolio', icon: Briefcase },
  { href: '/dashboard/leads', label: 'Leads', description: 'Capture + score enquiries', icon: Target },
  { href: '/dashboard/crm', label: 'CRM', description: 'Customer database', icon: Users },
  { href: '/dashboard/bookings', label: 'Bookings', description: 'Calendar of jobs', icon: Calendar },
  { href: '/dashboard/money', label: 'Money', description: 'Revenue & cash flow', icon: BadgePoundSterling },
  { href: '/dashboard/messages', label: 'Messages', description: 'Unified inbox', icon: MessageSquare },
  { href: '/dashboard/whatsapp', label: 'WhatsApp', description: 'Two-way WhatsApp', icon: PhoneCall },
  { href: '/dashboard/outreach', label: 'Outreach', description: 'Campaigns + drip', icon: Megaphone },
  { href: '/dashboard/ai-social/drafts', label: 'AI Social', description: 'AI-generated posts', icon: Sparkles },
  { href: '/dashboard/ai-social/brand-identity', label: 'Brand Identity', description: 'Colours, tone, logo', icon: Palette },
  { href: '/dashboard/ai-social/calendar', label: 'Social Calendar', description: 'Scheduled posts', icon: Calendar },
  { href: '/dashboard/landing-pages', label: 'Landing Pages', description: 'AI-generated pages', icon: Globe },
  { href: '/dashboard/automations', label: 'Automations', description: 'Trigger workflows', icon: Zap },
  { href: '/dashboard/reviews', label: 'Reviews', description: 'Request + reply', icon: Star },
  { href: '/dashboard/membership-rewards', label: 'Membership & Rewards', description: 'Loyalty points and memberships', icon: TrendingUp },
  { href: '/dashboard/marketer/audience', label: 'Audience Research', description: 'Demographics + insights', icon: Users },
  { href: '/dashboard/marketer/competitor', label: 'Competitor Scanner', description: 'Spy on rival sites', icon: Radar },
  { href: '/dashboard/marketer/funnel', label: 'Funnel Builder', description: '5-stage funnels', icon: GitBranch },
  { href: '/dashboard/pricing', label: 'My Plan', description: 'View / update billing', icon: BadgePoundSterling },
  { href: '/dashboard/assistant', label: 'AI Assistant', description: 'Chat copilot', icon: Bot },
]
