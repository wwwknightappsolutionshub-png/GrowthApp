'use client'

import { useQuery } from '@tanstack/react-query'
import { Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { Loader2 } from 'lucide-react'

import { membershipRewards } from '@/lib/api-client'

const TIER_COLORS: Record<string, string> = {
  bronze: '#cd7f32',
  silver: '#94a3b8',
  gold: '#fbbf24',
  platinum: '#a78bfa',
}

export function MembershipAnalyticsSection() {
  const { data, isLoading } = useQuery({
    queryKey: ['mr-analytics'],
    queryFn: async () => (await membershipRewards.analytics()).data,
  })

  if (isLoading) {
    return (
      <div className="flex justify-center py-16">
        <Loader2 className="w-8 h-8 animate-spin text-brand-teal-400" />
      </div>
    )
  }

  if (!data) return null

  const sourceChart = Object.entries(data.points_by_source ?? {}).map(([name, value]) => ({
    name: name.replace(/_/g, ' '),
    points: value,
  }))

  const tierChart = Object.entries(data.tier_distribution ?? {}).map(([name, value]) => ({
    name: name.charAt(0).toUpperCase() + name.slice(1),
    members: value,
    fill: TIER_COLORS[name] ?? '#20ccce',
  }))

  return (
    <div className="space-y-6">
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Stat label="Loyalty members" value={String(data.members_total)} />
        <Stat label="With point balance" value={String(data.members_with_balance)} />
        <Stat label="Redemption rate" value={`${data.redemption_rate_percent}%`} />
        <Stat label="Expiring in 30 days" value={`${data.expiring_points_soon} pts`} sub="Points at risk" />
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        <Stat label="Points issued (30d)" value={String(data.points_issued_30d)} />
        <Stat label="Points redeemed (30d)" value={String(data.points_redeemed_30d)} />
        <Stat label="Redemptions (30d)" value={String(data.redemptions_30d)} />
        <Stat label="Redemptions (all time)" value={String(data.redemptions_total)} />
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <ChartPanel title="Points earned by source" subtitle="Lifetime positive ledger entries">
          {sourceChart.length ? (
            <div className="h-56">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={sourceChart} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#025422" opacity={0.35} />
                  <XAxis dataKey="name" tick={{ fontSize: 10, fill: '#a7f3d0' }} />
                  <YAxis tick={{ fontSize: 10, fill: '#a7f3d0' }} allowDecimals={false} />
                  <Tooltip
                    contentStyle={{
                      background: '#025422',
                      border: '1px solid #20ccce33',
                      borderRadius: 8,
                      fontSize: 12,
                    }}
                  />
                  <Bar dataKey="points" fill="#20ccce" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <Empty>No points activity yet</Empty>
          )}
        </ChartPanel>

        <ChartPanel title="Members by tier" subtitle="All enrolled loyalty profiles">
          {tierChart.length ? (
            <div className="h-56">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={tierChart} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#025422" opacity={0.35} />
                  <XAxis dataKey="name" tick={{ fontSize: 11, fill: '#a7f3d0' }} />
                  <YAxis tick={{ fontSize: 11, fill: '#a7f3d0' }} allowDecimals={false} />
                  <Tooltip
                    contentStyle={{
                      background: '#025422',
                      border: '1px solid #20ccce33',
                      borderRadius: 8,
                      fontSize: 12,
                    }}
                  />
                  <Legend wrapperStyle={{ fontSize: 11 }} />
                  <Bar dataKey="members" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <Empty>No tier data yet</Empty>
          )}
        </ChartPanel>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <Panel title="Top customers">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-slate-400 border-b border-white/10">
                <th className="py-2 text-left">Member</th>
                <th className="py-2 text-right">Lifetime</th>
                <th className="py-2 text-right">Tier</th>
              </tr>
            </thead>
            <tbody>
              {(data.top_customers ?? []).map((row) => (
                <tr key={row.customer_id} className="border-b border-white/5 text-slate-200">
                  <td className="py-2">{row.customer_name || row.customer_id.slice(0, 8)}</td>
                  <td className="py-2 text-right">{row.points_lifetime}</td>
                  <td className="py-2 text-right capitalize">{row.tier_code}</td>
                </tr>
              ))}
            </tbody>
          </table>
          {!data.top_customers?.length && <Empty>No members yet</Empty>}
        </Panel>

        <Panel title="Recent redemptions">
          <ul className="space-y-2">
            {(data.recent_redemptions ?? []).map((r) => (
              <li
                key={r.id}
                className="flex justify-between gap-2 rounded-lg border border-white/10 px-3 py-2 text-sm"
              >
                <div>
                  <p className="text-white font-medium">{r.reward_name}</p>
                  <p className="text-xs text-slate-400">{r.customer_name}</p>
                </div>
                <span className="text-brand-teal-300 whitespace-nowrap">{r.points_spent} pts</span>
              </li>
            ))}
          </ul>
          {!data.recent_redemptions?.length && <Empty>No redemptions yet</Empty>}
        </Panel>
      </div>
    </div>
  )
}

function Stat({ label, value, sub }: { label: string; value: string; sub?: string }) {
  return (
    <div className="rounded-xl border border-white/10 bg-white/5 p-4">
      <p className="text-xs text-slate-400 uppercase tracking-wide">{label}</p>
      <p className="mt-1 text-2xl font-bold text-white">{value}</p>
      {sub ? <p className="text-xs text-slate-500 mt-0.5">{sub}</p> : null}
    </div>
  )
}

function ChartPanel({
  title,
  subtitle,
  children,
}: {
  title: string
  subtitle?: string
  children: React.ReactNode
}) {
  return (
    <div className="rounded-xl border border-white/10 bg-white/5 p-5">
      <h3 className="text-sm font-bold text-white">{title}</h3>
      {subtitle ? <p className="text-xs text-slate-400 mt-0.5 mb-4">{subtitle}</p> : null}
      {children}
    </div>
  )
}

function Panel({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="rounded-xl border border-white/10 bg-white/5 p-5 space-y-3">
      <h3 className="text-lg font-semibold text-white">{title}</h3>
      {children}
    </div>
  )
}

function Empty({ children }: { children: React.ReactNode }) {
  return <p className="text-sm text-slate-500 py-4">{children}</p>
}
