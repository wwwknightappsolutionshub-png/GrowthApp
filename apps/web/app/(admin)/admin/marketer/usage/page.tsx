'use client'

import { useQuery } from '@tanstack/react-query'
import { Activity, RefreshCw } from 'lucide-react'
import { adminApi } from '@/lib/api-client'

interface FunnelLog {
  id: string
  tenant_name: string
  funnel_type: string | null
}
interface AudienceLog {
  id: string
  tenant_name: string
  industry: string | null
}
interface CompetitorLog {
  id: string
  tenant_name: string
  competitor_name: string | null
  website: string | null
}

export default function MarketerUsagePage() {
  const { data, isLoading, refetch, isRefetching } = useQuery({
    queryKey: ['admin', 'marketer', 'usage'],
    queryFn: () => adminApi.marketerUsage().then((r) => r.data),
  })

  const funnels: FunnelLog[] = data?.funnels ?? []
  const audience: AudienceLog[] = data?.audience_research ?? []
  const competitor: CompetitorLog[] = data?.competitor_scans ?? []

  return (
    <div className="text-white">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <Activity className="h-6 w-6 text-amber-400" /> Marketer Usage Logs
          </h1>
          <p className="text-sm text-gray-400 mt-1">
            Recent reports generated across all tenants.
          </p>
        </div>
        <button
          onClick={() => refetch()}
          className="flex items-center gap-2 rounded-lg bg-gray-800 px-3 py-2 text-sm hover:bg-gray-700"
        >
          <RefreshCw className={`h-4 w-4 ${isRefetching ? 'animate-spin' : ''}`} /> Refresh
        </button>
      </div>

      {isLoading ? (
        <div className="text-gray-400">Loading…</div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          <LogCard title={`Funnel blueprints (${funnels.length})`}>
            {funnels.length === 0 ? (
              <Empty />
            ) : (
              funnels.map((f) => (
                <Row key={f.id} tenant={f.tenant_name} primary={f.funnel_type || '—'} />
              ))
            )}
          </LogCard>

          <LogCard title={`Audience research (${audience.length})`}>
            {audience.length === 0 ? (
              <Empty />
            ) : (
              audience.map((a) => (
                <Row key={a.id} tenant={a.tenant_name} primary={a.industry || '—'} />
              ))
            )}
          </LogCard>

          <LogCard title={`Competitor scans (${competitor.length})`}>
            {competitor.length === 0 ? (
              <Empty />
            ) : (
              competitor.map((c) => (
                <Row
                  key={c.id}
                  tenant={c.tenant_name}
                  primary={c.competitor_name || '—'}
                  secondary={c.website || ''}
                />
              ))
            )}
          </LogCard>
        </div>
      )}
    </div>
  )
}

function LogCard({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="rounded-xl border border-gray-800 bg-gray-900 overflow-hidden">
      <div className="px-4 py-3 border-b border-gray-800 text-sm font-semibold">{title}</div>
      <div className="divide-y divide-gray-800 max-h-[600px] overflow-y-auto">{children}</div>
    </div>
  )
}

function Row({
  tenant,
  primary,
  secondary,
}: {
  tenant: string
  primary: string
  secondary?: string
}) {
  return (
    <div className="px-4 py-2 text-sm">
      <div className="font-medium">{tenant}</div>
      <div className="text-xs text-amber-300">{primary}</div>
      {secondary && <div className="text-xs text-gray-500 truncate">{secondary}</div>}
    </div>
  )
}

function Empty() {
  return <div className="px-4 py-6 text-center text-sm text-gray-500">No activity</div>
}
